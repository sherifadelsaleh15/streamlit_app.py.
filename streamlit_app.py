import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction

st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# 1. State Management
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 2. Data Loading
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data Loading Error: {e}")
    st.stop()

sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # --- SMART COLUMN MAPPING & CLEANING ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'METRIC'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
    date_col = 'dt'

    # CLEANING: Remove commas and convert to numbers to fix the "0" values issue
    if value_col:
        tab_df[value_col] = tab_df[value_col].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('%', '')
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # --- FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].unique().tolist(), key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect("Filter Regions", all_locs, default=all_locs)
        # Apply filter to the dataframe
        filtered_df = tab_df[tab_df[loc_col].isin(sel_locs)]
    else:
        filtered_df = tab_df

    # --- CHAT WITH DATA ---
    st.sidebar.divider()
    st.sidebar.subheader("Chat with Data")
    user_q = st.sidebar.text_input("Ask a question:", key="chat_input")
    if user_q:
        with st.sidebar:
            # We pass the FILTERED data so AI only sees what you want
            ans = get_ai_strategic_insight(filtered_df, sel_tab, engine="groq", custom_prompt=user_q)
            st.session_state.chat_history.append({"q": user_q, "a": ans})
    
    for chat in reversed(st.session_state.chat_history):
        st.sidebar.info(f"User: {chat['q']}")
        st.sidebar.write(f"AI: {chat['a']}")

    # --- TOP 20 ANALYSIS ---
    st.subheader(f"Top 20 Leaderboard: {sel_tab}")
    # Determine the label column based on the tab type
    label_col = metric_name_col if "GSC" in sel_tab.upper() else page_col
    
    if label_col and value_col:
        agg_func = 'min' if is_ranking else 'sum'
        top_data = filtered_df.groupby(label_col)[value_col].agg(agg_func).reset_index()
        top_data = top_data.sort_values(by=value_col, ascending=(agg_func=='min')).head(20)
        
        fig = px.bar(top_data, x=value_col, y=label_col, orientation='h', template="plotly_white")
        if is_ranking: fig.update_layout(xaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # --- TRENDS SECTION ---
    st.subheader("Monthly Growth Trends")
    # Trends logic for specific items (Keywords/Pages)
    if label_col and date_col in filtered_df.columns:
        # Limit to top 5 for visual clarity
        top_items = filtered_df.groupby(label_col)[value_col].sum().sort_values(ascending=False).head(5).index
        trend_data = filtered_df[filtered_df[label_col].isin(top_items)]
        fig_trend = px.line(trend_data, x=date_col, y=value_col, color=label_col, markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)
