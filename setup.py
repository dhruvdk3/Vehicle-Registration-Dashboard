#!/usr/bin/env python3
"""
Setup script for Vehicle Registration Dashboard
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False
    return True

def generate_data():
    """Generate sample data"""
    print("Generating sample vehicle registration data...")
    try:
        from data_scraper import VehicleDataScraper
        scraper = VehicleDataScraper()
        scraper.scrape_and_process_data()
        print("✅ Sample data generated successfully!")
    except Exception as e:
        print(f"❌ Error generating data: {e}")
        return False
    return True

def main():
    """Main setup function"""
    print("🚗 Vehicle Registration Dashboard Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed during package installation")
        sys.exit(1)
    
    # Generate sample data
    if not generate_data():
        print("⚠️  Data generation failed, but you can run the dashboard anyway")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nTo run the dashboard:")
    print("streamlit run dashboard.py")
    print("\nTo access the dashboard, open your browser to:")
    print("http://localhost:8501")

if __name__ == "__main__":
    main()
