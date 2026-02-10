import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
# from utils import get_prediction  <-- COMMENTED OUT TO FIX CRASH

st.set_page_config(layout="wide", page_title="Strategic OKR Dashboard")

# 1. Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 2. Load Data
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data Loading Error: {e}")
    st.stop()

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
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("AI is analyzing..."):
            # specific_forecast = None  <-- DISABLED FOR STABILITY
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.markdown(report)

    st.divider()

    # --- DATA TABLE ---
    st.subheader("Data Explorer")
    st.dataframe(tab_df, use_container_width=True)
    
    st.divider()

    # --- CHARTS ---
    st.subheader("Performance Charts")
    
    metric_name_col = next((c for c in tab_df.columns if 'METRIC' in c.upper()), None)
    has_value_col = 'Value' in tab_df.columns
    locations = sorted(tab_df[loc_col].unique()) if loc_col else [None]
    
    chart_counter = 0 
    for loc in locations:
        loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
        
        if metric_name_col and has_value_col:
            unique_metrics = sorted(loc_data[metric_name_col].unique())
            for met in unique_metrics:
                chart_df = loc_data[loc_data[metric_name_col] == met].sort_values('dt')
                if not chart_df.empty:
                    chart_counter += 1
                    with st.container():
                        st.markdown(f"### {met} - {loc if loc else ''}")
                        fig = px.line(chart_df, x='dt', y='Value', markers=True)
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{chart_counter}")
                        st.write("---")

    # --- SIDEBAR CHAT ---
    st.sidebar.divider()
    user_q = st.sidebar.text_input("Ask AI about this data:", key="user_input")
    if user_q:
        with st.sidebar:
            with st.spinner("Thinking..."):
                ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
                st.session_state.chat_history.append((user_q, ans))
    
    if st.session_state.chat_history:
        for q, a in st.session_state.chat_history[::-1]:
            st.sidebar.info(f"**You:** {q}")
            st.sidebar.write(f"**AI:** {a}")
            st.sidebar.divider()
