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
            
            # Standardize Columns
            df.columns = [c.replace(' ', '_') for c in df.columns]
            
            # Standardize Date Column
            for col in ['Month', 'Date_Month', 'dt']:
                if col in df.columns:
                    df['dt'] = pd.to_datetime(df[col], errors='coerce')
                    break
            
            all_data[tab] = df
        except Exception as e:
            st.error(f"Error loading tab {tab}: {e}")
            all_data[tab] = pd.DataFrame()
            
    return all_data
