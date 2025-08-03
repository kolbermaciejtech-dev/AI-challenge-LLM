from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.memory import ConversationBufferWindowMemory
import os
import re
from typing import Dict, Any, List, Tuple, Optional
import json
from app.models.database import db_manager
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=settings.openai_api_key
        )
        
        # Create SQL database connection for LangChain
        self.db = SQLDatabase.from_uri(settings.database_url)
        
        # Create SQL query chain
        self.sql_chain = create_sql_query_chain(self.llm, self.db)
        
        # Memory for conversation context
        self.memory = ConversationBufferWindowMemory(k=5, return_messages=True)
        
        # Cache for recent queries to optimize token usage
        self.query_cache = {}
        
    def is_relevant_query(self, user_input: str) -> bool:
        """Check if the query is relevant to app portfolio analytics"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a classifier that determines if a user query is related to mobile app portfolio analytics and business intelligence.
            
            The app portfolio includes metrics like:
            - App installs, revenue, user acquisition costs
            - Platform performance (iOS/Android)
            - Geographic performance by country
            - Time-based analytics
            
            Respond with only 'YES' if the query is related to app analytics, or 'NO' if it's off-topic.
            
            Examples:
            - "How many apps do we have?" -> YES
            - "Which country generates most revenue?" -> YES
            - "What's the weather today?" -> NO
            - "How much does Google earn quarterly?" -> NO (not about our portfolio)
            """),
            ("human", "{input}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"input": user_input})
        return response.content.strip().upper() == "YES"
    
    def generate_sql_query(self, user_input: str) -> str:
        """Generate SQL query from natural language input"""
        # Check cache first
        cache_key = user_input.lower().strip()
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        # Enhanced prompt for better SQL generation
        enhanced_prompt = f"""
        Database Schema:
        {db_manager.get_schema_info()}
        
        User Question: {user_input}
        
        Generate a SQL query to answer this question. Consider:
        1. Use appropriate aggregations (SUM, COUNT, AVG, etc.)
        2. Include relevant GROUP BY and ORDER BY clauses
        3. Use date functions when dealing with time periods
        4. For "popularity", use installs as the metric
        5. Always include meaningful column aliases
        6. Limit results to reasonable numbers (e.g., TOP 10) unless specifically asked for all
        
        Return only the SQL query, no explanations.
        """
        
        try:
            sql_query = self.sql_chain.invoke({"question": enhanced_prompt})
            # Clean up the SQL query
            sql_query = self._clean_sql_query(sql_query)
            
            # Cache the query
            self.query_cache[cache_key] = sql_query
            
            return sql_query
        except Exception as e:
            raise Exception(f"Error generating SQL query: {str(e)}")
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean and validate SQL query"""
        # Remove markdown formatting if present
        sql_query = re.sub(r'```sql\n?', '', sql_query)
        sql_query = re.sub(r'```\n?', '', sql_query)
        sql_query = sql_query.strip()
        
        # Basic SQL injection prevention
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in sql_query.upper():
                raise Exception(f"Potentially dangerous SQL operation detected: {keyword}")
        
        return sql_query
    
    def determine_response_type(self, user_input: str, results: List[Dict]) -> str:
        """Determine if response should be simple text or detailed table"""
        # Simple questions that expect short answers
        simple_patterns = [
            r'how many.*apps?',
            r'total.*apps?',
            r'count.*apps?',
            r'number.*apps?'
        ]
        
        for pattern in simple_patterns:
            if re.search(pattern, user_input.lower()):
                return "simple"
        
        # If results have multiple rows or columns, show as table
        if len(results) > 1 or (len(results) == 1 and len(results[0]) > 2):
            return "table"
        
        return "simple"
    
    def format_response(self, user_input: str, results: List[Dict], sql_query: str) -> Dict[str, Any]:
        """Format the response based on query type and results"""
        if not results:
            return {
                "type": "simple",
                "message": "No data found for your query.",
                "sql_query": sql_query,
                "data": []
            }
        
        response_type = self.determine_response_type(user_input, results)
        
        if response_type == "simple":
            # Generate a simple text response
            message = self._generate_simple_response(user_input, results)
        else:
            # Generate a detailed table response
            message = self._generate_table_response(user_input, results)
        
        return {
            "type": response_type,
            "message": message,
            "sql_query": sql_query,
            "data": results
        }
    
    def _generate_simple_response(self, user_input: str, results: List[Dict]) -> str:
        """Generate a simple text response"""
        if len(results) == 1 and len(results[0]) == 1:
            # Single value response
            value = list(results[0].values())[0]
            if "how many" in user_input.lower() and "apps" in user_input.lower():
                return f"We have {value} apps in our portfolio."
            else:
                return f"The answer is: {value}"
        
        # Multiple values or complex result
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data analyst assistant. Generate a concise, friendly response based on the query results.
            Keep it brief and conversational. Include the key number/value in your response."""),
            ("human", "User asked: {question}\nResults: {results}\nProvide a brief answer:")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "question": user_input,
            "results": str(results)
        })
        
        return response.content
    
    def _generate_table_response(self, user_input: str, results: List[Dict]) -> str:
        """Generate a detailed response with explanation"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data analyst assistant. Analyze the query results and provide:
            1. A brief explanation of what the data shows
            2. Any assumptions made (e.g., time period, how 'popularity' was interpreted)
            3. Key insights from the data
            
            Be concise but informative. The actual table will be displayed separately."""),
            ("human", "User asked: {question}\nResults: {results}\nProvide analysis:")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "question": user_input,
            "results": str(results[:5])  # Limit to first 5 rows for analysis
        })
        
        return response.content
    
    def get_rejection_message(self) -> str:
        """Get a polite rejection message for off-topic queries"""
        messages = [
            "I'm focused on helping with app portfolio analytics. Please ask questions about our mobile apps, their performance, revenue, or user metrics.",
            "I can only assist with questions about our app portfolio data. Try asking about app installs, revenue, or performance metrics.",
            "My expertise is in app analytics and business intelligence. Please ask questions related to our mobile app portfolio.",
        ]
        import random
        return random.choice(messages)
        
    def process_question(self, user_input: str) -> Dict[str, Any]:
        """Process a natural language question and return a response"""
        # Check if query is relevant
        if not self.is_relevant_query(user_input):
            return {
                "type": "rejection",
                "message": self.get_rejection_message(),
                "data": []
            }
        
        try:
            # Generate SQL query
            sql_query = self.generate_sql_query(user_input)
            
            # Execute query
            from app.models.database import db_manager
            results = db_manager.execute_query(sql_query)
            
            # Format response
            response = self.format_response(user_input, results, sql_query)
            
            return response
        except Exception as e:
            print(f"Error in real LLM service: {str(e)}")
            print("Falling back to mock LLM service")
            try:
                from app.services.mock_llm_service import mock_llm_service
                # Use mock service
                if not mock_llm_service.is_relevant_query(user_input):
                    return {
                        "type": "rejection",
                        "message": mock_llm_service.get_rejection_message(),
                        "data": []
                    }
                
                sql_query = mock_llm_service.generate_sql_query(user_input)
                from app.models.database import db_manager
                results = db_manager.execute_query(sql_query)
                response = mock_llm_service.format_response(user_input, results, sql_query)
                return response
            except Exception as mock_error:
                return {
                    "type": "error",
                    "message": f"Error processing question: {str(e)}. Mock service error: {str(mock_error)}",
                    "data": []
                }

# Initialize LLM service
try:
    llm_service = LLMService()
    print("Using real LLM service with OpenAI")
except Exception as e:
    print(f"Error initializing real LLM service: {e}")
    print("Falling back to mock LLM service")
    from app.services.mock_llm_service import mock_llm_service
    llm_service = mock_llm_service