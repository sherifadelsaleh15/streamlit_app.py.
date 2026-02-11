# modules/data_loader.py
import pandas as pd
import streamlit as st
from config import TABS, USE_SAMPLE_DATA, SHEET_ID

def load_and_preprocess_data():
    """Loads all tabs from your Google Sheet"""
    base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    all_data = {}

    for tab in TABS:
        try:
            url = base_url + tab.replace(" ", "%20")
            st.sidebar.write(f"Loading {tab}...")  # Debug
            df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')
            
            # Standardize column names
            df.columns = [c.strip().replace(' ', '_').replace('/', '_').replace('-', '_') for c in df.columns]
            
            # Look for date column
            date_cols = ['date', 'Date', 'day', 'Day', 'dt', 'timestamp']
            for col in df.columns:
                if col.lower() in date_cols or 'date' in col.lower():
                    df['dt'] = pd.to_datetime(df[col], errors='coerce')
                    break
            
            # If no date column found, create a dummy one
            if 'dt' not in df.columns:
                df['dt'] = pd.Timestamp.now()
            
            all_data[tab] = df
            st.sidebar.success(f"✅ Loaded {tab}: {len(df)} rows")
            
        except Exception as e:
            st.sidebar.error(f"❌ Error loading {tab}: {str(e)}")
            all_data[tab] = pd.DataFrame()
            
    return all_data
