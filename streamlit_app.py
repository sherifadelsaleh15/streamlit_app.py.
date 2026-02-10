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
    
    # 1. Filter Logic (Preserving data if only one objective exists)
    obj_col = 'Objective_ID' if 'Objective_ID' in tab_df.columns else ('Objective ID' if 'Objective ID' in tab_df.columns else None)
    if obj_col:
        unique_objs = sorted(tab_df[obj_col].unique())
        if len(unique_objs) > 1:
            sel_objs = st.sidebar.multiselect(f"Filter {obj_col}", unique_objs)
            if sel_objs:
                tab_df = tab_df[tab_df[obj_col].isin(sel_objs)]

    show_table = st.sidebar.checkbox("📋 Show Raw Data Table", value=False)
    render_pdf_button()

    # Main Header
    render_header(APP_TITLE, f"Performance for {sel_tab}")

    # 2. GSC/GA4 Breakdown
    if any(k in sel_tab.upper() for k in ["GA4", "GSC", "TOP_PAGES"]):
        render_top_pages_table(tab_df, sel_tab)
        st.divider()

    # 3. Automatic Charts
    st.subheader("Performance Over Time")
    # Identify numeric columns but ignore ID columns
    numeric_cols = tab_df.select_dtypes(include=['number']).columns.tolist()
    chart_cols = [c for c in numeric_cols if not any(x in c.upper() for x in ['ID', 'POS'])]
    
    if chart_cols:
        grid = st.columns(2)
        for i, col in enumerate(chart_cols[:4]): # Limit to first 4 metrics to keep clean
            with grid[i % 2]:
                st.write(f"**Metric: {col.replace('_', ' ')}**")
                render_metric_chart(tab_df, col)
    else:
        st.info("No numeric trend data found in this tab.")

    # 4. Raw Data Table (Searchable)
    if show_table:
        st.divider()
        st.subheader("Detailed Records")
        search = st.text_input("🔍 Search rows...", "", key="table_search")
        if search:
            display_df = tab_df[tab_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        else:
            display_df = tab_df
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    render_footer()
else:
    st.error(f"Tab '{sel_tab}' is currently empty. Please check the sheet names in config.py.")
