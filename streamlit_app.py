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
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['METRIC', 'QUERY', 'KEYWORD', 'TERM'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
    date_col = 'dt'

    # Clean numeric data & handle mixed types
    if value_col:
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # --- FILTERS ---
    if loc_col:
        # Clean and sort locations, forcing Germany to the top
        raw_locs = tab_df[loc_col].dropna().unique()
        all_locs = sorted([str(x) for x in raw_locs], key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- TOP LEADERBOARDS ---
    st.subheader("Performance Overview")
    col1, col2 = st.columns(2)
    
    with col1:
        if page_col and value_col:
            agg_func = 'min' if is_ranking else 'sum'
            top_pages = tab_df.groupby(page_col)[value_col].agg(agg_func).reset_index()
            top_pages = top_pages.sort_values(by=value_col, ascending=(agg_func=='min')).head(15)
            fig_top = px.bar(top_pages, x=value_col, y=page_col, orientation='h', title="Top 15 Pages", template="plotly_white")
            if is_ranking: fig_top.update_layout(xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_top, use_container_width=True, key="main_top_pages_bar")

    with col2:
        if metric_name_col and value_col:
            agg_func = 'min' if is_ranking else 'sum'
            top_metrics = tab_df.groupby(metric_name_col)[value_col].agg(agg_func).reset_index()
            top_metrics = top_metrics.sort_values(by=value_col, ascending=(agg_func=='min')).head(20)
            fig_kw = px.bar(top_metrics, x=value_col, y=metric_name_col, orientation='h', title="Top 20 Keywords", template="plotly_white")
            if is_ranking: fig_kw.update_layout(xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_kw, use_container_width=True, key="main_top_keywords_bar")

    st.divider()

    # --- INDIVIDUAL KEYWORD TRENDS (MONTHLY) ---
    st.subheader("Monthly Keyword Deep-Dive")
    
    if metric_name_col and value_col and date_col in tab_df.columns:
        # Get the list of top 20 keywords globally for this tab to generate charts
        agg_sort = 'min' if is_ranking else 'sum'
        top_20_global = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()

        # Group by Region, prioritizing Germany
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]
        
        chart_idx = 0
        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"### 📍 Region: {loc if loc else 'Global'}")
            
            # Filter the global top 20 for keywords that actually exist in this specific region
            region_keywords = [kw for kw in top_20_global if kw in loc_data[metric_name_col].unique()]

            for kw in region_keywords:
                kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
                chart_idx += 1
                
                # Expand Germany by default
                with st.expander(f"Monthly Trend: {kw}", expanded=(loc == 'Germany')):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        fig = px.line(kw_data, x='dt', y=value_col, markers=True, height=350)
                        if is_ranking:
                            fig.update_layout(yaxis=dict(autorange="reversed", title="Rank (Lower is Better)"))
                        # UNIQUE KEY FIX:
                        st.plotly_chart(fig, use_container_width=True, key=f"line_chart_{loc}_{chart_idx}")
                    
                    with c2:
                        st.write("**Monthly Data**")
                        table_data = kw_data[['dt', value_col]].copy()
                        table_data['dt'] = table_data['dt'].dt.strftime('%b %Y')
                        st.dataframe(table_data, hide_index=True, use_container_width=True, key=f"table_{loc}_{chart_idx}")
