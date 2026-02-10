import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction

st.set_page_config(layout="wide", page_title="2026 Strategy Hub")

# 1. Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 2. Load Data
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data Loading Error: {e}")
    st.stop()

# Sidebar Selection
sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # --- FAILSAFE COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    # Priority for Value: CLICKS/SESSIONS first, then VALUE/POSITION
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['METRIC', 'QUERY', 'KEYWORD', 'TERM'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
    date_col = 'dt'

    # Clean numeric data
    if value_col:
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    # Determine if we are in an SEO Ranking tab
    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # --- FILTERS ---
    if loc_col:
        # Sort locations to put Germany at the top
        all_locs = sorted(tab_df[loc_col].unique().tolist(), key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- REPORT SECTION ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("AI is analyzing trends..."):
            sample_forecast = None
            if value_col and len(tab_df) > 2:
                sample_data = tab_df.rename(columns={value_col: 'Value'})
                sample_forecast = get_prediction(sample_data.head(20))
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini", forecast_df=sample_forecast)
            st.markdown(report)

    st.divider()

    # --- TOP LEADERBOARDS (CLEANED) ---
    st.subheader("High-Level Performance")
    col1, col2 = st.columns(2)
    
    with col1:
        if page_col and value_col:
            agg_func = 'min' if is_ranking else 'sum'
            top_pages = tab_df.groupby(page_col)[value_col].agg(agg_func).reset_index()
            top_pages = top_pages.sort_values(by=value_col, ascending=(agg_func=='min')).head(15)
            
            fig_top = px.bar(top_pages, x=value_col, y=page_col, orientation='h', 
                             title="Top 15 Pages", template="plotly_white", color=value_col)
            if is_ranking: fig_top.update_layout(xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        if metric_name_col and value_col:
            agg_func = 'min' if is_ranking else 'sum'
            top_metrics = tab_df.groupby(metric_name_col)[value_col].agg(agg_func).reset_index()
            # Fixed GSC: Only top 20 results
            top_metrics = top_metrics.sort_values(by=value_col, ascending=(agg_func=='min')).head(20)
            
            fig_kw = px.bar(top_metrics, x=value_col, y=metric_name_col, orientation='h', 
                            title="Top 20 Metrics/Keywords", template="plotly_white", color=value_col)
            if is_ranking: fig_kw.update_layout(xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_kw, use_container_width=True)

    st.divider()

    # --- INDIVIDUAL KEYWORD DATA & MONTHLY TRENDS ---
    st.subheader("Individual Keyword Deep-Dive")
    
    if metric_name_col and value_col and date_col in tab_df.columns:
        # Highlight Germany first
        locations = sorted(tab_df[loc_col].unique().tolist(), key=lambda x: x != 'Germany') if loc_col else [None]
        
        for loc in locations:
            loc_label = f"📍 Region: {loc}" if loc else "Global"
            st.markdown(f"### {loc_label}")
            
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            keywords = sorted(loc_data[metric_name_col].unique())

            for kw in keywords:
                kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
                
                # Each keyword gets an expander; Germany is open by default
                with st.expander(f"Data for: {kw}", expanded=(loc == 'Germany')):
                    c1, c2 = st.columns([2, 1])
                    
                    with c1:
                        # Monthly trend line
                        fig = px.line(kw_data, x='dt', y=value_col, markers=True, 
                                      height=300, title=f"Monthly Rank: {kw}")
                        if is_ranking:
                            fig.update_layout(yaxis=dict(autorange="reversed", title="Rank (1 is Top)"))
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with c2:
                        # Monthly data table
                        st.write("**Month-over-Month**")
                        table_data = kw_data[['dt', value_col]].copy()
                        table_data['dt'] = table_data['dt'].dt.strftime('%b %Y')
                        st.dataframe(table_data, hide_index=True, use_container_width=True)

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
