"""
Database utilities for vehicle registration dashboard
Handles SQL operations and data retrieval
"""

import sqlite3
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class DatabaseManager:
    """
    Manages database operations for vehicle registration data
    """
    
    def __init__(self, db_path: str = 'vehicle_data.db'):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            print(f"Error executing query: {e}")
            return pd.DataFrame()
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Get the available date range in the database"""
        query = """
        SELECT MIN(date) as min_date, MAX(date) as max_date
        FROM vehicle_registrations
        """
        result = self.execute_query(query)
        if not result.empty:
            min_date = pd.to_datetime(result.iloc[0]['min_date'])
            max_date = pd.to_datetime(result.iloc[0]['max_date'])
            return min_date, max_date
        return datetime.now() - timedelta(days=365), datetime.now()
    
    def get_vehicle_categories(self) -> List[str]:
        """Get all unique vehicle categories"""
        query = "SELECT DISTINCT vehicle_category FROM vehicle_registrations ORDER BY vehicle_category"
        result = self.execute_query(query)
        return result['vehicle_category'].tolist() if not result.empty else []
    
    def get_manufacturers(self, vehicle_category: Optional[str] = None) -> List[str]:
        """Get manufacturers, optionally filtered by vehicle category"""
        if vehicle_category:
            query = """
            SELECT DISTINCT manufacturer 
            FROM vehicle_registrations 
            WHERE vehicle_category = ?
            ORDER BY manufacturer
            """
            result = self.execute_query(query, (vehicle_category,))
        else:
            query = "SELECT DISTINCT manufacturer FROM vehicle_registrations ORDER BY manufacturer"
            result = self.execute_query(query)
        return result['manufacturer'].tolist() if not result.empty else []
    
    def get_filtered_data(self, 
                         start_date: datetime,
                         end_date: datetime,
                         vehicle_categories: List[str] = None,
                         manufacturers: List[str] = None) -> pd.DataFrame:
        """Get filtered vehicle registration data"""
        
        query = """
        SELECT *
        FROM vehicle_registrations
        WHERE date BETWEEN ? AND ?
        """
        params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
        
        if vehicle_categories:
            placeholders = ','.join(['?' for _ in vehicle_categories])
            query += f" AND vehicle_category IN ({placeholders})"
            params.extend(vehicle_categories)
        
        if manufacturers:
            placeholders = ','.join(['?' for _ in manufacturers])
            query += f" AND manufacturer IN ({placeholders})"
            params.extend(manufacturers)
        
        query += " ORDER BY date, vehicle_category, manufacturer"
        
        return self.execute_query(query, tuple(params))
    
    def get_category_summary(self, 
                           start_date: datetime,
                           end_date: datetime) -> pd.DataFrame:
        """Get summary by vehicle category"""
        query = """
        SELECT 
            vehicle_category,
            SUM(registrations) as total_registrations,
            AVG(yoy_growth) as avg_yoy_growth,
            AVG(qoq_growth) as avg_qoq_growth,
            COUNT(DISTINCT manufacturer) as num_manufacturers
        FROM vehicle_registrations
        WHERE date BETWEEN ? AND ?
        GROUP BY vehicle_category
        ORDER BY total_registrations DESC
        """
        return self.execute_query(query, (start_date.strftime('%Y-%m-%d'), 
                                        end_date.strftime('%Y-%m-%d')))
    
    def get_manufacturer_summary(self, 
                               start_date: datetime,
                               end_date: datetime,
                               vehicle_category: Optional[str] = None) -> pd.DataFrame:
        """Get summary by manufacturer"""
        query = """
        SELECT 
            manufacturer,
            vehicle_category,
            SUM(registrations) as total_registrations,
            AVG(yoy_growth) as avg_yoy_growth,
            AVG(qoq_growth) as avg_qoq_growth
        FROM vehicle_registrations
        WHERE date BETWEEN ? AND ?
        """
        params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
        
        if vehicle_category:
            query += " AND vehicle_category = ?"
            params.append(vehicle_category)
        
        query += """
        GROUP BY manufacturer, vehicle_category
        ORDER BY total_registrations DESC
        """
        
        return self.execute_query(query, tuple(params))
    
    def get_monthly_trends(self, 
                          start_date: datetime,
                          end_date: datetime,
                          vehicle_categories: List[str] = None,
                          manufacturers: List[str] = None) -> pd.DataFrame:
        """Get monthly trend data"""
        
        query = """
        SELECT 
            date,
            year,
            month,
            quarter,
            vehicle_category,
            manufacturer,
            SUM(registrations) as registrations,
            AVG(yoy_growth) as yoy_growth,
            AVG(qoq_growth) as qoq_growth
        FROM vehicle_registrations
        WHERE date BETWEEN ? AND ?
        """
        params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
        
        if vehicle_categories:
            placeholders = ','.join(['?' for _ in vehicle_categories])
            query += f" AND vehicle_category IN ({placeholders})"
            params.extend(vehicle_categories)
        
        if manufacturers:
            placeholders = ','.join(['?' for _ in manufacturers])
            query += f" AND manufacturer IN ({placeholders})"
            params.extend(manufacturers)
        
        query += """
        GROUP BY date, year, month, quarter, vehicle_category, manufacturer
        ORDER BY date, vehicle_category, manufacturer
        """
        
        return self.execute_query(query, tuple(params))
    
    def get_growth_leaders(self, 
                          start_date: datetime,
                          end_date: datetime,
                          growth_type: str = 'yoy') -> pd.DataFrame:
        """Get top growth performers"""
        
        growth_column = 'yoy_growth' if growth_type == 'yoy' else 'qoq_growth'
        
        query = f"""
        SELECT 
            manufacturer,
            vehicle_category,
            AVG({growth_column}) as avg_growth,
            SUM(registrations) as total_registrations
        FROM vehicle_registrations
        WHERE date BETWEEN ? AND ?
        AND {growth_column} IS NOT NULL
        GROUP BY manufacturer, vehicle_category
        HAVING total_registrations > 1000
        ORDER BY avg_growth DESC
        LIMIT 10
        """
        
        return self.execute_query(query, (start_date.strftime('%Y-%m-%d'), 
                                        end_date.strftime('%Y-%m-%d')))
    
    def get_market_share_data(self, 
                             start_date: datetime,
                             end_date: datetime,
                             vehicle_category: str) -> pd.DataFrame:
        """Get market share data for a specific vehicle category"""
        
        query = """
        SELECT 
            manufacturer,
            SUM(registrations) as total_registrations,
            ROUND(SUM(registrations) * 100.0 / 
                  (SELECT SUM(registrations) 
                   FROM vehicle_registrations 
                   WHERE date BETWEEN ? AND ? 
                   AND vehicle_category = ?), 2) as market_share
        FROM vehicle_registrations
        WHERE date BETWEEN ? AND ?
        AND vehicle_category = ?
        GROUP BY manufacturer
        ORDER BY total_registrations DESC
        """
        
        params = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), 
                 vehicle_category, start_date.strftime('%Y-%m-%d'), 
                 end_date.strftime('%Y-%m-%d'), vehicle_category)
        
        return self.execute_query(query, params)
