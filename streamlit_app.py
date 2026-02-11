import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction

# 1. Page Config
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# 2. Login Security (Hardcoded Password)
def check_password():
    ADMIN_PASSWORD = "strategic_2026" 

    def password_entered():
        if st.session_state["password"] == ADMIN_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.subheader("🔒 Digital Strategy Login")
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# 3. Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_report" not in st.session_state:
    st.session_state.ai_report = ""

# 4. Load Data
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data Loading Error: {e}")
    st.stop()

sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # Column Detection
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'

    # Nuclear Cleaning (Handles commas/symbols)
    if value_col:
        def clean_currency(x):
            if isinstance(x, str):
                clean_str = re.sub(r'[^\d.]', '', x) 
                return clean_str if clean_str else '0'
            return x
        tab_df[value_col] = tab_df[value_col].apply(clean_currency)
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # Sidebar Filters
    if loc_col:
        raw_locs = tab_df[loc_col].dropna().unique()
        all_locs = sorted([str(x) for x in raw_locs], key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # Chat with Data
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

    # Visualizations
    if "GSC" in sel_tab.upper() and metric_name_col:
        st.subheader("Top 20 GSC Keywords")
        agg_k = 'min' if is_ranking else 'sum'
        top_k = tab_df.groupby(metric_name_col)[value_col].agg(agg_k).reset_index()
        top_k = top_k.sort_values(by=value_col, ascending=(agg_k=='min')).head(20)
        fig_k = px.bar(top_k, x=value_col, y=metric_name_col, orientation='h', color_discrete_sequence=['#4285F4'])
        if is_ranking: fig_k.update_layout(xaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_k, use_container_width=True)

    if ("GA4" in sel_tab.upper() or "PAGE" in sel_tab.upper()) and page_col:
        st.subheader("Top 20 GA4 Pages")
        top_p = tab_df.groupby(page_col)[value_col].sum().reset_index()
        top_p = top_p.sort_values(by=value_col, ascending=False).head(20)
        fig_p = px.bar(top_p, x=value_col, y=page_col, orientation='h', color_discrete_sequence=['#34A853'])
        st.plotly_chart(fig_p, use_container_width=True)

    st.divider()

    # Gemini Strategic Report
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."):
            sample_forecast = None
            if value_col and len(tab_df) >= 2:
                predict_df = tab_df.rename(columns={value_col: 'Value'})
                sample_forecast = get_prediction(predict_df)
            st.session_state.ai_report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini", forecast_df=sample_forecast)
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    # Monthly Trends
    st.subheader("Monthly Performance Trends")
    if metric_name_col and value_col and date_col in tab_df.columns:
        agg_sort = 'min' if is_ranking else 'sum'
        top_20_list = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()
        
        for loc in (tab_df[loc_col].unique() if loc_col else [None]):
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"**Region: {loc if loc else 'Global'}**")
            region_keywords = [kw for kw in top_20_list if kw in loc_data[metric_name_col].unique()]

            for kw in region_keywords:
                kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
                with st.expander(f"Data for: {kw}"):
                    fig = px.line(kw_data, x='dt', y=value_col, markers=True, title=f"Trend: {kw}")
                    if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig, use_container_width=True)
