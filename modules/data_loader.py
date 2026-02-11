import pandas as pd
import streamlit as st
from config import SHEET_ID, TABS, USE_SAMPLE_DATA
from modules.sample_data import get_sample_data

def preprocess_df(df):
    """Internal helper to clean columns and handle date formats."""
    # Standardize Columns
    df.columns = [c.replace(' ', '_').replace('/', '_') for c in df.columns]

    # Standardize Date Column
    for col in ['Month', 'Date_Month', 'dt', 'Month_Date', 'Date']:
        if col in df.columns:
            df['dt'] = pd.to_datetime(df[col], errors='coerce')
            break

    # Handle Numeric Data for Rankings
    if 'Value_Position' in df.columns:
        df['Value_Position'] = pd.to_numeric(df['Value_Position'], errors='coerce')
    
    return df

def load_from_google_sheets():
    base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    all_data = {}

    for tab in TABS:
        try:
            url = base_url + tab.replace(" ", "%20")
            df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')
            all_data[tab] = preprocess_df(df)
            # Success messages removed for a cleaner sidebar
        except Exception as e:
            # We keep the warning so you know if a specific tab fails
            st.sidebar.warning(f"⚠️ {tab} sync failed.")
            all_data[tab] = None
    
    return all_data

def load_sample_data():
    all_data = {}
    for tab in TABS:
        df = get_sample_data(tab)
        all_data[tab] = preprocess_df(df)
    return all_data

def load_and_preprocess_data():
    """Main entry point for streamlit_app.py"""
    # Use a spinner so the user knows it's working without showing '✅' messages
    with st.spinner("Synchronizing with Google Sheets..."):
        if USE_SAMPLE_DATA:
            return load_sample_data()
        
        data = load_from_google_sheets()
        
        # If any essential sheets failed (None values), fallback to sample data
        if any(v is None for v in data.values()):
            st.sidebar.info("💡 Using cached sample data (Sheet access limited).")
            return load_sample_data()
            
        return data
