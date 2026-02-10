import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS

# Import our custom modules
from modules.data_loader import load_and_preprocess_data
from modules.analytics import calculate_kpis
from modules.visualizations import render_metric_chart
from modules.ml_models import generate_forecast
from modules.ui_components import apply_custom_css, render_header, render_footer
import utils 

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide"
)

# Apply the custom CSS
apply_custom_css()

# --- 2. DATA LOADING ---
df = load_and_preprocess_data()

if not df.empty:
    # --- 3. SIDEBAR FILTERS ---
    st.sidebar.title("Dashboard Controls")
    
    sel_tab = st.sidebar.selectbox("Select Data Source", TABS)
    
    # Display the Date Range utility in the sidebar
    st.sidebar.info(utils.get_date_range_label(df))
    
    tab_df = df[df['Source'] == sel_tab].copy()
    
    st.sidebar.markdown("---")
    
    # Filter Objectives
    obj_list = sorted(tab_df['Objective'].unique())
    sel_objs = st.sidebar.multiselect("Filter Objectives", obj_list)
    if sel_objs:
        tab_df = tab_df[tab_df['Objective'].isin(sel_objs)]
        
    # Filter OKRs
    okr_list = sorted(tab_df['OKR'].unique())
    sel_okrs = st.sidebar.multiselect("Filter OKRs", okr_list)
    if sel_okrs:
        tab_df = tab_df[tab_df['OKR'].isin(sel_okrs)]

    # --- 4. MAIN CONTENT AREA ---
    render_header(APP_TITLE, f"Strategic insights for {sel_tab}")

    # KPI Summary Row
    stats = calculate_kpis(tab_df)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.metric("Total Volume", f"{stats.get('total_value', 0):,.0f}")
    with kpi_col2:
        st.metric("Avg Monthly", f"{stats.get('avg_value', 0):,.1f}")
    with kpi_col3:
        st.metric("Objectives", stats.get('active_objectives', 0))
    with kpi_col4:
        st.metric("Active Regions", stats.get('active_regions', 0))

    st.markdown("---")

    # --- 5. CHART GRID ---
    metrics = sorted(tab_df['Metric'].unique())
    
    if metrics:
        chart_cols = st.columns(2)
        for idx, metric_name in enumerate(metrics):
            metric_data = tab_df[tab_df['Metric'] == metric_name]
            
            # Generate forecast
            f_df = generate_forecast(metric_data)
            
            with chart_cols[idx % 2]:
                render_metric_chart(tab_df, metric_name, forecast_df=f_df)
    else:
        st.info("No metrics found for the selected filters.")

    # --- 6. FOOTER ---
    render_footer()

else:
    st.error("No data loaded. Check config.py and your Google Sheet connection.")

# Refresh Button
if st.sidebar.button("Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()
