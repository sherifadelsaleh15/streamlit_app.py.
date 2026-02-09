import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS ---
st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide")

# --- 2. DATA ENGINE ---
# Your published CSV link
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6yoAToWo8pkVEqypvSIISiZWTScO04siyppf_oTxZYgr_TWmD3V1h2mNnfHZHlY6x1WcEEqPkzvGW/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        # Clean headers to ensure no hidden spaces
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. Standardize Dates (01/01/2026 -> Jan 2026)
        df['dt_object'] = pd.to_datetime(df['Date_Month'], dayfirst=True, errors='coerce')
        df['Month_Display'] = df['dt_object'].dt.strftime('%b %Y')
        
        # 2. Ensure Value is numeric
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

# --- 3. DASHBOARD ---
if not df.empty:
    st.title("🎯 Strategic OKR Dashboard")

    # SIDEBAR FILTERS
    with st.sidebar:
        st.header("Filtration")
        
        # Region Filter
        all_regions = sorted(df['Region'].unique().tolist())
        sel_region = st.multiselect("Filter by Region", all_regions, default=all_regions)
        
        # Month Filter (Sorted Chronologically)
        sorted_months = df.sort_values('dt_object')['Month_Display'].unique().tolist()
        sel_months = st.multiselect("Filter by Month", sorted_months, default=sorted_months)

    # Apply Filters
    mask = (df['Region'].isin(sel_region)) & (df['Month_Display'].isin(sel_months))
    filtered_df = df[mask]

    # --- 4. DISPLAY BY OBJECTIVE ---
    objectives = filtered_df['Objective_ID'].unique()
    
    for obj in objectives:
        st.divider()
        st.subheader(f"Objective: {obj}")
        
        obj_data = filtered_df[filtered_df['Objective_ID'] == obj]
        
        # Get unique metrics in this objective
        metrics = obj_data['Metric_Name'].unique()
        
        # Create a grid for metrics
        cols = st.columns(2)
        for idx, m_name in enumerate(metrics):
            with cols[idx % 2]:
                m_data = obj_subset = obj_data[obj_data['Metric_Name'] == m_name].sort_values('dt_object')
                
                # Metric Card UI
                with st.container(border=True):
                    st.caption(f"OKR {m_data['OKR_ID'].iloc[0]}")
                    st.markdown(f"**{m_name}**")
                    
                    # Chart
                    st.area_chart(m_data, x='Month_Display', y='Value', color="#2563eb", use_container_width=True)
                    
                    # Summary Stats
                    total = m_data['Value'].sum()
                    avg = m_data['Value'].mean()
                    st.metric("Total (YTD)", f"{total:,.2f}", delta=None)

else:
    st.warning("Please check your Google Sheet publishing settings.")
