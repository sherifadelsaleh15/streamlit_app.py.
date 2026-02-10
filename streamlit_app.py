import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS
from modules.data_loader import load_and_preprocess_data
from modules.visualizations import render_metric_chart, render_top_pages_table
from modules.ui_components import (
    apply_custom_css, render_header, render_footer, 
    render_sidebar_logo, render_pdf_button
)

st.set_page_config(page_title=APP_TITLE, layout="wide")
apply_custom_css()

# Load Data
df_dict = load_and_preprocess_data()

# Sidebar
render_sidebar_logo()
sel_tab = st.sidebar.selectbox("Select Dashboard Tab", TABS)
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    st.sidebar.markdown("---")
    show_table = st.sidebar.checkbox("📋 Show Raw Data Table", value=False)
    render_pdf_button()

    # Header
    render_header(APP_TITLE, f"Performance for {sel_tab}")

    # Top Pages / Keywords Logic
    if any(k in sel_tab.upper() for k in ["GA4", "GSC", "TOP_PAGES"]):
        render_top_pages_table(tab_df)
        st.divider()

    # Auto-Charts for Numeric Columns
    st.subheader("Performance Over Time")
    numeric_cols = tab_df.select_dtypes(include=['number']).columns.tolist()
    # Filter out columns that shouldn't be charted
    chart_cols = [c for c in numeric_cols if c not in ['OKR_ID', 'Objective_ID']]
    
    if chart_cols:
        grid = st.columns(2)
        for i, col in enumerate(chart_cols[:4]): # Show top 4 metrics
            with grid[i % 2]:
                st.write(f"**Metric: {col.replace('_', ' ')}**")
                render_metric_chart(tab_df, col)

    # Raw Data Table
    if show_table:
        st.divider()
        st.subheader("Raw Data Inspection")
        search = st.text_input("🔍 Filter rows...", "")
        if search:
            display_df = tab_df[tab_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        else:
            display_df = tab_df
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    render_footer()
else:
    st.error(f"Tab '{sel_tab}' not found or empty. Please check your Google Sheet names.")
