import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS
from modules.data_loader import load_and_preprocess_data
from modules.visualizations import render_metric_chart, render_top_breakdown
from modules.ui_components import (
    apply_custom_css, render_header, render_footer, 
    render_sidebar_logo, render_pdf_button
)
from modules.ai_engine import get_ai_strategic_insight

# 1. Page Configuration
st.set_page_config(page_title=APP_TITLE, layout="wide")
apply_custom_css()

# 2. Data Loading
df_dict = load_and_preprocess_data()

# 3. Sidebar Setup
render_sidebar_logo()

st.sidebar.title("🌍 Global Filters")

# Tab Selection
sel_tab = st.sidebar.selectbox("Select Strategy Tab", TABS)
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # --- FIX: REGION & COUNTRY DETECTION ---
    # Dynamically find columns for Region/Country/Geo
    region_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    
    if region_col:
        all_regions = sorted(tab_df[region_col].unique())
        # Default to ALL regions selected
        sel_regions = st.sidebar.multiselect(f"Filter by {region_col}", all_regions, default=all_regions)
        tab_df = tab_df[tab_df[region_col].isin(sel_regions)]

    # --- FIX: OBJECTIVE AUTO-SELECT ---
    obj_col = next((c for c in tab_df.columns if 'OBJECTIVE' in c.upper()), None)
    if obj_col:
        all_objs = sorted(tab_df[obj_col].unique())
        # Default to ALL objectives selected so charts appear immediately
        sel_objs = st.sidebar.multiselect("Filter Objectives", all_objs, default=all_objs)
        tab_df = tab_df[tab_df[obj_col].isin(sel_objs)]

    st.sidebar.divider()
    
    # --- SIDEBAR AI CHAT (GROQ) ---
    st.sidebar.subheader("💬 Chat with Data (Groq)")
    user_q = st.sidebar.text_input("Ask about these regions/rows:")
    if user_q:
        with st.sidebar:
            with st.spinner("Groq is scanning rows..."):
                chat_res = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
                st.info(chat_res)

    # 4. Main Dashboard Header
    render_header(APP_TITLE, f"Analysis: {sel_tab}")

    # 5. EXECUTIVE SUMMARY (GEMINI)
    with st.expander("📝 Deep Executive Analysis (Gemini)", expanded=False):
        if st.button("Generate Regional Performance Report"):
            with st.spinner("Gemini is analyzing all rows..."):
                report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
                st.markdown(report)

    # 6. CHARTS (Automatic rendering for all metrics/rows)
    st.subheader("📊 Performance Trends")
    
    # Identify value columns (Metric_Name or generic numeric columns)
    if 'Metric_Name' in tab_df.columns:
        metrics = sorted(tab_df['Metric_Name'].unique())
        cols = st.columns(2)
        for i, m_name in enumerate(metrics):
            m_data = tab_df[tab_df['Metric_Name'] == m_name]
            with cols[i % 2]:
                render_metric_chart(m_data, m_name, 'Value', key_suffix=f"{sel_tab}_{i}")
    else:
        # Fallback: find all numeric columns that aren't IDs
        num_cols = [c for c in tab_df.select_dtypes('number').columns 
                    if not any(x in c.upper() for x in ['ID', 'POS', 'YEAR', 'MONTH'])]
        cols = st.columns(2)
        for i, m_name in enumerate(num_cols):
            with cols[i % 2]:
                render_metric_chart(tab_df, m_name, m_name, key_suffix=f"{sel_tab}_{i}")

    # 7. SPECIALIZED BREAKDOWNS (GSC/GA4 Pages)
    if any(k in sel_tab.upper() for k in ["GSC", "TOP_PAGES", "GA4"]):
        st.divider()
        render_top_breakdown(tab_df, sel_tab)

    # 8. RAW DATA PREVIEW
    with st.expander("📋 View Filtered Source Data"):
        st.dataframe(tab_df, use_container_width=True, hide_index=True)

    render_footer()
else:
    st.error(f"Tab '{sel_tab}' contains no data. Please check your source file.")
