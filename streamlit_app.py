import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction

st.set_page_config(layout="wide", page_title="2026 Strategy Intelligence Hub")

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
    # We find the best match for each required data type
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    
    # Priority for Value: CLICKS/SESSIONS first, then VALUE/POSITION
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION'])), None)
    
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['METRIC', 'QUERY', 'KEYWORD', 'TERM'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
    date_col = 'dt' # Standardized by our loader

    # Ensure value_col is actually numeric (Fixes the "0" value/empty chart issue)
    if value_col:
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    # --- FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- REPORT SECTION ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("AI is analyzing trends..."):
            sample_forecast = None
            if value_col and len(tab_df) > 2:
                # Standardize for the prediction utility
                sample_data = tab_df.rename(columns={value_col: 'Value'})
                sample_forecast = get_prediction(sample_data.head(20))
                
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini", forecast_df=sample_forecast)
            st.markdown(report)

    st.divider()

    # --- DATA TABLE ---
    st.subheader("Data Explorer")
    st.dataframe(tab_df, use_container_width=True)
    
    st.divider()

    # --- TOP LISTS (BAR CHARTS) ---
    col1, col2 = st.columns(2)
    
    # Determine if we are looking at Rankings (where lower is better)
    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    with col1:
        if page_col and value_col:
            st.subheader("Top Performance by Page")
            agg_func = 'min' if is_ranking else 'sum'
            top_pages = tab_df.groupby(page_col)[value_col].agg(agg_func).reset_index()
            top_pages = top_pages.sort_values(by=value_col, ascending=(agg_func=='min')).head(15)
            
            fig_top = px.bar(top_pages, x=value_col, y=page_col, orientation='h', 
                             color=value_col, template="plotly_white",
                             color_continuous_scale='Viridis' if is_ranking else 'Blues')
            
            if is_ranking:
                fig_top.update_layout(xaxis=dict(autorange="reversed", title="Best Rank"))
            
            st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        if metric_name_col and value_col:
            st.subheader("Top Performance by Metric/Keyword")
            agg_func = 'min' if is_ranking else 'sum'
            top_metrics = tab_df.groupby(metric_name_col)[value_col].agg(agg_func).reset_index()
            top_metrics = top_metrics.sort_values(by=value_col, ascending=(agg_func=='min')).head(20)
            
            fig_kw = px.bar(top_metrics, x=value_col, y=metric_name_col, orientation='h', 
                            color=value_col, template="plotly_white",
                            color_continuous_scale='Viridis' if is_ranking else 'Reds')
            
            if is_ranking:
                fig_kw.update_layout(xaxis=dict(autorange="reversed", title="Best Rank"))
                
            st.plotly_chart(fig_kw, use_container_width=True)

    st.divider()

    # --- PERFORMANCE TRENDS WITH AI PROJECTION ---
    st.subheader("Performance Trends & AI Projection")
    show_forecast = st.checkbox("🔮 Show Lightweight Trend Forecast", value=True)
    
    if metric_name_col and value_col and date_col in tab_df.columns:
        locations = sorted(tab_df[loc_col].unique()) if loc_col else [None]
        
        chart_counter = 0 
        for loc in locations:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            unique_metrics = sorted(loc_data[metric_name_col].unique())
            
            # Limit charts to prevent crashing on large datasets
            for met in unique_metrics[:10]: 
                chart_df = loc_data[loc_data[metric_name_col] == met].sort_values('dt')
                if not chart_df.empty:
                    chart_counter += 1
                    with st.container():
                        st.markdown(f"### {met} - {loc if loc else ''}")
                        
                        fig = px.line(chart_df, x='dt', y=value_col, markers=True)
                        
                        if is_ranking:
                            fig.update_layout(yaxis=dict(autorange="reversed", title="Search Rank (1 is Top)"))

                        if show_forecast and len(chart_df) >= 2:
                            forecast_input = chart_df.rename(columns={value_col: 'Value'})
                            forecast = get_prediction(forecast_input)
                            
                            if forecast is not None:
                                fig.add_trace(go.Scatter(
                                    x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
                                    y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
                                    fill='toself', fillcolor='rgba(255,165,0,0.1)',
                                    line=dict(color='rgba(255,255,255,0)'),
                                    name='Confidence', showlegend=False
                                ))
                                fig.add_trace(go.Scatter(
                                    x=forecast['ds'], y=forecast['yhat'],
                                    mode='lines', name='AI Trend',
                                    line=dict(color='orange', dash='dash')
                                ))

                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{chart_counter}")

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
