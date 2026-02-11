# modules/sample_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_gsc_performance():
    """Generate sample GSC Performance data"""
    dates = pd.date_range(start='2026-01-01', end='2026-02-28', freq='D')
    data = []
    
    for date in dates:
        data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Clicks': np.random.randint(1000, 5000),
            'Impressions': np.random.randint(10000, 50000),
            'CTR': np.random.uniform(0.05, 0.15),
            'Position': np.random.uniform(5, 15)
        })
    
    return pd.DataFrame(data)

def generate_gsc_countries():
    """Generate sample GSC Countries data"""
    dates = pd.date_range(start='2026-01-01', end='2026-02-28', freq='W')
    countries = ['Germany', 'France', 'Italy', 'Spain', 'Netherlands', 'Switzerland', 'Austria', 'Belgium']
    data = []
    
    for date in dates:
        for country in countries:
            clicks = np.random.randint(100, 1000)
            impressions = clicks * np.random.randint(10, 30)
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Country': country,
                'Clicks': clicks,
                'Impressions': impressions,
                'CTR': clicks / impressions,
                'Position': np.random.uniform(8, 20)
            })
    
    return pd.DataFrame(data)

def generate_gsc_devices():
    """Generate sample GSC Devices data"""
    dates = pd.date_range(start='2026-01-01', end='2026-02-28', freq='D')
    devices = ['Desktop', 'Mobile', 'Tablet']
    data = []
    
    for date in dates:
        for device in devices:
            clicks = np.random.randint(100, 2000)
            impressions = clicks * np.random.randint(15, 40)
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Device': device,
                'Clicks': clicks,
                'Impressions': impressions,
                'CTR': clicks / impressions,
                'Position': np.random.uniform(5, 25)
            })
    
    return pd.DataFrame(data)

def generate_gsc_queries():
    """Generate sample GSC Queries data"""
    dates = pd.date_range(start='2026-01-01', end='2026-02-28', freq='W')
    queries = [
        'digital strategy 2026',
        'seo best practices',
        'content marketing trends',
        'analytics platform',
        'search engine optimization',
        'google search console',
        'keyword research tool',
        'backlink analysis',
        'technical seo audit',
        'local seo services'
    ]
    data = []
    
    for date in dates:
        for query in queries:
            clicks = np.random.randint(10, 500)
            impressions = clicks * np.random.randint(20, 50)
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Query': query,
                'Clicks': clicks,
                'Impressions': impressions,
                'CTR': clicks / impressions,
                'Position': np.random.uniform(3, 30)
            })
    
    return pd.DataFrame(data)

def generate_rank_tracking():
    """Generate sample Rank Tracking data"""
    dates = pd.date_range(start='2026-01-01', end='2026-02-28', freq='D')
    keywords = [
        'seo tools',
        'marketing analytics',
        'search console',
        'rank tracker',
        'keyword planner'
    ]
    data = []
    
    for date in dates:
        for keyword in keywords:
            # Create realistic ranking trend (improving over time)
            days_since_start = (date - dates[0]).days
            base_position = 30 - (days_since_start * 0.3)
            position = max(1, base_position + np.random.normal(0, 2))
            
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Keyword': keyword,
                'Position': position,
                'Search_Volume': np.random.randint(1000, 10000),
                'Competition': np.random.uniform(0.1, 0.9)
            })
    
    return pd.DataFrame(data)

def get_sample_data(tab_name):
    """Get sample data for a specific tab"""
    generators = {
        "GSC Performance": generate_gsc_performance,
        "GSC Countries": generate_gsc_countries,
        "GSC Devices": generate_gsc_devices,
        "GSC Queries": generate_gsc_queries,
        "Rank Tracking": generate_rank_tracking
    }
    
    if tab_name in generators:
        return generators[tab_name]()
    else:
        # Return empty DataFrame for unknown tabs
        return pd.DataFrame({'Date': [], 'Value': []})
