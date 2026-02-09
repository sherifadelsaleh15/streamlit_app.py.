import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# --- 1. SETTINGS & PREMIUM UI ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #fcfcfd; }
    
    /* Elegant Metric Cards */
    div[data-testid="stMetric"] {
        background-color: white; border: 1px solid #f0f2f6; padding: 20px; border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    }
    
    /* Chart Container Styling */
    .chart-container {
        background-color: white; border: 1px solid #f0f2f6; padding: 25px;
        border-radius: 20px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .chart-title { color: #1e293b; font-size: 20px; font-weight: 700; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def fetch_and_clean(tab_name):
    encoded_name = urllib.parse.quote(tab_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        
        # Unified Mapping
        mapping = {'Month': 'Month', 'Date_Month': 'Month', 'Region/Country': 'Region', 'Metric Name': 'Metric'}
        df = df.rename(columns=mapping)
        
        # Clean numeric data
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
            
        return df
    except:
        return pd.DataFrame()

# --- 3. GLOBAL FILTRATION & LOGIC ---
st.title("🚀 2026 Strategy Command Center")

tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.selectbox("📂 Select Intelligence Layer", tabs)

df = fetch_and_clean(selected_tab)

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # A. MONTH FILTER (Plan Step 3)
        if 'Month' in df.columns:
            # Sort months chronologically
            month_order = ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026', 
                           'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026']
            existing_months = [m for m in month_order if m in df['Month'].unique()]
            sel_months = st.multiselect("Select Months", options=existing_months, default=existing_months)
            df = df[df['Month'].isin(sel_months)]

        # B. OTHER FILTERS
        f_cols = [c for c in ['Region', 'Metric', 'Objective ID', 'Source'] if c in df.columns]
        for col in f_cols:
            opts = sorted(df[col].unique().tolist())
            sel = st.multiselect(f"Select {col}", options=opts, default=opts)
            df = df[df[col].isin(sel)]

    # --- 4. VISUAL DASHBOARD ---
    # Top Level KPI Row
    k1, k2, k3 = st.columns(3)
    with k1:
        total = df['Value'].sum() if 'Value' in df.columns else len(df)
        st.metric("Aggregate Performance", f"{total:,.0f}")
    with k2:
        st.metric("Data Dimensions", len(df.columns))
    with k3:
        st.metric("Status", "Live Sync", delta="100%")

    st.divider()

    # --- 5. ENHANCED CHARTING ---
    # If the sheet has an OKR_ID or Metric, we split into "Small Multiples"
    split_col = next((c for c in ['OKR_ID', 'Metric', 'Objective ID'] if c in df.columns), None)
    
    if split_col and 'Month' in df.columns:
        unique_items = df[split_col].unique()
        
        for item in unique_items:
            item_data = df[df[split_col] == item].copy()
            
            # Use a container for the "Card" look
            st.markdown(f"""<div class="chart-container">
                            <div class="chart-title">📊 {item}</div>""", unsafe_allow_html=True)
            
            c_left, c_right = st.columns([2, 1])
            with c_left:
                # Custom dark-theme Area Chart
                st.area_chart(item_data, x='Month', y='Value', color="#1e293b")
            with c_right:
                st.dataframe(item_data[['Month', 'Value']].sort_values('Month'), hide_index=True, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.subheader("General Trend")
        st.area_chart(df, x='Month' if 'Month' in df.columns else None, y='Value' if 'Value' in df.columns else None)
        st.dataframe(df, use_container_width=True)

else:
    st.info("Check your Google Sheet tab names or sharing settings.")
