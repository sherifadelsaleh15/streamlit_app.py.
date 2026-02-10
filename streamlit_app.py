import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS
from modules.data_loader import load_and_preprocess_data
from modules.analytics import calculate_kpis
from modules.visualizations import render_metric_chart
from modules.ml_models import generate_forecast # <--- Added this import

st.set_page_config(page_title=APP_TITLE, layout="wide")

# 1. Load Data
df = load_and_preprocess_data()

if not df.empty:
    # 2. Sidebar Filters
    st.sidebar.title("Filters")
    sel_tab = st.sidebar.selectbox("Data Source", TABS)
    
    filtered_df = df[df['Source'] == sel_tab].copy()
    
    # Cascading Objectives & OKRs
    sel_objs = st.sidebar.multiselect("Objectives", sorted(filtered_df['Objective'].unique()))
    if sel_objs:
        filtered_df = filtered_df[filtered_df['Objective'].isin(sel_objs)]
        
    sel_okrs = st.sidebar.multiselect("OKRs", sorted(filtered_df['OKR'].unique()))
    if sel_okrs:
        filtered_df = filtered_df[filtered_df['OKR'].isin(sel_okrs)]

    # 3. Main Dashboard UI
    st.title(APP_TITLE)
    stats = calculate_kpis(filtered_df)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", f"{stats['total_value']:,.0f}")
    m2.metric("Average", f"{stats['avg_value']:,.1f}")
    m3.metric("Objectives", stats['active_objectives'])
    m4.metric("Regions", stats['active_regions'])

    # 4. Grid of Charts with Forecasts
    st.divider()
    metrics = sorted(filtered_df['Metric'].unique())
    if metrics:
        cols = st.columns(2)
        for i, m_name in enumerate(metrics):
            # Pass specific metric data to the forecasting model
            m_data = filtered_df[filtered_df['Metric'] == m_name]
            f_df = generate_forecast(m_data)
            
            with cols[i % 2]:
                render_metric_chart(filtered_df, m_name, forecast_df=f_df)
    else:
        st.info("No metrics found for current filters.")
else:
    st.error("Could not load data. Check config.py and Google Sheets link.")
