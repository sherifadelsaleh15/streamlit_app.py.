import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS
from modules.data_loader import load_and_preprocess_data
from modules.visualizations import render_metric_chart, render_top_breakdown
from modules.ui_components import apply_custom_css, render_header, render_footer, render_sidebar_logo
from modules.ai_engine import get_ai_strategic_insight

st.set_page_config(page_title=APP_TITLE, layout="wide")
apply_custom_css()

# 1. Load Data
df_dict = load_and_preprocess_data()

# 2. Sidebar
render_sidebar_logo()

# --- NEW: Groq Chat Box in Sidebar ---
st.sidebar.subheader("💬 Fast AI Chat (Groq)")
user_query = st.sidebar.text_input("Ask about your data:")
if user_query:
    # We use engine="groq" for the quick chat
    answer = get_ai_strategic_insight(pd.concat(df_dict.values()), "Global", engine="groq", custom_prompt=user_query)
    st.sidebar.info(answer)

st.sidebar.divider()
sel_tab = st.sidebar.selectbox("Select Strategy Tab", TABS)
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # --- FIX: Objective Filter (Multi-select defaults to ALL) ---
    obj_col = next((c for c in tab_df.columns if 'Objective' in c), None)
    if obj_col:
        unique_objs = sorted(tab_df[obj_col].unique())
        # Defaulting to ALL unique objectives ensures they all appear on start
        sel_objs = st.sidebar.multiselect("Filter Objectives", unique_objs, default=unique_objs)
        tab_df = tab_df[tab_df[obj_col].isin(sel_objs)]

    # 3. Header
    render_header(APP_TITLE, f"Performance: {sel_tab}")

    # 4. Deep Summary (Gemini)
    with st.expander("📝 Deep Executive Summary (Gemini)", expanded=False):
        if st.button("Generate Monthly Report"):
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.markdown(report)

    # 5. Visualizations (All charts appear automatically)
    if any(k in sel_tab.upper() for k in ["GSC", "TOP_PAGES", "GA4"]):
        render_top_breakdown(tab_df, sel_tab)
    
    st.subheader("Performance Trends")
    # Dynamically find all numeric metrics
    if 'Metric_Name' in tab_df.columns:
        metrics = sorted(tab_df['Metric_Name'].unique())
        cols = st.columns(2)
        for i, m_name in enumerate(metrics):
            m_data = tab_df[tab_df['Metric_Name'] == m_name]
            with cols[i % 2]:
                render_metric_chart(m_data, m_name, 'Value', key_suffix=f"{sel_tab}_{i}")
    else:
        # Loop through all numeric columns (Clicks, Views, etc.)
        num_cols = [c for c in tab_df.select_dtypes('number').columns if not any(x in c.upper() for x in ['ID', 'POS'])]
        cols = st.columns(2)
        for i, m_name in enumerate(num_cols):
            with cols[i % 2]:
                render_metric_chart(tab_df, m_name, m_name, key_suffix=f"{sel_tab}_{i}")

    render_footer()
