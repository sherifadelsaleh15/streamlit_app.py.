import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS
from modules.data_loader import load_and_preprocess_data
from modules.visualizations import render_metric_chart, render_top_breakdown
from modules.ui_components import (
    apply_custom_css, render_header, render_footer, 
    render_sidebar_logo, render_pdf_button
)
# New: Import the AI Engine we updated
from modules.ai_engine import get_ai_strategic_insight

st.set_page_config(page_title=APP_TITLE, layout="wide")
apply_custom_css()

# 1. Load Data
df_dict = load_and_preprocess_data()

# 2. Sidebar Navigation & AI Settings
render_sidebar_logo()

st.sidebar.markdown("### Intelligence Settings")
selected_engine = st.sidebar.selectbox(
    "AI Engine",
    options=["groq", "gemini"],
    format_func=lambda x: "Groq (High-Speed)" if x == "groq" else "Gemini (Deep Reasoning)",
    help="Groq is nearly instant. Gemini is better for complex data patterns."
)

st.sidebar.divider()
sel_tab = st.sidebar.selectbox("Select Strategy Tab", TABS)
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    st.sidebar.markdown("---")
    
    # Objective Filter
    obj_col = 'Objective_ID' if 'Objective_ID' in tab_df.columns else ('Objective ID' if 'Objective ID' in tab_df.columns else None)
    if obj_col:
        all_objs = sorted(tab_df[obj_col].unique())
        sel_objs = st.sidebar.multiselect("Filter Objectives", all_objs, default=all_objs)
        if sel_objs:
            tab_df = tab_df[tab_df[obj_col].isin(sel_objs)]

    show_table = st.sidebar.checkbox("📋 Show Raw Data Table", value=False)
    render_pdf_button()

    # 3. Header
    render_header(APP_TITLE, f"Strategic Intelligence: {sel_tab}")

    # 4. NEW AI Strategic Insights Section (Real AI)
    with st.expander(f"🤖 Real-Time Strategy Analysis ({selected_engine.upper()})", expanded=True):
        col_insight, col_stats = st.columns([3, 1])
        
        with col_stats:
            numeric_df = tab_df.select_dtypes(include=['number'])
            if not numeric_df.empty:
                latest_month = tab_df['dt'].max()
                current_perf = tab_df[tab_df['dt'] == latest_month].select_dtypes(include=['number']).sum().iloc[0]
                st.metric("Latest Volume", f"{current_perf:,.0f}")
                st.caption(f"Data as of {latest_month.strftime('%b %Y')}")

        with col_insight:
            if st.button("🔍 Generate AI Strategic Report"):
                with st.spinner(f"Analysing trends using {selected_engine}..."):
                    # Call our updated secure engine
                    report = get_ai_strategic_insight(tab_df, sel_tab, engine=selected_engine)
                    st.markdown(report)
            else:
                st.info("Click the button above to run a deep-dive analysis on this tab's specific data.")

    # 5. Specialized Analysis (GSC/GA4)
    if any(k in sel_tab.upper() for k in ["GSC", "TOP_PAGES", "GA4"]):
        render_top_breakdown(tab_df, sel_tab)
        st.divider()

    # 6. All Metrics with Predictive Forecasting
    st.subheader("Predictive Performance Trends")
    st.caption("Solid Line = Actual Data | Dotted Line = AI Linear Regression Forecast")
    
    if 'Metric_Name' in tab_df.columns:
        metrics = sorted(tab_df['Metric_Name'].unique())
        cols = st.columns(2)
        for i, m_name in enumerate(metrics):
            m_data = tab_df[tab_df['Metric_Name'] == m_name]
            with cols[i % 2]:
                render_metric_chart(m_data, m_name, 'Value', key_suffix=f"{sel_tab}_{i}")
    else:
        num_cols = [c for c in tab_df.select_dtypes('number').columns if not any(x in c.upper() for x in ['ID', 'POS'])]
        cols = st.columns(2)
        for i, m_name in enumerate(num_cols):
            with cols[i % 2]:
                render_metric_chart(tab_df, m_name, m_name, key_suffix=f"{sel_tab}_{i}")

    # 7. Raw Data
    if show_table:
        st.divider()
        st.subheader("Source Data")
        st.dataframe(tab_df, use_container_width=True, hide_index=True)

    render_footer()
else:
    st.error(f"Tab '{sel_tab}' is empty. Check Google Sheet tab name and link share settings.")
