#!/usr/bin/env python3
"""
Test script for the Slack Analytics Bot
Run this to test core functionality without Slack integration
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
        from app.models.database import db_manager
        
        # Test schema info
        schema = db_manager.get_schema_info()
        print(f"✅ Database schema loaded")
        
        # Test sample data
        sample_data = db_manager.get_sample_data(5)
        print(f"✅ Sample data: {len(sample_data)} rows")
        
        # Test query execution
        results = db_manager.execute_query("SELECT COUNT(*) as total_apps FROM (SELECT DISTINCT app_name FROM app_metrics)")
        print(f"✅ Total unique apps: {results[0]['total_apps']}")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_llm_service():
    """Test LLM service functionality"""
    print("\n🤖 Testing LLM Service...")
    try:
        from llm_service import llm_service
        
        # Test relevance detection
        relevant = llm_service.is_relevant_query("how many apps do we have?")
        print(f"✅ Relevance detection: {relevant}")
        
        irrelevant = llm_service.is_relevant_query("what's the weather today?")
        print(f"✅ Off-topic detection: {not irrelevant}")
        
        # Test SQL generation
        sql_query = llm_service.generate_sql_query("how many apps do we have?")
        print(f"✅ SQL generation: {sql_query[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        return False

def test_end_to_end():
    """Test end-to-end query processing"""
    print("\n🔄 Testing End-to-End Flow...")
    try:
        from app.models.database import db_manager
        from app.services.llm_service import llm_service
        
        test_queries = [
            "how many apps do we have?",
            "which platform has more installs?",
            "show top 3 countries by revenue"
        ]
        
        for query in test_queries:
            print(f"\n📝 Testing: '{query}'")
            
            # Check relevance
            if not llm_service.is_relevant_query(query):
                print(f"❌ Query marked as irrelevant")
                continue
            
            # Generate SQL
            sql_query = llm_service.generate_sql_query(query)
            print(f"🔍 SQL: {sql_query}")
            
            # Execute query
            results = db_manager.execute_query(sql_query)
            print(f"📊 Results: {len(results)} rows")
            
            # Format response
            response = llm_service.format_response(query, results, sql_query)
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
        from app.models.database import db_manager
        
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

def main():
    """Run all tests"""
    print("🚀 Starting Slack Analytics Bot Tests\n")
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return False
    
    print("✅ Environment variables loaded")
    
    # Run tests
    tests = [
        ("Database", test_database),
        ("LLM Service", test_llm_service),
        ("End-to-End", test_end_to_end),
        ("CSV Export", test_csv_export)
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
        print(f"{test_name:15} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)