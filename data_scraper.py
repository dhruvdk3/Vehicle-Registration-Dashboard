"""
Vehicle Registration Data Scraper for Vahan Dashboard
This module handles data collection from public vehicle registration sources.
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Tuple
import time
import random

class VehicleDataScraper:
    """
    A class to scrape and process vehicle registration data from Vahan Dashboard
    and other public sources.
    """
    
    def __init__(self):
        self.base_url = "https://vahan.parivahan.gov.in/vahan4dashboard/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def generate_synthetic_data(self) -> pd.DataFrame:
        """
        Generate synthetic vehicle registration data for demonstration purposes.
        This simulates real Vahan Dashboard data with realistic trends.
        """
        print("Generating synthetic vehicle registration data...")
        
        # Date range: 2020 to 2024
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        # Generate monthly data points
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        
        # Vehicle categories
        categories = ['2W', '3W', '4W']
        
        # Major manufacturers by category
        manufacturers = {
            '2W': ['Hero MotoCorp', 'Honda', 'TVS', 'Bajaj', 'Yamaha', 'Royal Enfield'],
            '3W': ['Bajaj', 'Mahindra', 'TVS', 'Piaggio', 'Atul Auto'],
            '4W': ['Maruti Suzuki', 'Hyundai', 'Tata', 'Mahindra', 'Kia', 'Toyota', 'MG Motor']
        }
        
        data = []
        
        # Base registration numbers (monthly)
        base_registrations = {
            '2W': 1200000,
            '3W': 25000,
            '4W': 280000
        }
        
        for date in dates:
            month = date.month
            year = date.year
            quarter = f"Q{((month-1)//3)+1}"
            
            # Seasonal factors (higher in festival months)
            seasonal_factor = 1.0
            if month in [10, 11]:  # Festive season
                seasonal_factor = 1.3
            elif month in [3, 4]:  # Year-end/new year
                seasonal_factor = 1.1
            elif month in [7, 8]:  # Monsoon (lower sales)
                seasonal_factor = 0.8
                
            # Growth trends
            years_since_2020 = year - 2020
            growth_factor = (1 + 0.08) ** years_since_2020  # 8% YoY growth base
            
            # COVID impact (2020-2021)
            covid_factor = 1.0
            if year == 2020 and month >= 3:
                covid_factor = 0.6  # 40% drop during lockdown
            elif year == 2021 and month <= 6:
                covid_factor = 0.75  # Gradual recovery
                
            for category in categories:
                for manufacturer in manufacturers[category]:
                    # Market share simulation
                    market_shares = {
                        '2W': {'Hero MotoCorp': 0.35, 'Honda': 0.25, 'TVS': 0.15, 
                               'Bajaj': 0.12, 'Yamaha': 0.08, 'Royal Enfield': 0.05},
                        '3W': {'Bajaj': 0.45, 'Mahindra': 0.25, 'TVS': 0.15, 
                               'Piaggio': 0.10, 'Atul Auto': 0.05},
                        '4W': {'Maruti Suzuki': 0.40, 'Hyundai': 0.18, 'Tata': 0.12,
                               'Mahindra': 0.10, 'Kia': 0.08, 'Toyota': 0.07, 'MG Motor': 0.05}
                    }
                    
                    base_reg = base_registrations[category] * market_shares[category][manufacturer]
                    
                    # Add random variation
                    random_factor = random.uniform(0.85, 1.15)
                    
                    registrations = int(base_reg * growth_factor * seasonal_factor * 
                                      covid_factor * random_factor)
                    
                    data.append({
                        'date': date,
                        'year': year,
                        'month': month,
                        'quarter': quarter,
                        'vehicle_category': category,
                        'manufacturer': manufacturer,
                        'registrations': registrations
                    })
        
        df = pd.DataFrame(data)
        print(f"Generated {len(df)} records of synthetic data")
        return df
    
    def calculate_growth_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate YoY and QoQ growth metrics"""
        print("Calculating growth metrics...")
        
        # Sort by date
        df = df.sort_values(['vehicle_category', 'manufacturer', 'date'])
        
        # Calculate YoY growth
        df['prev_year_registrations'] = df.groupby(['vehicle_category', 'manufacturer'])['registrations'].shift(12)
        df['yoy_growth'] = ((df['registrations'] - df['prev_year_registrations']) / df['prev_year_registrations'] * 100).round(2)
        
        # Calculate QoQ growth
        df['prev_quarter_registrations'] = df.groupby(['vehicle_category', 'manufacturer'])['registrations'].shift(3)
        df['qoq_growth'] = ((df['registrations'] - df['prev_quarter_registrations']) / df['prev_quarter_registrations'] * 100).round(2)
        
        return df
    
    def save_to_database(self, df: pd.DataFrame, db_path: str = 'vehicle_data.db'):
        """Save data to SQLite database"""
        print(f"Saving data to {db_path}...")
        
        conn = sqlite3.connect(db_path)
        
        # Create table
        df.to_sql('vehicle_registrations', conn, if_exists='replace', index=False)
        
        # Create indexes for better performance
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_date ON vehicle_registrations(date);
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON vehicle_registrations(vehicle_category);
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_manufacturer ON vehicle_registrations(manufacturer);
        ''')
        
        conn.close()
        print("Data saved to database successfully")
    
    def scrape_and_process_data(self):
        """Main method to scrape and process all data"""
        print("Starting data collection and processing...")
        
        # For demo purposes, we'll use synthetic data
        # In a real scenario, you would implement actual scraping logic here
        df = self.generate_synthetic_data()
        
        # Calculate growth metrics
        df = self.calculate_growth_metrics(df)
        
        # Save to database
        self.save_to_database(df)
        
        # Also save as CSV for backup
        df.to_csv('vehicle_data.csv', index=False)
        
        print("Data collection and processing completed!")
        return df

if __name__ == "__main__":
    scraper = VehicleDataScraper()
    data = scraper.scrape_and_process_data()
    print(f"Total records processed: {len(data)}")
    print("\nSample data:")
    print(data.head(10))
