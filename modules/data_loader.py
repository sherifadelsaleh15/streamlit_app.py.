import pandas as pd
import streamlit as st
from config import TABS, USE_SAMPLE_DATA, SHEET_ID
from modules.sample_data import get_sample_data

def load_from_google_sheets():
    """Attempt to load data from Google Sheets"""
    # Clean URL construction
    base_url = "https://docs.google.com/spreadsheets/d/1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY/gviz/tq?tqx=out:csv&sheet="
    all_data = {}

    for tab in TABS:
        try:
            url = base_url + tab.replace(" ", "%20")
            df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')

            # 1. Standardize Columns
            df.columns = [c.replace(' ', '_').replace('/', '_') for c in df.columns]

            # 2. Standardize Date Column
            for col in ['Month', 'Date_Month', 'dt', 'Month_Date', 'Date']:
                if col in df.columns:
                    df['dt'] = pd.to_datetime(df[col], errors='coerce')
                    break

            # 3. Handle Numeric Data
            if 'Value_Position' in df.columns:
                df['Value_Position'] = pd.to_numeric(df['Value_Position'], errors='coerce')

            all_data[tab] = df
        except Exception as e:
            st.error(f"Error loading tab {tab}: {e}")
            all_data[tab] = None
    
    return all_data

def load_sample_data():
    """Load sample data for all tabs"""
    all_data = {}
    for tab in TABS:
        try:
            df = get_sample_data(tab)
            df.columns = [c.replace(' ', '_').replace('/', '_') for c in df.columns]
            for col in ['Month', 'Date_Month', 'dt', 'Month_Date', 'Date']:
                if col in df.columns:
                    df['dt'] = pd.to_datetime(df[col], errors='coerce')
                    break
            all_data[tab] = df
        except:
            all_data[tab] = pd.DataFrame()
    return all_data

def load_and_preprocess_data():
    """Main entry point called by streamlit_app.py"""
    if USE_SAMPLE_DATA:
        return load_sample_data()
    else:
        all_data = load_from_google_sheets()
        # Fallback if Google Sheets fails
        if not all_data or any(df is None for df in all_data.values()):
            st.warning("Sheet load issues detected. Using sample data fallback.")
            return load_sample_data()
        return all_data
