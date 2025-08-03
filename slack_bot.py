import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import tempfile

from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import uvicorn

from database import db_manager
from llm_service import llm_service

# Initialize Slack app
slack_app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

# Initialize FastAPI
api = FastAPI(title="Slack Analytics Bot")
handler = SlackRequestHandler(slack_app)

# Session storage for context (in production, use Redis or database)
user_sessions = {}

class SessionManager:
    @staticmethod
    def get_session(user_id: str) -> Dict[str, Any]:
        if user_id not in user_sessions:
            user_sessions[user_id] = {
                "last_query": None,
                "last_sql": None,
                "last_results": None,
                "query_history": []
            }
        return user_sessions[user_id]
    
    @staticmethod
    def update_session(user_id: str, query: str, sql: str, results: list):
        session = SessionManager.get_session(user_id)
        session["last_query"] = query
        session["last_sql"] = sql
        session["last_results"] = results
        session["query_history"].append({
            "query": query,
            "sql": sql,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 10 queries
        session["query_history"] = session["query_history"][-10:]

def format_table_for_slack(data: list, max_rows: int = 10) -> str:
    """Format data as a table for Slack display"""
    if not data:
        return "No data to display."
    
    # Limit rows for display
    display_data = data[:max_rows]
    
    # Create DataFrame for better formatting
    df = pd.DataFrame(display_data)
    
    # Format the table as code block for better readability
    table_str = "```\n"
    table_str += df.to_string(index=False, max_cols=10)
    if len(data) > max_rows:
        table_str += f"\n... and {len(data) - max_rows} more rows"
    table_str += "\n```"
    
    return table_str

def create_csv_file(data: list, filename: str) -> str:
    """Create a CSV file and return the file path"""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    filepath = f"/tmp/{filename}"
    df.to_csv(filepath, index=False)
    return filepath

@slack_app.message("hello")
def handle_hello(message, say):
    """Handle hello messages"""
    say(f"Hello <@{message['user']}>! I'm your app portfolio analytics assistant. Ask me questions about our mobile apps, their performance, revenue, or user metrics!")

@slack_app.message("help")
def handle_help(message, say):
    """Handle help requests"""
    help_text = """
🤖 *App Portfolio Analytics Bot*

I can help you analyze our mobile app portfolio data. Here's what you can ask:

*Simple Questions:*
• "How many apps do we have?"
• "What's the total revenue for TikTok?"
• "Which platform performs better?"

*Complex Analysis:*
• "Which country generates the most revenue?"
• "List all iOS apps sorted by popularity"
• "Show apps with biggest UA spend change"

*Special Commands:*
• "export this as csv" - Export last results as CSV
• "show me the sql" - See the SQL query used
• "show sql for [previous question]" - Get SQL for specific query

*Example Questions:*
• "Which apps had the highest installs last month?"
• "Compare iOS vs Android revenue"
• "Show top 5 countries by ad revenue"
• "What's the average UA cost per install?"

Just ask naturally - I'll understand! 🚀
    """
    say(help_text)

@slack_app.message("")
def handle_message(message, say):
    """Handle all other messages"""
    user_id = message["user"]
    user_input = message["text"].strip()
    
    # Skip if message is from bot or empty
    if message.get("bot_id") or not user_input:
        return
    
    try:
        # Handle special commands
        if user_input.lower() in ["export this as csv", "export as csv", "download csv"]:
            handle_csv_export(user_id, say)
            return
        
        if user_input.lower().startswith("show me the sql") or user_input.lower().startswith("show sql"):
            handle_sql_request(user_id, user_input, say)
            return
        
        # Check if query is relevant
        if not llm_service.is_relevant_query(user_input):
            say(llm_service.get_rejection_message())
            return
        
        # Show typing indicator
        say("Let me analyze that for you... 🔍")
        
        # Generate SQL query
        sql_query = llm_service.generate_sql_query(user_input)
        
        # Execute query
        results = db_manager.execute_query(sql_query)
        
        # Format response
        response = llm_service.format_response(user_input, results, sql_query)
        
        # Update session
        SessionManager.update_session(user_id, user_input, sql_query, results)
        
        # Send response
        if response["type"] == "simple":
            say(response["message"])
        else:
            # Send explanation and table
            say(response["message"])
            if results:
                table_text = format_table_for_slack(results)
                say(table_text)
        
        # Add helpful hints
        if results:
            hints = "\n💡 *Tip:* You can say 'export this as csv' to download the data or 'show me the sql' to see the query used."
            say(hints)
    
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}\n\nPlease try rephrasing your question or ask for help."
        say(error_msg)

def handle_csv_export(user_id: str, say):
    """Handle CSV export requests"""
    session = SessionManager.get_session(user_id)
    
    if not session["last_results"]:
        say("No recent query results to export. Please run a query first.")
        return
    
    try:
        # Create CSV file
        filename = f"app_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = create_csv_file(session["last_results"], filename)
        
        if filepath:
            # In a real implementation, you'd upload to Slack or provide a download link
            # For now, we'll provide information about the export
            say(f"✅ Data exported successfully!\n\n📊 *Export Details:*\n• Filename: `{filename}`\n• Rows: {len(session['last_results'])}\n• Query: {session['last_query']}\n\n*Note:* In production, this would provide a download link or upload the file directly to Slack.")
        else:
            say("❌ Failed to export data. No results available.")
    
    except Exception as e:
        say(f"❌ Export failed: {str(e)}")

def handle_sql_request(user_id: str, user_input: str, say):
    """Handle SQL query requests"""
    session = SessionManager.get_session(user_id)
    
    # Check if asking for SQL of a specific previous query
    if "for" in user_input.lower():
        # This is a simplified implementation - in production, you'd use NLP to match queries
        say("Here's the SQL for your most recent query:")
    
    if not session["last_sql"]:
        say("No recent SQL query available. Please run a query first.")
        return
    
    sql_text = f"```sql\n{session['last_sql']}\n```"
    say(f"Here's the SQL query I used:\n\n{sql_text}")

# FastAPI routes
@api.post("/slack/events")
async def endpoint(req: Request):
    return await handler.handle(req)

@api.get("/")
async def root():
    return {"message": "Slack Analytics Bot is running!"}

@api.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# CSV download endpoint (for production use)
@api.get("/download/{file_id}")
async def download_csv(file_id: str):
    """Download CSV file endpoint"""
    filepath = f"/tmp/app_analytics_{file_id}.csv"
    if os.path.exists(filepath):
        return FileResponse(
            filepath,
            media_type="text/csv",
            filename=f"app_analytics_{file_id}.csv"
        )
    return {"error": "File not found"}

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 12000))
    uvicorn.run(
        "slack_bot:api",
        host="0.0.0.0",
        port=port,
        reload=True
    )