import pandas as pd
import numpy as np
import urllib.parse
import streamlit as st
from config import SHEET_ID, TABS

@st.cache_data(ttl=60)
def load_and_preprocess_data():
    """Fetches all tabs from Google Sheets and merges them into one Master DF"""
    all_chunks = []
    
    mapping = {
        "Objective ID": "Objective", "Objective_ID": "Objective",
        "Region/Country": "Region", "Region": "Region",
        "Date_Month": "Date_Raw", "Month": "Date_Raw",
        "Metric_Name": "Metric", "Metric Name": "Metric",
        "OKR_ID": "OKR"
    }

    for tab in TABS:
        encoded = urllib.parse.quote(tab)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        try:
            df = pd.read_csv(url).dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.rename(columns=mapping)

            # Identify value column
            val_col = next((c for c in ['Value', 'Views', 'Clicks', 'KeywordClicks', 'Active Users'] if c in df.columns), None)
            
            if val_col:
                temp = pd.DataFrame()
                temp['Objective'] = df['Objective'].astype(str).replace('nan', 'Unassigned')
                temp['Region'] = df['Region'].astype(str).replace('nan', 'Global')
                temp['OKR'] = df['OKR'].astype(str).replace('nan', 'N/A')
                temp['Metric'] = df['Metric'].astype(str).fillna(tab)
                temp['Val'] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
                temp['Source'] = tab
                
                # Date Processing
                temp['dt'] = pd.to_datetime(df['Date_Raw'], errors='coerce')
                temp = temp.dropna(subset=['dt'])
                temp['Month_Display'] = temp['dt'].dt.strftime('%b %Y')
                
                all_chunks.append(temp)
        except:
            continue

    if not all_chunks:
        return pd.DataFrame()

    return pd.concat(all_chunks, ignore_index=True)

def get_filtered_data(df, selected_tab, objectives, okrs):
    """Specific filtration logic for each tab/view"""
    filtered = df[df['Source'] == selected_tab].copy()
    
    if objectives:
        filtered = filtered[filtered['Objective'].isin(objectives)]
    if okrs:
        filtered = filtered[filtered['OKR'].isin(okrs)]
        
    return filtered
