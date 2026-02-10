import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight

st.set_page_config(layout="wide")

# 1. Load Data
df_dict = load_and_preprocess_data()
sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # --- FILTERS ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    if loc_col:
        all_locs = sorted(tab_df[loc_col].unique())
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- REPORT SECTION ---
    st.subheader("Report")
    if st.button("Generate Report"):
        report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
        st.write(report)
        st.download_button("Download Report", report, file_name="report.txt")

    st.divider()

    # --- DATA TABLE SECTION ---
    st.subheader("Data Table")
    st.dataframe(tab_df, use_container_width=True)
    st.download_button("Download Table CSV", tab_df.to_csv(index=False), file_name="data_table.csv")

    st.divider()

    # --- CHART SECTION (FIXED FOR GSC/GA4) ---
    st.subheader("Charts")
    
    # Check for Long Format (OKR style) vs Wide Format (Analytics style)
    metric_name_col = next((c for c in tab_df.columns if 'METRIC' in c.upper()), None)
    
    # Determine the Y-axis column. If 'Value' exists, use it. 
    # Otherwise, we use the numeric columns (Clicks, Impressions, etc.)
    has_value_col = 'Value' in tab_df.columns

    if metric_name_col and has_value_col:
        # CASE: OKR/Social sheets (Metric Name + Value columns)
        unique_metrics = sorted(tab_df[metric_name_col].unique())
        for loc in (sorted(tab_df[loc_col].unique()) if loc_col else [None]):
            if loc: st.write(f"Location: {loc}")
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            cols = st.columns(2)
            for i, met in enumerate(unique_metrics):
                chart_df = loc_data[loc_data[metric_name_col] == met]
                if not chart_df.empty:
                    with cols[i % 2]:
                        fig = px.line(chart_df, x='dt', y='Value', title=f"{met} - {loc if loc else ''}", markers=True)
                        st.plotly_chart(fig, use_container_width=True)
    else:
        # CASE: GSC/GA4 sheets (Metrics are actual column names)
        # Find numeric columns that are likely metrics
        num_cols = [c for c in tab_df.select_dtypes('number').columns 
                    if not any(x in c.upper() for x in ['ID', 'YEAR', 'MONTH', 'POSITION'])]
        
        for loc in (sorted(tab_df[loc_col].unique()) if loc_col else [None]):
            if loc: st.write(f"Location: {loc}")
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            cols = st.columns(2)
            for i, col_name in enumerate(num_cols):
                if not loc_data[col_name].dropna().empty:
                    with cols[i % 2]:
                        # FIXED: We use 'col_name' for the Y-axis instead of 'Value'
                        fig = px.line(loc_data, x='dt', y=col_name, title=f"{col_name} - {loc if loc else ''}", markers=True)
                        st.plotly_chart(fig, use_container_width=True)

    # --- SIDEBAR CHAT ---
    st.sidebar.divider()
    if st.sidebar.button("Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

    user_q = st.sidebar.text_input("Ask about data:")
    if user_q:
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
        st.session_state.chat_history.append((user_q, ans))
    
    for q, a in st.session_state.chat_history[::-1]:
        st.sidebar.write(f"User: {q}")
        st.sidebar.write(f"Assistant: {a}")
