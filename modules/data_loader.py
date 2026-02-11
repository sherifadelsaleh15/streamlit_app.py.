# modules/data_loader.py
import pandas as pd
import streamlit as st
from config import SHEET_ID, TABS
from config import TABS, USE_SAMPLE_DATA, SHEET_ID
from modules.sample_data import get_sample_data

def load_and_preprocess_data():
    """Loads all tabs and standardizes column names for consistency."""
    base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
def load_from_google_sheets():
    """Attempt to load data from Google Sheets"""
    base_url = f"https://docs.google.com/spreadsheets/d/1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY/edit?usp=sharing/gviz/tq?tqx=out:csv&sheet="
all_data = {}

for tab in TABS:
try:
url = base_url + tab.replace(" ", "%20")
df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')

            # 1. Standardize Columns (removes spaces and special characters)
            # This turns 'Month/Date' into 'Month_Date' and 'Value/Position' into 'Value_Position'
            # Standardize Columns
df.columns = [c.replace(' ', '_').replace('/', '_') for c in df.columns]

            # 2. Standardize Date Column
            # Added 'Month_Date' to the list to match our new sheet
            for col in ['Month', 'Date_Month', 'dt', 'Month_Date']:
            # Standardize Date Column
            for col in ['Month', 'Date_Month', 'dt', 'Month_Date', 'Date']:
if col in df.columns:
df['dt'] = pd.to_datetime(df[col], errors='coerce')
break

            # 3. Handle Numeric Data for Rankings
            # If it's the position tracking tab, ensure the value is a number
            # Handle Numeric Data
if 'Value_Position' in df.columns:
df['Value_Position'] = pd.to_numeric(df['Value_Position'], errors='coerce')

all_data[tab] = df
            st.sidebar.success(f"✅ Loaded {tab} from Google Sheets")
except Exception as e:
            st.error(f"Error loading tab {tab}: {e}")
            all_data[tab] = pd.DataFrame()
            
            st.sidebar.warning(f"⚠️ Could not load {tab} from Google Sheets: {str(e)}")
            all_data[tab] = None
    
    return all_data

def load_sample_data():
    """Load sample data for all tabs"""
    all_data = {}
    
    for tab in TABS:
        df = get_sample_data(tab)
        
        # Standardize columns
        df.columns = [c.replace(' ', '_').replace('/', '_') for c in df.columns]
        
        # Standardize Date Column
        for col in ['Month', 'Date_Month', 'dt', 'Month_Date', 'Date']:
            if col in df.columns:
                df['dt'] = pd.to_datetime(df[col], errors='coerce')
                break
        
        all_data[tab] = df
    
return all_data

def load_and_preprocess_data():
    """Loads all tabs - either from Google Sheets or sample data"""
    
    if USE_SAMPLE_DATA:
        st.info("📊 Using sample data for demonstration. To connect to Google Sheets, set USE_SAMPLE_DATA = False in config.py and update SHEET_ID.")
        return load_sample_data()
    else:
        # Try to load from Google Sheets
        all_data = load_from_google_sheets()
        
        # Check if any tabs failed to load
        failed_tabs = [tab for tab, df in all_data.items() if df is None]
        
        if failed_tabs:
            st.warning(f"Failed to load {len(failed_tabs)} tabs from Google Sheets. Falling back to sample data for all tabs.")
            return load_sample_data()
        
        return all_data
