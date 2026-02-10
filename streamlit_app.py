import streamlit as st
from config import APP_TITLE, TABS
from modules.data_loader import load_and_preprocess_data
from modules.analytics import calculate_kpis
from modules.visualizations import render_metric_chart

st.set_page_config(page_title=APP_TITLE, layout="wide")

# 1. Load Data
df = load_and_preprocess_data()

if not df.empty:
    st.title(f"🎯 {APP_TITLE}")
    
    # 2. Sidebar Filters (Logic per Tab)
    st.sidebar.header("Global Filters")
    sel_tab = st.sidebar.selectbox("Select Data Source (Tab)", TABS)
    
    tab_df = df[df['Source'] == sel_tab]
    
    sel_objs = st.sidebar.multiselect("Filter Objectives", sorted(tab_df['Objective'].unique()))
    if sel_objs:
        tab_df = tab_df[tab_df['Objective'].isin(sel_objs)]
        
    sel_okrs = st.sidebar.multiselect("Filter OKRs", sorted(tab_df['OKR'].unique()))
    if sel_okrs:
        tab_df = tab_df[tab_df['OKR'].isin(sel_okrs)]

    # 3. KPI Row
    stats = calculate_kpis(tab_df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Value", f"{stats['total_value']:,}")
    c2.metric("Avg Performance", f"{stats['avg_value']:,.1f}")
    c3.metric("Objectives", stats['active_objectives'])
    c4.metric("Regions", stats['active_regions'])

    st.markdown("---")

    # 4. Grid of Charts
    metrics = tab_df['Metric'].unique()
    cols = st.columns(2)
    for idx, m in enumerate(metrics):
        with cols[idx % 2]:
            render_metric_chart(tab_df, m)

else:
    st.error("Data not found. Please check your Google Sheet and config.py.")
