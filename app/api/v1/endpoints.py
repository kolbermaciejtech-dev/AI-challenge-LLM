from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
import tempfile
import pandas as pd
from datetime import datetime

from app.models.database import db_manager
try:
    from app.services.llm_service import llm_service
except Exception as e:
    print(f"Error importing LLM service: {e}")
    from app.services.mock_llm_service import mock_llm_service as llm_service

# Create FastAPI app
api = FastAPI(title="Slack Analytics Bot - REST API", version="1.0.0")

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/schema")
async def get_database_schema():
    """Get database schema information"""
    try:
        schema_info = db_manager.get_schema_info()
        return {"schema": schema_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def execute_query(query_request: Dict[str, Any]):
    """Execute a natural language query"""
    try:
        user_question = query_request.get("question", "")
        if not user_question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        try:
            response = llm_service.process_question(user_question)
            return response
        except Exception as llm_error:
            # If LLM service fails, use a direct SQL query approach
            print(f"LLM service error: {llm_error}")
            print("Using direct SQL query approach")
            
            # Simple pattern matching for common queries
            user_lower = user_question.lower()
            sql_query = ""
            
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
            else:
                sql_query = """
                    SELECT app_name, platform, 
                           SUM(installs) as total_installs,
                           SUM(in_app_revenue + ads_revenue) as total_revenue
                    FROM app_metrics 
                    GROUP BY app_name, platform 
                    ORDER BY total_revenue DESC 
                    LIMIT 10
                """
            
            results = db_manager.execute_query(sql_query)
            
            if "how many apps" in user_lower:
                message = f"We have {results[0]['total_apps']} apps in our portfolio."
                return {
                    "type": "simple",
                    "message": message,
                    "sql_query": sql_query,
                    "data": results
                }
            else:
                return {
                    "type": "table",
                    "message": "Here's the analysis of your query results.",
                    "sql_query": sql_query,
                    "data": results
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/apps")
async def get_apps():
    """Get a list of all apps in the database"""
    try:
        sql_query = "SELECT DISTINCT app_name FROM app_metrics"
        results = db_manager.execute_query(sql_query)
        return {"apps": [result["app_name"] for result in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{session_id}")
async def export_data(session_id: str):
    """Export query results as CSV"""
    try:
        # Get cached results for session
        cached_data = llm_service.get_cached_results(session_id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="No data found for session")
        
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(cached_data)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df.to_csv(tmp_file.name, index=False)
            return FileResponse(
                tmp_file.name,
                media_type='text/csv',
                filename=f"analytics_data_{session_id}.csv"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include router in the app
api.include_router(router, prefix="/api/v1")