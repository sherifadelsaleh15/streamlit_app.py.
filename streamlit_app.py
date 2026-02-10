import streamlit as st
import pandas as pd
import os
from config import APP_TITLE, TABS

# --- 1. MODULE IMPORTS ---
try:
    from modules.data_loader import load_and_preprocess_data
    from modules.analytics import calculate_kpis
    from modules.visualizations import render_metric_chart, render_top_pages_table
    from modules.ml_models import generate_forecast
    from modules.ui_components import (
        apply_custom_css, 
        render_header, 
        render_footer, 
        render_sidebar_logo,
        render_pdf_button
    )
    import utils
except Exception as e:
    st.error(f"Critical Module Error: {e}")
    st.stop()

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(page_title=APP_TITLE, layout="wide")

# Apply Raleway Light Mode Styling
apply_custom_css()

# --- 3. DATA LOADING ---
df = load_and_preprocess_data()

if df is not None and not df.empty:
    # --- 4. SIDEBAR NAVIGATION & FILTERS ---
    render_sidebar_logo()
    
    st.sidebar.title("Dashboard Controls")
    
    # Tab Selection
    sel_tab = st.sidebar.selectbox("Select Strategy Source", TABS)
    st.sidebar.info(utils.get_date_range_label(df))
    
    # Filter Data based on selection
    tab_df = df[df['Source'] == sel_tab].copy()
    
    # Objective Multi-select
    all_objs = sorted(tab_df['Objective'].unique())
    sel_objs = st.sidebar.multiselect("Filter Objectives / Pages", all_objs)
    if sel_objs:
        tab_df = tab_df[tab_df['Objective'].isin(sel_objs)]

    # Raw Data Toggle
    st.sidebar.markdown("---")
    show_table = st.sidebar.checkbox("📋 Show Raw Data Table", value=False)
    
    # PDF Export Button
    render_pdf_button()
    
    # --- 5. MAIN CONTENT AREA ---
    render_header(APP_TITLE, f"Insights for {sel_tab}")

    # KPI Summary Row
    stats = calculate_kpis(tab_df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Volume", f"{stats.get('total_value', 0):,.0f}")
    c2.metric("Avg Monthly", f"{stats.get('avg_value', 0):,.1f}")
    c3.metric("Active Objectives", stats.get('active_objectives', 0))
    c4.metric("Active Regions", stats.get('active_regions', 0))

    st.divider()

    # --- 6. GSC / GA4 SPECIAL VIEW ---
    # If the current tab is Google Search Console or Analytics, show the Top Pages chart
    if any(keyword in sel_tab.upper() for keyword in ["GSC", "GA4", "SEARCH", "ANALYTICS"]):
        render_top_pages_table(tab_df)
        st.divider()

    # --- 7. TREND CHARTS & FORECASTING ---
    metrics = sorted(tab_df['Metric'].unique())
    if metrics:
        st.subheader("Performance Trends")
        chart_cols = st.columns(2)
        for idx, m_name in enumerate(metrics):
            m_data = tab_df[tab_df['Metric'] == m_name]
            f_df = generate_forecast(m_data)
            with chart_cols[idx % 2]:
                render_metric_chart(tab_df, m_name, forecast_df=f_df)
    
    # --- 8. RAW DATA TABLE (IF TOGGLED) ---
    if show_table:
        st.divider()
        st.subheader(f"Raw Data Inspection: {sel_tab}")
        
        # Search box for the table
        search_query = st.text_input("Search table rows...", "")
        if search_query:
            display_df = tab_df[tab_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
        else:
            display_df = tab_df
            
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Val": st.column_config.NumberColumn("Value", format="%.2f"),
                "dt": st.column_config.DateColumn("Date")
            }
        )

    # --- 9. FOOTER ---
    render_footer()

else:
    # Error state if no data is found
    st.warning("⚠️ No data loaded. Please verify your Google Sheet configuration and Tab names.")
    if st.button("Reconnect to Source"):
        st.cache_data.clear()
        st.rerun()
