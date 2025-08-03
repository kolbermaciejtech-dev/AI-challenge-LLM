#!/usr/bin/env python3
"""
Test script for the Slack Analytics Bot using mock LLM service
This tests the core functionality without making API calls
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database():
    """Test database initialization and queries"""
    print("🔍 Testing Database...")
    try:
        from database import db_manager
        
        # Test schema info
        schema = db_manager.get_schema_info()
        print(f"✅ Database schema loaded")
        
        # Test sample data
        sample_data = db_manager.get_sample_data(5)
        print(f"✅ Sample data: {len(sample_data)} rows")
        
        # Test query execution
        results = db_manager.execute_query("SELECT COUNT(DISTINCT app_name) as total_apps FROM app_metrics")
        print(f"✅ Total unique apps: {results[0]['total_apps']}")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_mock_llm_service():
    """Test mock LLM service functionality"""
    print("\n🤖 Testing Mock LLM Service...")
    try:
        from mock_llm_service import mock_llm_service
        
        # Test relevance detection
        relevant = mock_llm_service.is_relevant_query("how many apps do we have?")
        print(f"✅ Relevance detection: {relevant}")
        
        irrelevant = mock_llm_service.is_relevant_query("what's the weather today?")
        print(f"✅ Off-topic detection: {not irrelevant}")
        
        # Test SQL generation
        sql_query = mock_llm_service.generate_sql_query("how many apps do we have?")
        print(f"✅ SQL generation: {sql_query[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Mock LLM service test failed: {e}")
        return False

def test_end_to_end_mock():
    """Test end-to-end query processing with mock service"""
    print("\n🔄 Testing End-to-End Flow (Mock)...")
    try:
        from database import db_manager
        from mock_llm_service import mock_llm_service
        
        test_queries = [
            "how many apps do we have?",
            "which platform has more installs?",
            "show top 3 countries by revenue",
            "list iOS apps by popularity"
        ]
        
        for query in test_queries:
            print(f"\n📝 Testing: '{query}'")
            
            # Check relevance
            if not mock_llm_service.is_relevant_query(query):
                print(f"❌ Query marked as irrelevant")
                continue
            
            # Generate SQL
            sql_query = mock_llm_service.generate_sql_query(query)
            print(f"🔍 SQL: {sql_query.replace(chr(10), ' ')[:100]}...")
            
            # Execute query
            results = db_manager.execute_query(sql_query)
            print(f"📊 Results: {len(results)} rows")
            
            # Format response
            response = mock_llm_service.format_response(query, results, sql_query)
            print(f"💬 Response type: {response['type']}")
            print(f"📝 Message: {response['message'][:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False

def test_csv_export():
    """Test CSV export functionality"""
    print("\n📄 Testing CSV Export...")
    try:
        import pandas as pd
        from database import db_manager
        
        # Get some sample data
        results = db_manager.execute_query("SELECT * FROM app_metrics LIMIT 10")
        
        # Create DataFrame and export
        df = pd.DataFrame(results)
        test_file = "/tmp/test_export.csv"
        df.to_csv(test_file, index=False)
        
        # Verify file exists and has content
        if os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            print(f"✅ CSV export successful: {file_size} bytes")
            os.remove(test_file)  # Clean up
            return True
        else:
            print("❌ CSV file not created")
            return False
    except Exception as e:
        print(f"❌ CSV export test failed: {e}")
        return False

def test_slack_bot_components():
    """Test Slack bot components without Slack connection"""
    print("\n🤖 Testing Slack Bot Components...")
    try:
        # Test session management
        from slack_bot import SessionManager
        
        user_id = "test_user"
        session = SessionManager.get_session(user_id)
        print(f"✅ Session created for user: {user_id}")
        
        # Test session update
        SessionManager.update_session(user_id, "test query", "SELECT 1", [{"result": 1}])
        updated_session = SessionManager.get_session(user_id)
        print(f"✅ Session updated with query history: {len(updated_session['query_history'])} entries")
        
        # Test table formatting
        from slack_bot import format_table_for_slack
        test_data = [
            {"app": "TikTok", "installs": 1000000},
            {"app": "Instagram", "installs": 800000}
        ]
        table = format_table_for_slack(test_data)
        print(f"✅ Table formatting works: {len(table)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Slack bot components test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Slack Analytics Bot Tests (Mock Mode)\n")
    
    print("✅ Running in mock mode - no API calls required")
    
    # Run tests
    tests = [
        ("Database", test_database),
        ("Mock LLM Service", test_mock_llm_service),
        ("End-to-End (Mock)", test_end_to_end_mock),
        ("CSV Export", test_csv_export),
        ("Slack Bot Components", test_slack_bot_components)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot core functionality is working.")
        print("\n📝 Next steps:")
        print("1. Set up Slack app credentials in .env")
        print("2. Configure OpenAI API key with sufficient quota")
        print("3. Deploy to a public endpoint for Slack events")
        print("4. Test with real Slack integration")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)