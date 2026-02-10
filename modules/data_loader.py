import pandas as pd
import streamlit as st
from config import SHEET_ID, TABS

def load_and_preprocess_data():
    """Loads all tabs and standardizes column names for consistency."""
    base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    all_data = {}

    for tab in TABS:
        try:
            url = base_url + tab.replace(" ", "%20")
            df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')
            
            # 1. Standardize Columns (removes spaces and special characters)
            # This turns 'Month/Date' into 'Month_Date' and 'Value/Position' into 'Value_Position'
            df.columns = [c.replace(' ', '_').replace('/', '_') for c in df.columns]
            
            # 2. Standardize Date Column
            # Added 'Month_Date' to the list to match our new sheet
            for col in ['Month', 'Date_Month', 'dt', 'Month_Date']:
                if col in df.columns:
                    df['dt'] = pd.to_datetime(df[col], errors='coerce')
                    break
            
            # 3. Handle Numeric Data for Rankings
            # If it's the position tracking tab, ensure the value is a number
            if 'Value_Position' in df.columns:
                df['Value_Position'] = pd.to_numeric(df['Value_Position'], errors='coerce')
            
            all_data[tab] = df
        except Exception as e:
            st.error(f"Error loading tab {tab}: {e}")
            all_data[tab] = pd.DataFrame()
            
    return all_data
