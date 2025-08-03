#!/usr/bin/env python3
"""
Standalone server for demonstrating the bot functionality without Slack
This creates a web interface to test the bot
"""

import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our services
from app.models.database import db_manager
from app.services.mock_llm_service import mock_llm_service

# Initialize FastAPI
app = FastAPI(title="Slack Analytics Bot - Standalone Demo")

# Session storage (in production, use Redis)
sessions = {}

def get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "last_query": None,
            "last_sql": None,
            "last_results": None
        }
    return sessions[session_id]

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the demo web interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Slack Analytics Bot Demo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }
            .chat-container {
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                min-height: 400px;
                max-height: 600px;
                overflow-y: auto;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 8px;
            }
            .user-message {
                background-color: #e3f2fd;
                margin-left: 20%;
                text-align: right;
            }
            .bot-message {
                background-color: #f5f5f5;
                margin-right: 20%;
            }
            .sql-block {
                background-color: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                margin: 10px 0;
                overflow-x: auto;
            }
            .data-table {
                margin: 10px 0;
                overflow-x: auto;
            }
            .data-table table {
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
            }
            .data-table th, .data-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .data-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .input-container {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            .input-field {
                flex: 1;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
            }
            .send-button {
                padding: 12px 24px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .send-button:hover {
                background-color: #45a049;
            }
            .examples {
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .example-query {
                background-color: #f0f8ff;
                padding: 8px 12px;
                margin: 5px;
                border-radius: 5px;
                cursor: pointer;
                display: inline-block;
                border: 1px solid #ddd;
            }
            .example-query:hover {
                background-color: #e6f3ff;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 Slack Analytics Bot Demo</h1>
            <p>Ask questions about our mobile app portfolio in natural language!</p>
        </div>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-apps">-</div>
                <div>Total Apps</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-records">-</div>
                <div>Data Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="countries">-</div>
                <div>Countries</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="platforms">2</div>
                <div>Platforms</div>
            </div>
        </div>

        <div class="examples">
            <h3>💡 Try these example queries:</h3>
            <div class="example-query" onclick="sendQuery('how many apps do we have?')">How many apps do we have?</div>
            <div class="example-query" onclick="sendQuery('which country generates the most revenue?')">Which country generates the most revenue?</div>
            <div class="example-query" onclick="sendQuery('list iOS apps by popularity')">List iOS apps by popularity</div>
            <div class="example-query" onclick="sendQuery('show top 5 countries by installs')">Show top 5 countries by installs</div>
            <div class="example-query" onclick="sendQuery('compare iOS vs Android performance')">Compare iOS vs Android performance</div>
            <div class="example-query" onclick="sendQuery('what is the weather today?')">What is the weather today? (off-topic)</div>
        </div>

        <div class="chat-container" id="chat">
            <div class="bot-message">
                <strong>Analytics Bot:</strong> Hello! I'm your app portfolio analytics assistant. Ask me questions about our mobile apps, their performance, revenue, or user metrics!
            </div>
        </div>

        <div class="loading" id="loading">
            🔍 Analyzing your query...
        </div>

        <div class="input-container">
            <input type="text" id="queryInput" class="input-field" placeholder="Ask a question about our app portfolio..." onkeypress="handleKeyPress(event)">
            <button onclick="sendQuery()" class="send-button">Send</button>
        </div>

        <script>
            // Load stats on page load
            window.onload = function() {
                loadStats();
            };

            function loadStats() {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('total-apps').textContent = data.total_apps;
                        document.getElementById('total-records').textContent = data.total_records.toLocaleString();
                        document.getElementById('countries').textContent = data.countries;
                    })
                    .catch(error => console.error('Error loading stats:', error));
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendQuery();
                }
            }

            function sendQuery(query) {
                const input = document.getElementById('queryInput');
                const chatContainer = document.getElementById('chat');
                const loading = document.getElementById('loading');
                
                const userQuery = query || input.value.trim();
                if (!userQuery) return;

                // Add user message
                const userMessage = document.createElement('div');
                userMessage.className = 'message user-message';
                userMessage.innerHTML = `<strong>You:</strong> ${userQuery}`;
                chatContainer.appendChild(userMessage);

                // Show loading
                loading.style.display = 'block';
                
                // Clear input
                input.value = '';

                // Send query to backend
                fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({query: userQuery})
                })
                .then(response => response.json())
                .then(data => {
                    loading.style.display = 'none';
                    
                    // Add bot response
                    const botMessage = document.createElement('div');
                    botMessage.className = 'message bot-message';
                    
                    let content = `<strong>Analytics Bot:</strong> ${data.message}`;
                    
                    if (data.sql_query) {
                        content += `<div class="sql-block">SQL Query:<br>${data.sql_query}</div>`;
                    }
                    
                    if (data.data && data.data.length > 0) {
                        content += '<div class="data-table">' + formatTable(data.data) + '</div>';
                    }
                    
                    botMessage.innerHTML = content;
                    chatContainer.appendChild(botMessage);
                    
                    // Scroll to bottom
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                })
                .catch(error => {
                    loading.style.display = 'none';
                    console.error('Error:', error);
                    
                    const errorMessage = document.createElement('div');
                    errorMessage.className = 'message bot-message';
                    errorMessage.innerHTML = '<strong>Analytics Bot:</strong> Sorry, I encountered an error processing your query.';
                    chatContainer.appendChild(errorMessage);
                });
            }

            function formatTable(data) {
                if (!data || data.length === 0) return '';
                
                const headers = Object.keys(data[0]);
                let table = '<table><thead><tr>';
                
                headers.forEach(header => {
                    table += `<th>${header}</th>`;
                });
                table += '</tr></thead><tbody>';
                
                data.slice(0, 10).forEach(row => {  // Limit to 10 rows for display
                    table += '<tr>';
                    headers.forEach(header => {
                        let value = row[header];
                        if (typeof value === 'number') {
                            value = value.toLocaleString();
                        }
                        table += `<td>${value}</td>`;
                    });
                    table += '</tr>';
                });
                
                table += '</tbody></table>';
                
                if (data.length > 10) {
                    table += `<p><em>Showing first 10 of ${data.length} rows</em></p>`;
                }
                
                return table;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        total_apps = db_manager.execute_query("SELECT COUNT(DISTINCT app_name) as count FROM app_metrics")[0]['count']
        total_records = db_manager.execute_query("SELECT COUNT(*) as count FROM app_metrics")[0]['count']
        countries = db_manager.execute_query("SELECT COUNT(DISTINCT country) as count FROM app_metrics")[0]['count']
        
        return {
            "total_apps": total_apps,
            "total_records": total_records,
            "countries": countries
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/query")
async def process_query(request: Request):
    """Process a user query"""
    try:
        data = await request.json()
        user_query = data.get("query", "").strip()
        
        if not user_query:
            return {"error": "Empty query"}
        
        # Check if query is relevant
        if not mock_llm_service.is_relevant_query(user_query):
            return {
                "message": mock_llm_service.get_rejection_message(),
                "sql_query": None,
                "data": []
            }
        
        # Generate SQL query
        sql_query = mock_llm_service.generate_sql_query(user_query)
        
        # Execute query
        results = db_manager.execute_query(sql_query)
        
        # Format response
        response = mock_llm_service.format_response(user_query, results, sql_query)
        
        return {
            "message": response["message"],
            "sql_query": sql_query,
            "data": results[:20]  # Limit to 20 rows for web display
        }
    
    except Exception as e:
        return {
            "message": f"Sorry, I encountered an error: {str(e)}",
            "sql_query": None,
            "data": []
        }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "llm_service": "mock"
    }

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 12000))
    host = os.getenv("APP_HOST", "0.0.0.0")
    
    print(f"🚀 Starting Standalone Analytics Bot Demo on {host}:{port}")
    print(f"📊 Database initialized with sample app portfolio data")
    print(f"🤖 Using mock LLM service (no API calls required)")
    print(f"🌐 Open http://localhost:{port} in your browser")
    
    uvicorn.run(
        "standalone_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )