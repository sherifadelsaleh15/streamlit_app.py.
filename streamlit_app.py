import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS
from modules.data_loader import load_and_preprocess_data
from modules.visualizations import render_metric_chart, render_top_breakdown
from modules.ui_components import (
    apply_custom_css, render_header, render_footer, 
    render_sidebar_logo, render_pdf_button
)

st.set_page_config(page_title=APP_TITLE, layout="wide")
apply_custom_css()

# 1. Load Data
df_dict = load_and_preprocess_data()

# 2. Sidebar Setup
render_sidebar_logo()
sel_tab = st.sidebar.selectbox("Select Strategy Tab", TABS)
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    st.sidebar.markdown("---")
    
    # --- Objective Filter (RESTORED) ---
    if 'Objective_ID' in tab_df.columns:
        all_objs = sorted(tab_df['Objective_ID'].unique())
        sel_objs = st.sidebar.multiselect("Filter Objectives", all_objs, default=all_objs)
        if sel_objs:
            tab_df = tab_df[tab_df['Objective_ID'].isin(sel_objs)]

    show_table = st.sidebar.checkbox("📋 Show Raw Data Table", value=False)
    render_pdf_button()

    # 3. Main Header
    render_header(APP_TITLE, f"Performance: {sel_tab}")

    # 4. Specialized Breakdown (GSC/GA4 Top Pages)
    if any(k in sel_tab.upper() for k in ["GSC", "TOP_PAGES"]):
        render_top_breakdown(tab_df, sel_tab)
        st.divider()

    # 5. Render All Metrics (Dynamic Loop)
    st.subheader("Monthly Metrics & Trends")
    
    # Logic: If tab has 'Metric_Name' column (like GA4_Data or Social), split charts by that.
    # Otherwise, loop through numeric columns (like Clicks, Avg Position).
    if 'Metric_Name' in tab_df.columns:
        metrics = sorted(tab_df['Metric_Name'].unique())
        cols = st.columns(2)
        for i, m_name in enumerate(metrics):
            m_data = tab_df[tab_df['Metric_Name'] == m_name]
            val_col = 'Value' if 'Value' in m_data.columns else m_data.select_dtypes('number').columns[0]
            with cols[i % 2]:
                render_metric_chart(m_data, m_name, val_col, key_suffix=f"{sel_tab}_{i}")
    else:
        # Fallback for tabs without 'Metric_Name' - plot all numeric columns
        numeric_cols = tab_df.select_dtypes(include=['number']).columns.tolist()
        # Filter out ID columns
        chart_metrics = [c for c in numeric_cols if not any(x in c.upper() for x in ['ID', 'POS'])]
        cols = st.columns(2)
        for i, m_name in enumerate(chart_metrics):
            with cols[i % 2]:
                render_metric_chart(tab_df, m_name, m_name, key_suffix=f"{sel_tab}_{i}")

    # 6. Raw Data Table
    if show_table:
        st.divider()
        st.subheader("Source Data")
        st.dataframe(tab_df, use_container_width=True, hide_index=True)

    render_footer()
else:
    st.error(f"Tab '{sel_tab}' not found or empty. Please check your config.py TABS names.")
