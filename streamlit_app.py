import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

# Custom CSS to make filters easier to click
st.markdown("""
    <style>
    .stMultiSelect div[data-baseweb="select"] {
        background-color: white;
        border-radius: 8px;
    }
    .chart-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def fetch_and_clean(tab_name):
    encoded_name = urllib.parse.quote(tab_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        df = pd.read_csv(url)
        # CRITICAL: Strip spaces from headers AND data
        df.columns = [str(c).strip() for c in df.columns]
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        # Unified Mapping
        mapping = {
            'Month': 'Month', 'Date_Month': 'Month', 'Date Month': 'Month',
            'Region/Country': 'Region', 'Region': 'Region',
            'Metric Name': 'Metric', 'Metric_Name': 'Metric'
        }
        df = df.rename(columns=mapping)
        
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# --- 3. SELECTION & FILTRATION ---
st.title("🚀 2026 Strategy Command")

tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.selectbox("📂 Data Source", tabs)

df = fetch_and_clean(selected_tab)

if not df.empty:
    # Sidebar Filters
    st.sidebar.header("🎛️ Filters")
    
    # 1. Month Filter
    if 'Month' in df.columns:
        month_list = sorted(df['Month'].unique().tolist())
        # We use a unique KEY to prevent the filter from breaking on refresh
        sel_months = st.sidebar.multiselect("Select Month", options=month_list, default=month_list, key=f"month_{selected_tab}")
    else:
        sel_months = []

    # 2. Region Filter
    if 'Region' in df.columns:
        region_list = sorted(df['Region'].unique().tolist())
        sel_regions = st.sidebar.multiselect("Select Region", options=region_list, default=region_list, key=f"reg_{selected_tab}")
    else:
        sel_regions = []

    # APPLY FILTERS
    filtered_df = df.copy()
    if sel_months:
        filtered_df = filtered_df[filtered_df['Month'].isin(sel_months)]
    if sel_regions:
        filtered_df = filtered_df[filtered_df['Region'].isin(sel_regions)]

    # --- 4. DISPLAY ---
    # Metric Cards
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Value", f"{filtered_df['Value'].sum() if 'Value' in filtered_df.columns else 0:,.0f}")
    with m2:
        st.metric("Visible Rows", len(filtered_df))
    with m3:
        st.metric("Status", "Filtered" if len(filtered_df) < len(df) else "All Data")

    st.divider()

    # Dynamic OKR Charts
    id_col = next((c for c in ['OKR_ID', 'Metric', 'Objective ID'] if c in filtered_df.columns), None)
    
    if id_col and not filtered_df.empty:
        for item in filtered_df[id_col].unique():
            item_data = filtered_df[filtered_df[id_col] == item]
            
            st.markdown(f'<div class="chart-card"><h4>📈 {item}</h4>', unsafe_allow_html=True)
            c_left, c_right = st.columns([2, 1])
            with c_left:
                st.area_chart(item_data, x='Month' if 'Month' in item_data.columns else None, y='Value', color="#1e293b")
            with c_right:
                st.dataframe(item_data[['Month', 'Value', 'Region']] if 'Region' in item_data.columns else item_data, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.dataframe(filtered_df, use_container_width=True)

else:
    st.error("Data could not be loaded. Check your Google Sheet Tab names.")
