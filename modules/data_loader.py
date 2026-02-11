import pandas as pd
import streamlit as st
from config import SHEET_ID, TABS, USE_SAMPLE_DATA
from modules.sample_data import get_sample_data

def load_from_google_sheets():
    # Corrected URL format for Gviz CSV export
    base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    all_data = {}

    for tab in TABS:
        try:
            url = base_url + tab.replace(" ", "%20")
            df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')

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

            all_data[tab] = df
            st.sidebar.success(f"✅ Loaded {tab}")
        except Exception as e:
            st.sidebar.warning(f"⚠️ {tab} load failed: {str(e)}")
            all_data[tab] = None
    
    return all_data

def load_sample_data():
    all_data = {}
    for tab in TABS:
        df = get_sample_data(tab)
        df.columns = [c.replace(' ', '_').replace('/', '_') for c in df.columns]
        for col in ['Month', 'Date_Month', 'dt', 'Month_Date', 'Date']:
            if col in df.columns:
                df['dt'] = pd.to_datetime(df[col], errors='coerce')
                break
        all_data[tab] = df
    return all_data

def load_and_preprocess_data():
    """Matches the call on Line 10 of your streamlit_app.py"""
    if USE_SAMPLE_DATA:
        return load_sample_data()
    
    data = load_from_google_sheets()
    # If sheets failed, use sample data so the app doesn't crash
    if any(v is None for v in data.values()):
        return load_sample_data()
    return data
