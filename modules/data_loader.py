import pandas as pd
import streamlit as st
from config import SHEET_ID, TABS, USE_SAMPLE_DATA
from modules.sample_data import get_sample_data

def load_from_google_sheets():
    """Logic to pull from Google Sheets using the Gviz CSV export"""
    base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
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
            st.sidebar.success(f"Loaded {tab}")
        except Exception as e:
            st.sidebar.warning(f"Could not load {tab}: {str(e)}")
            all_data[tab] = None
    
    return all_data

def load_sample_data():
    """Fallback logic using sample data"""
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
    """
    This is the ONLY function called by streamlit_app.py.
    It decides whether to use Google Sheets or Sample Data.
    """
    if USE_SAMPLE_DATA:
        return load_sample_data()
    else:
        all_data = load_from_google_sheets()
        # Fallback if Google Sheets is unreachable
        if not all_data or any(df is None for df in all_data.values()):
            st.warning("Google Sheets sync issues. Falling back to sample data.")
            return load_sample_data()
        return all_data
