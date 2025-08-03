from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
import tempfile
import pandas as pd
from datetime import datetime

from app.models.database import db_manager
from app.services.llm_service import llm_service

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
        schema = db_manager.get_schema()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def execute_query(query_request: Dict[str, Any]):
    """Execute a natural language query"""
    try:
        user_question = query_request.get("question", "")
        if not user_question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        response = llm_service.process_question(user_question)
        return response
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