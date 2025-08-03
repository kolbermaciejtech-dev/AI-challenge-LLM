import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
import os

class DatabaseManager:
    def __init__(self, db_path: str = "data/app_portfolio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with schema and sample data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                platform TEXT NOT NULL CHECK (platform IN ('iOS', 'Android')),
                date DATE NOT NULL,
                country TEXT NOT NULL,
                installs INTEGER NOT NULL DEFAULT 0,
                in_app_revenue DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                ads_revenue DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                ua_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM app_metrics")
        if cursor.fetchone()[0] == 0:
            self._generate_sample_data(cursor)
        
        conn.commit()
        conn.close()
    
    def _generate_sample_data(self, cursor):
        """Generate realistic sample data for the app portfolio"""
        apps = [
            "TikTok", "Instagram", "WhatsApp", "Snapchat", "Twitter", 
            "Facebook", "YouTube", "Netflix", "Spotify", "Uber",
            "DoorDash", "Airbnb", "Amazon", "Google Maps", "Gmail"
        ]
        
        platforms = ["iOS", "Android"]
        countries = ["US", "UK", "Germany", "France", "Japan", "Brazil", "India", "Canada", "Australia", "Mexico"]
        
        # Generate data for the last 6 months
        start_date = datetime.now() - timedelta(days=180)
        
        sample_data = []
        
        for app in apps:
            for platform in platforms:
                for country in countries:
                    # Generate data for random dates in the last 6 months
                    for _ in range(random.randint(30, 60)):  # 30-60 data points per app/platform/country
                        date = start_date + timedelta(days=random.randint(0, 180))
                        
                        # Generate realistic metrics based on app popularity
                        base_installs = random.randint(1000, 50000)
                        if app in ["TikTok", "Instagram", "WhatsApp"]:
                            base_installs *= random.randint(5, 15)
                        
                        installs = base_installs
                        in_app_revenue = round(installs * random.uniform(0.01, 0.5), 2)
                        ads_revenue = round(installs * random.uniform(0.005, 0.2), 2)
                        ua_cost = round(installs * random.uniform(0.1, 2.0), 2)
                        
                        sample_data.append((
                            app, platform, date.strftime('%Y-%m-%d'), country,
                            installs, in_app_revenue, ads_revenue, ua_cost
                        ))
        
        cursor.executemany('''
            INSERT INTO app_metrics (app_name, platform, date, country, installs, in_app_revenue, ads_revenue, ua_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dictionaries"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            conn.close()
            raise e
    
    def get_schema_info(self) -> str:
        """Get database schema information for the LLM"""
        schema_info = """
        Database Schema:
        
        Table: app_metrics
        Columns:
        - app_name (TEXT): The name of a mobile app (e.g., TikTok, Instagram)
        - platform (TEXT): The operating system (iOS or Android)
        - date (DATE): The specific date for the data being reported (YYYY-MM-DD format)
        - country (TEXT): The geographic country where the app metrics were recorded
        - installs (INTEGER): The number of times the app was downloaded by users
        - in_app_revenue (DECIMAL): Revenue generated from purchases made within the app
        - ads_revenue (DECIMAL): Revenue earned from advertisements displayed within the app
        - ua_cost (DECIMAL): User Acquisition Cost - amount spent on marketing to acquire new users
        
        Sample apps in database: TikTok, Instagram, WhatsApp, Snapchat, Twitter, Facebook, YouTube, Netflix, Spotify, Uber, DoorDash, Airbnb, Amazon, Google Maps, Gmail
        Countries: US, UK, Germany, France, Japan, Brazil, India, Canada, Australia, Mexico
        Date range: Last 6 months from current date
        """
        return schema_info
    
    def get_sample_data(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data for context"""
        query = "SELECT * FROM app_metrics LIMIT ?"
        return self.execute_query(query, (limit,))

# Initialize database
db_manager = DatabaseManager()