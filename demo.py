#!/usr/bin/env python3
"""
Interactive Demo of the Slack Analytics Bot
This demonstrates the bot functionality without Slack integration
"""

import os
from dotenv import load_dotenv
from database import db_manager
from mock_llm_service import mock_llm_service
import pandas as pd

# Load environment variables
load_dotenv()

def format_table_for_console(data, max_rows=10):
    """Format data as a table for console display"""
    if not data:
        return "No data to display."
    
    # Limit rows for display
    display_data = data[:max_rows]
    
    # Create DataFrame for better formatting
    df = pd.DataFrame(display_data)
    
    table_str = df.to_string(index=False, max_cols=10)
    if len(data) > max_rows:
        table_str += f"\n... and {len(data) - max_rows} more rows"
    
    return table_str

def process_query(user_input):
    """Process a user query and return formatted response"""
    print(f"\n🔍 Processing: '{user_input}'")
    print("-" * 50)
    
    # Check if query is relevant
    if not mock_llm_service.is_relevant_query(user_input):
        return mock_llm_service.get_rejection_message()
    
    try:
        # Generate SQL query
        sql_query = mock_llm_service.generate_sql_query(user_input)
        print(f"📝 Generated SQL:")
        print(f"```sql\n{sql_query}\n```")
        
        # Execute query
        results = db_manager.execute_query(sql_query)
        print(f"\n📊 Query returned {len(results)} rows")
        
        # Format response
        response = mock_llm_service.format_response(user_input, results, sql_query)
        
        print(f"\n💬 Bot Response ({response['type']}):")
        print(response['message'])
        
        # Show table if applicable
        if response['type'] == 'table' and results:
            print(f"\n📋 Data Table:")
            print(format_table_for_console(results))
        
        return response
    
    except Exception as e:
        error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
        print(error_msg)
        return {"error": str(e)}

def demo_queries():
    """Run a series of demo queries"""
    print("🚀 Slack Analytics Bot Demo")
    print("=" * 50)
    print("This demo shows how the bot processes natural language queries")
    print("about our mobile app portfolio and converts them to SQL.\n")
    
    # Sample queries to demonstrate different capabilities
    demo_queries_list = [
        "how many apps do we have?",
        "which country generates the most revenue?",
        "list all iOS apps sorted by popularity",
        "show top 5 countries by ad revenue",
        "which platform has more installs?",
        "what's the average UA cost per app?",
        "what's the weather today?",  # Off-topic query
    ]
    
    for i, query in enumerate(demo_queries_list, 1):
        print(f"\n{'='*60}")
        print(f"DEMO QUERY {i}/{len(demo_queries_list)}")
        print(f"{'='*60}")
        
        response = process_query(query)
        
        if i < len(demo_queries_list):
            input("\nPress Enter to continue to next query...")
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}")
    print("\n🎉 Demo completed! The bot successfully:")
    print("✅ Processed natural language queries")
    print("✅ Generated appropriate SQL statements")
    print("✅ Executed queries against the database")
    print("✅ Formatted responses intelligently")
    print("✅ Detected and rejected off-topic queries")

def interactive_mode():
    """Run interactive mode where user can ask questions"""
    print("\n🤖 Interactive Mode")
    print("=" * 50)
    print("Ask questions about our app portfolio!")
    print("Type 'quit' to exit, 'help' for examples\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print("\n💡 Example questions you can ask:")
                print("• How many apps do we have?")
                print("• Which country generates the most revenue?")
                print("• List iOS apps by popularity")
                print("• Show top countries by installs")
                print("• Compare iOS vs Android performance")
                print("• What's the total revenue for TikTok?")
                continue
            
            if not user_input:
                continue
            
            process_query(user_input)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def show_database_info():
    """Show information about the database"""
    print("📊 Database Information")
    print("=" * 50)
    
    # Show schema
    print("🗄️  Database Schema:")
    print(db_manager.get_schema_info())
    
    # Show sample data
    print("\n📋 Sample Data (first 5 rows):")
    sample_data = db_manager.get_sample_data(5)
    if sample_data:
        df = pd.DataFrame(sample_data)
        print(df.to_string(index=False))
    
    # Show statistics
    stats_queries = [
        ("Total Records", "SELECT COUNT(*) as count FROM app_metrics"),
        ("Unique Apps", "SELECT COUNT(DISTINCT app_name) as count FROM app_metrics"),
        ("Date Range", "SELECT MIN(date) as start_date, MAX(date) as end_date FROM app_metrics"),
        ("Platforms", "SELECT platform, COUNT(*) as records FROM app_metrics GROUP BY platform"),
        ("Countries", "SELECT COUNT(DISTINCT country) as count FROM app_metrics")
    ]
    
    print(f"\n📈 Database Statistics:")
    for stat_name, query in stats_queries:
        try:
            result = db_manager.execute_query(query)
            if stat_name == "Platforms":
                platforms = ", ".join([f"{r['platform']}: {r['records']}" for r in result])
                print(f"• {stat_name}: {platforms}")
            else:
                value = list(result[0].values())[0] if len(result[0]) == 1 else result[0]
                print(f"• {stat_name}: {value}")
        except Exception as e:
            print(f"• {stat_name}: Error - {e}")

def main():
    """Main demo function"""
    print("🎯 Welcome to the Slack Analytics Bot Demo!")
    print("\nChoose an option:")
    print("1. Run automated demo queries")
    print("2. Interactive mode (ask your own questions)")
    print("3. Show database information")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                demo_queries()
                break
            elif choice == '2':
                interactive_mode()
                break
            elif choice == '3':
                show_database_info()
                break
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()