"""
Mock LLM Service for testing without OpenAI API calls
This demonstrates the bot functionality without consuming API credits
"""

import re
from typing import Dict, Any, List
from app.models.database import db_manager

class MockLLMService:
    def __init__(self):
        self.query_cache = {}
    
    def is_relevant_query(self, user_input: str) -> bool:
        """Mock relevance detection based on keywords"""
        app_keywords = [
            'app', 'apps', 'install', 'revenue', 'platform', 'country',
            'ios', 'android', 'tiktok', 'instagram', 'download', 'user',
            'acquisition', 'cost', 'performance', 'analytics', 'metrics'
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in app_keywords)
    
    def generate_sql_query(self, user_input: str) -> str:
        """Generate SQL based on pattern matching"""
        user_lower = user_input.lower()
        
        # Cache check
        if user_lower in self.query_cache:
            return self.query_cache[user_lower]
        
        sql_query = ""
        
        # Pattern matching for common queries
        if "how many apps" in user_lower or "total apps" in user_lower:
            sql_query = "SELECT COUNT(DISTINCT app_name) as total_apps FROM app_metrics"
        
        elif "which country" in user_lower and "revenue" in user_lower:
            sql_query = """
                SELECT country, 
                       SUM(in_app_revenue + ads_revenue) as total_revenue
                FROM app_metrics 
                GROUP BY country 
                ORDER BY total_revenue DESC 
                LIMIT 10
            """
        
        elif "ios apps" in user_lower and "popularity" in user_lower:
            sql_query = """
                SELECT app_name, 
                       SUM(installs) as total_installs
                FROM app_metrics 
                WHERE platform = 'iOS'
                GROUP BY app_name 
                ORDER BY total_installs DESC
            """
        
        elif "platform" in user_lower and "installs" in user_lower:
            sql_query = """
                SELECT platform, 
                       SUM(installs) as total_installs
                FROM app_metrics 
                GROUP BY platform 
                ORDER BY total_installs DESC
            """
        
        elif "top" in user_lower and "countries" in user_lower and "revenue" in user_lower:
            sql_query = """
                SELECT country, 
                       SUM(in_app_revenue + ads_revenue) as total_revenue,
                       SUM(installs) as total_installs
                FROM app_metrics 
                GROUP BY country 
                ORDER BY total_revenue DESC 
                LIMIT 3
            """
        
        elif "ua spend" in user_lower or "acquisition cost" in user_lower:
            sql_query = """
                SELECT app_name,
                       AVG(ua_cost) as avg_ua_cost,
                       SUM(installs) as total_installs
                FROM app_metrics 
                GROUP BY app_name 
                ORDER BY avg_ua_cost DESC
                LIMIT 10
            """
        
        else:
            # Default query for unrecognized patterns
            sql_query = """
                SELECT app_name, platform, 
                       SUM(installs) as total_installs,
                       SUM(in_app_revenue + ads_revenue) as total_revenue
                FROM app_metrics 
                GROUP BY app_name, platform 
                ORDER BY total_revenue DESC 
                LIMIT 10
            """
        
        # Clean up the query
        sql_query = sql_query.strip()
        
        # Cache the query
        self.query_cache[user_lower] = sql_query
        
        return sql_query
    
    def determine_response_type(self, user_input: str, results: List[Dict]) -> str:
        """Determine response type"""
        simple_patterns = [
            r'how many.*apps?',
            r'total.*apps?',
            r'count.*apps?'
        ]
        
        for pattern in simple_patterns:
            if re.search(pattern, user_input.lower()):
                return "simple"
        
        if len(results) > 1 or (len(results) == 1 and len(results[0]) > 2):
            return "table"
        
        return "simple"
    
    def format_response(self, user_input: str, results: List[Dict], sql_query: str) -> Dict[str, Any]:
        """Format response with mock analysis"""
        if not results:
            return {
                "type": "simple",
                "message": "No data found for your query.",
                "sql_query": sql_query,
                "data": []
            }
        
        response_type = self.determine_response_type(user_input, results)
        
        if response_type == "simple":
            message = self._generate_simple_response(user_input, results)
        else:
            message = self._generate_table_response(user_input, results)
        
        return {
            "type": response_type,
            "message": message,
            "sql_query": sql_query,
            "data": results
        }
    
    def _generate_simple_response(self, user_input: str, results: List[Dict]) -> str:
        """Generate simple response"""
        if len(results) == 1 and len(results[0]) == 1:
            value = list(results[0].values())[0]
            if "how many" in user_input.lower() and "apps" in user_input.lower():
                return f"We have {value} apps in our portfolio."
            else:
                return f"The answer is: {value}"
        
        return f"Based on the data analysis, here are the key findings from your query."
    
    def _generate_table_response(self, user_input: str, results: List[Dict]) -> str:
        """Generate table response with mock analysis"""
        analysis_templates = {
            "country": "This analysis shows revenue performance by country. The data includes both in-app purchases and advertising revenue across all apps and platforms.",
            "platform": "This comparison shows performance metrics between iOS and Android platforms across our app portfolio.",
            "apps": "This ranking shows app performance based on the requested metrics. The data reflects aggregated performance across all markets.",
            "revenue": "This revenue analysis includes both in-app purchases and advertising income. All figures are in USD.",
            "installs": "Install numbers represent total downloads across all tracked markets and time periods."
        }
        
        user_lower = user_input.lower()
        analysis = "Here's the analysis of your query results:"
        
        for key, template in analysis_templates.items():
            if key in user_lower:
                analysis = template
                break
        
        # Add assumptions
        assumptions = []
        if "popularity" in user_lower:
            assumptions.append("'Popularity' is measured by total install count")
        if not any(time_word in user_lower for time_word in ["today", "yesterday", "week", "month", "year"]):
            assumptions.append("Data includes all available time periods")
        
        if assumptions:
            analysis += f"\n\nAssumptions made: {', '.join(assumptions)}"
        
        return analysis
    
    def get_rejection_message(self) -> str:
        """Get rejection message for off-topic queries"""
        return "I'm focused on helping with app portfolio analytics. Please ask questions about our mobile apps, their performance, revenue, or user metrics."

# Create mock service instance
mock_llm_service = MockLLMService()