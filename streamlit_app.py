import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. PREMIUM STYLING ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
        background-color: #f8fafc;
        color: #1e293b;
    }
    
    /* Objective Section Header */
    .obj-section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 40px;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #cbd5e1;
    }
    
    /* Card Design */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Typography inside Card */
    .card-okr-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .card-obj-subtitle {
        font-size: 0.85rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 20px;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def fetch_data(tab_name):
    encoded_name = urllib.parse.quote(tab_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Unified Schema Mapping
        mapping = {
            'Month': 'Month', 'Date_Month': 'Month', 'Date Month': 'Month',
            'Region/Country': 'Region', 'Region': 'Region',
            'Objective ID': 'Objective', 'Objective_ID': 'Objective',
            # Map various columns to 'OKR_Name'
            'Metric Name': 'OKR_Name', 'OKR_ID': 'OKR_Name', 'Metric_Name': 'OKR_Name',
            'Page Path': 'OKR_Name', 'Query': 'OKR_Name',
            'Social Network': 'OKR_Name', 'Channel': 'OKR_Name'
        }
        df = df.rename(columns=mapping)
        
        # Fix Duplicate Columns (Crucial for preventing crashes)
        df = df.loc[:, ~df.columns.duplicated()]
        
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
            
        return df
    except:
        return pd.DataFrame()

# --- 3. NAVIGATION ---
st.sidebar.header("NAVIGATOR")
tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.radio("Select Source", tabs)

df = fetch_data(selected_tab)

# --- 4. DASHBOARD LOGIC ---
if not df.empty:
    st.title(f"📊 {selected_tab.replace('_', ' ')}")
    
    # Filters
    with st.expander("🔎 Filter Data", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            months = sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else []
            sel_months = st.multiselect("Select Months", months, default=months, key=f"m_{selected_tab}")
        with c2:
            regions = sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else []
            sel_regions = st.multiselect("Select Regions", regions, default=regions, key=f"r_{selected_tab}")

    # Apply Filters
    f_df = df.copy()
    if sel_months and 'Month' in f_df.columns: f_df = f_df[f_df['Month'].isin(sel_months)]
    if sel_regions and 'Region' in f_df.columns: f_df = f_df[f_df['Region'].isin(sel_regions)]

    # --- HIERARCHY RENDERER ---
    
    # 1. Detect Objective Column
    obj_col = 'Objective' if 'Objective' in f_df.columns else None
    okr_col = 'OKR_Name' if 'OKR_Name' in f_df.columns else None
    
    # Fallback: If no Objective column, use a placeholder
    if not obj_col and okr_col:
        f_df['Objective'] = "General Objectives"
        obj_col = 'Objective'

    if obj_col and okr_col and 'Value' in f_df.columns:
        # Loop through Objectives
        unique_objs = f_df[obj_col].unique()
        
        for obj in unique_objs:
            # SECTION HEADER
            st.markdown(f'<div class="obj-section-header">🚩 {obj}</div>', unsafe_allow_html=True)
            
            # Get OKRs for this Objective
            obj_data = f_df[f_df[obj_col] == obj]
            unique_okrs = obj_data[okr_col].unique()
            
            for okr in unique_okrs:
                okr_data = obj_data[obj_data[okr_col] == okr]
                
                # Sort Chronologically
                if 'Month' in okr_data.columns:
                    okr_data = okr_data.sort_values('Month')

                # OKR CARD
                with st.container():
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    
                    # TITLE BLOCK: Objective + OKR Name
                    st.markdown(f'<div class="card-okr-title">{okr}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="card-obj-subtitle">GOAL: {obj}</div>', unsafe_allow_html=True)
                    
                    c_chart, c_stat = st.columns([3, 1])
                    
                    with c_chart:
                        # Area Chart
                        st.area_chart(okr_data, x='Month' if 'Month' in okr_data.columns else None, y='Value', color="#3b82f6")
                    
                    with c_stat:
                        total = okr_data['Value'].sum()
                        st.markdown('<div class="card-obj-subtitle">TOTAL VALUE</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="stat-value">{total:,.0f}</div>', unsafe_allow_html=True)
                        st.dataframe(okr_data[['Month', 'Value']], hide_index=True, use_container_width=True, height=150)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Data structure requires 'Objective' and 'Metric Name' columns.")
        st.dataframe(f_df, use_container_width=True)

    # --- 5. AI CHAT ---
    st.markdown("---")
    st.subheader("🤖 Strategy Assistant")
    q = st.chat_input("Ask about any Objective or Result...")
    if q:
        with st.chat_message("assistant"):
            words = q.lower().split()
            res = df.copy()
            for w in words:
                res = res[res.apply(lambda r: r.astype(str).str.lower().str.contains(w).any(), axis=1)]
            if not res.empty:
                st.write(f"Found {len(res)} matching records:")
                st.dataframe(res)
            else:
                st.write("No matches found.")

else:
    st.error("Unable to load data. Please check your Google Sheet tabs.")
