"""
Vehicle Registration Dashboard - Streamlit Application
An investor-focused dashboard for analyzing vehicle registration trends
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from database_utils import DatabaseManager
from data_scraper import VehicleDataScraper
import os

# Page configuration
st.set_page_config(
    page_title="Vehicle Registration Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 3px solid #1f77b4;
    margin: 0.5rem 0;
}
.growth-positive {
    color: #28a745;
    font-weight: bold;
}
.growth-negative {
    color: #dc3545;
    font-weight: bold;
}
.sidebar .sidebar-content {
    background-color: #f8f9fa;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache data from database"""
    db = DatabaseManager()
    
    # Check if database exists
    if not os.path.exists('vehicle_data.db'):
        with st.spinner('Generating sample data... This may take a moment.'):
            scraper = VehicleDataScraper()
            scraper.scrape_and_process_data()
    
    return db

def format_number(num):
    """Format large numbers for display"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(int(num))

def format_growth(growth):
    """Format growth percentage with colors"""
    if pd.isna(growth):
        return "N/A"
    if growth > 0:
        return f'<span class="growth-positive">+{growth:.1f}%</span>'
    else:
        return f'<span class="growth-negative">{growth:.1f}%</span>'

def main():
    st.title("🚗 Vehicle Registration Dashboard")
    st.markdown("**An Investor-Focused Analysis of Indian Automotive Market**")
    
    # Initialize database
    db = load_data()
    
    # Sidebar filters
    st.sidebar.header("📊 Filters")
    
    # Date range
    try:
        min_date, max_date = db.get_date_range()
        
        # Default to last 2 years
        default_start = max_date - timedelta(days=730)
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=[default_start.date(), max_date.date()],
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())
        else:
            st.sidebar.error("Please select both start and end dates.")
            return
            
    except Exception as e:
        st.error(f"Error loading date range: {e}")
        return
    
    # Vehicle category filter
    categories = db.get_vehicle_categories()
    selected_categories = st.sidebar.multiselect(
        "Vehicle Categories",
        options=categories,
        default=categories
    )
    
    # Manufacturer filter
    if selected_categories:
        manufacturers = []
        for cat in selected_categories:
            manufacturers.extend(db.get_manufacturers(cat))
        manufacturers = list(set(manufacturers))
    else:
        manufacturers = db.get_manufacturers()
    
    selected_manufacturers = st.sidebar.multiselect(
        "Manufacturers",
        options=sorted(manufacturers),
        default=[]
    )
    
    # Main dashboard
    if not selected_categories:
        st.warning("Please select at least one vehicle category.")
        return
    
    # Key Metrics Row
    st.header("📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get summary data
    category_summary = db.get_category_summary(start_date, end_date)
    
    if not category_summary.empty:
        total_registrations = category_summary['total_registrations'].sum()
        avg_yoy_growth = category_summary['avg_yoy_growth'].mean()
        avg_qoq_growth = category_summary['avg_qoq_growth'].mean()
        total_manufacturers = category_summary['num_manufacturers'].sum()
        
        with col1:
            st.metric(
                label="Total Registrations",
                value=format_number(total_registrations),
                delta=f"{avg_yoy_growth:.1f}% YoY" if not pd.isna(avg_yoy_growth) else None
            )
        
        with col2:
            st.metric(
                label="Average YoY Growth",
                value=f"{avg_yoy_growth:.1f}%" if not pd.isna(avg_yoy_growth) else "N/A",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Average QoQ Growth",
                value=f"{avg_qoq_growth:.1f}%" if not pd.isna(avg_qoq_growth) else "N/A",
                delta=None
            )
        
        with col4:
            st.metric(
                label="Active Manufacturers",
                value=str(int(total_manufacturers)),
                delta=None
            )
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Registration Trends by Category")
        
        # Get monthly trends
        trends_data = db.get_monthly_trends(
            start_date, end_date, 
            selected_categories, 
            selected_manufacturers if selected_manufacturers else None
        )
        
        if not trends_data.empty:
            # Aggregate by category and date
            category_trends = trends_data.groupby(['date', 'vehicle_category'])['registrations'].sum().reset_index()
            category_trends['date'] = pd.to_datetime(category_trends['date'])
            
            fig = px.line(
                category_trends, 
                x='date', 
                y='registrations',
                color='vehicle_category',
                title="Monthly Registration Trends",
                labels={'registrations': 'Registrations', 'date': 'Date'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for selected filters.")
    
    with col2:
        st.subheader("🎯 Market Share by Category")
        
        if not category_summary.empty:
            fig = px.pie(
                category_summary, 
                values='total_registrations', 
                names='vehicle_category',
                title="Registration Share by Vehicle Category"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Growth Analysis
    st.header("📈 Growth Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top YoY Growth Performers")
        
        growth_leaders_yoy = db.get_growth_leaders(start_date, end_date, 'yoy')
        
        if not growth_leaders_yoy.empty:
            fig = px.bar(
                growth_leaders_yoy.head(10), 
                x='avg_growth', 
                y='manufacturer',
                color='vehicle_category',
                orientation='h',
                title="Top 10 Manufacturers by YoY Growth",
                labels={'avg_growth': 'Average YoY Growth (%)', 'manufacturer': 'Manufacturer'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No growth data available.")
    
    with col2:
        st.subheader("⚡ Top QoQ Growth Performers")
        
        growth_leaders_qoq = db.get_growth_leaders(start_date, end_date, 'qoq')
        
        if not growth_leaders_qoq.empty:
            fig = px.bar(
                growth_leaders_qoq.head(10), 
                x='avg_growth', 
                y='manufacturer',
                color='vehicle_category',
                orientation='h',
                title="Top 10 Manufacturers by QoQ Growth",
                labels={'avg_growth': 'Average QoQ Growth (%)', 'manufacturer': 'Manufacturer'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No growth data available.")
    
    # Market Share Analysis by Category
    st.header("🎯 Detailed Market Share Analysis")
    
    selected_category_for_share = st.selectbox(
        "Select Vehicle Category for Market Share Analysis",
        options=selected_categories,
        index=0 if selected_categories else None
    )
    
    if selected_category_for_share:
        market_share_data = db.get_market_share_data(start_date, end_date, selected_category_for_share)
        
        if not market_share_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    market_share_data, 
                    values='total_registrations', 
                    names='manufacturer',
                    title=f"Market Share - {selected_category_for_share} Category"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    market_share_data.head(10), 
                    x='manufacturer', 
                    y='market_share',
                    title=f"Market Share % - {selected_category_for_share} Category",
                    labels={'market_share': 'Market Share (%)', 'manufacturer': 'Manufacturer'}
                )
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
    
    # Detailed Data Table
    st.header("📋 Detailed Performance Summary")
    
    manufacturer_summary = db.get_manufacturer_summary(
        start_date, end_date,
        selected_category_for_share if 'selected_category_for_share' in locals() else None
    )
    
    if not manufacturer_summary.empty:
        # Format the data for display
        display_df = manufacturer_summary.copy()
        display_df['total_registrations'] = display_df['total_registrations'].apply(format_number)
        display_df['avg_yoy_growth'] = display_df['avg_yoy_growth'].apply(lambda x: f"{x:.1f}%" if not pd.isna(x) else "N/A")
        display_df['avg_qoq_growth'] = display_df['avg_qoq_growth'].apply(lambda x: f"{x:.1f}%" if not pd.isna(x) else "N/A")
        
        display_df.columns = ['Manufacturer', 'Category', 'Total Registrations', 'Avg YoY Growth', 'Avg QoQ Growth']
        
        st.dataframe(display_df, use_container_width=True, height=400)
    
    # Investment Insights
    st.header("💡 Key Investment Insights")
    
    insights_col1, insights_col2 = st.columns(2)
    
    with insights_col1:
        st.subheader("🔍 Market Observations")
        
        if not category_summary.empty:
            # Find the dominant category
            dominant_category = category_summary.loc[category_summary['total_registrations'].idxmax(), 'vehicle_category']
            dominant_share = category_summary['total_registrations'].max() / category_summary['total_registrations'].sum() * 100
            
            # Find best growth category
            best_growth_category = category_summary.loc[category_summary['avg_yoy_growth'].idxmax(), 'vehicle_category']
            best_growth_rate = category_summary['avg_yoy_growth'].max()
            
            st.markdown(f"""
            - **{dominant_category}** dominates the market with **{dominant_share:.1f}%** share
            - **{best_growth_category}** shows highest growth at **{best_growth_rate:.1f}%** YoY
            - Market has **{int(total_manufacturers)}** active manufacturers
            - Strong seasonal patterns visible in registration data
            """)
    
    with insights_col2:
        st.subheader("📊 Investment Recommendations")
        
        if not growth_leaders_yoy.empty:
            top_performer = growth_leaders_yoy.iloc[0]
            
            st.markdown(f"""
            - **Growth Leader**: {top_performer['manufacturer']} ({top_performer['vehicle_category']})
            - **Growth Rate**: {top_performer['avg_growth']:.1f}% YoY
            - **Electric Vehicle** adoption trends show promise
            - **Two-wheelers** remain the volume driver
            - **Premium segments** showing resilient growth
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **Data Source**: Vehicle Registration Dashboard (Synthetic Data for Demo)  
    **Last Updated**: Generated in real-time  
    **Dashboard Created By**: Backend Developer Intern Candidate
    """)

if __name__ == "__main__":
    main()
