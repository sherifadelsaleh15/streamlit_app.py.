import streamlit as st
from config import APP_TITLE, TABS
from modules.data_loader import load_and_preprocess_data
from modules.analytics import calculate_kpis
from modules.visualizations import render_metric_chart
from modules.ml_models import generate_forecast
from modules.ui_components import (
    apply_custom_css, 
    render_header, 
    render_footer, 
    render_sidebar_logo,
    render_pdf_button
)
import utils

# Page Config
st.set_page_config(page_title=APP_TITLE, layout="wide")

# Apply Styling
apply_custom_css()

# Load Data
df = load_and_preprocess_data()

if df is not None and not df.empty:
    # Sidebar Area
    render_sidebar_logo()
    st.sidebar.title("Dashboard Controls")
    
    sel_tab = st.sidebar.selectbox("Select Data Source", TABS)
    st.sidebar.info(utils.get_date_range_label(df))
    
    # Filter Logic
    tab_df = df[df['Source'] == sel_tab].copy()
    sel_objs = st.sidebar.multiselect("Filter Objectives", sorted(tab_df['Objective'].unique()))
    if sel_objs:
        tab_df = tab_df[tab_df['Objective'].isin(sel_objs)]
    
    # PDF Button
    render_pdf_button()
    
    # Main Content Area
    render_header(APP_TITLE, f"Strategic insights for {sel_tab}")
    
    # KPI Row
    stats = calculate_kpis(tab_df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Volume", f"{stats.get('total_value', 0):,.0f}")
    c2.metric("Avg Monthly", f"{stats.get('avg_value', 0):,.1f}")
    c3.metric("Objectives", stats.get('active_objectives', 0))
    c4.metric("Active Regions", stats.get('active_regions', 0))
    
    st.divider()
    
    # Chart Grid
    metrics = sorted(tab_df['Metric'].unique())
    if metrics:
        chart_cols = st.columns(2)
        for idx, m_name in enumerate(metrics):
            m_data = tab_df[tab_df['Metric'] == m_name]
            f_df = generate_forecast(m_data)
            with chart_cols[idx % 2]:
                render_metric_chart(tab_df, m_name, forecast_df=f_df)
    
    render_footer()
else:
    st.error("Data connection failed. Please check config.py.")
