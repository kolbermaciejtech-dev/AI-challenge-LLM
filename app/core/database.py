import sqlite3
from typing import List, Dict, Any
from app.core.config import settings


class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT, UPDATE, DELETE queries and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def get_schema(self) -> Dict[str, List[str]]:
        """Get database schema information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [row[1] for row in cursor.fetchall()]
                schema[table] = columns
            
            return schema


# Global database instance
db = DatabaseManager()