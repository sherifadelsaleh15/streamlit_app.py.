import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction

st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# 1. Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_report" not in st.session_state:
    st.session_state.ai_report = ""

# 2. Load Data
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data Loading Error: {e}")
    st.stop()

sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # --- FAILSAFE COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'VALUE', 'POSITION'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['METRIC', 'QUERY', 'KEYWORD'])), None)
    date_col = 'dt'

    if value_col:
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # --- FILTERS ---
    if loc_col:
        raw_locs = tab_df[loc_col].dropna().unique()
        all_locs = sorted([str(x) for x in raw_locs], key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- SIDEBAR: CHAT WITH DATA ---
    st.sidebar.divider()
    st.sidebar.subheader("Chat with Data")
    user_q = st.sidebar.text_input("Ask a question about this data:", key="user_input")
    if user_q:
        with st.sidebar:
            ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
            st.session_state.chat_history.append({"q": user_q, "a": ans})
    
    for chat in reversed(st.session_state.chat_history):
        st.sidebar.info(f"User: {chat['q']}")
        st.sidebar.write(f"AI: {chat['a']}")
        st.sidebar.divider()

    # --- GEMINI REPORT SECTION ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Processing..."):
            sample_forecast = None
            if value_col and len(tab_df) >= 2:
                predict_df = tab_df.rename(columns={value_col: 'Value'})
                sample_forecast = get_prediction(predict_df)
            
            st.session_state.ai_report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini", forecast_df=sample_forecast)
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)
        st.download_button(
            label="Download AI Report (TXT)",
            data=st.session_state.ai_report,
            file_name=f"Executive_Report_{sel_tab}.txt",
            mime="text/plain"
        )

    st.divider()

    # --- KEYWORD TRENDS & DATA ---
    st.subheader("Keyword Performance and Projections")
    show_forecast = st.checkbox("Show Scikit-Learn Forecasts", value=True)
    
    if metric_name_col and value_col and date_col in tab_df.columns:
        agg_sort = 'min' if is_ranking else 'sum'
        top_20 = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]
        
        c_idx = 0
        for loc in loc_list:
