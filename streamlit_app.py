import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction  # This is your Scikit-Learn logic

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
    date_col = 'dt'

    if value_col:
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # --- FILTERS ---
    if loc_col:
        # Prioritize Germany in sorting
        raw_locs = tab_df[loc_col].dropna().unique()
        all_locs = sorted([str(x) for x in raw_locs], key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- SCIKIT-LEARN POWERED AI REPORT ---
    st.subheader("Strategic AI Report (Predictive)")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing velocity with Scikit-Learn..."):
            sample_forecast = None
            if value_col and len(tab_df) >= 2:
                # Prepare data for Scikit-Learn utility
                predict_df = tab_df.rename(columns={value_col: 'Value'})
                sample_forecast = get_prediction(predict_df)
                
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini", forecast_df=sample_forecast)
            st.markdown(report)

    st.divider()

    # --- PERFORMANCE TRENDS WITH SCIKIT-LEARN FORECAST ---
    st.subheader("Keyword Deep-Dive & Scikit-Learn Projections")
    show_forecast = st.checkbox("🔮 Show Scikit-Learn Trend Forecasts", value=True)
    
    if metric_name_col and value_col and date_col in tab_df.columns:
        # Sort by volume (sum) or rank (min)
        agg_sort = 'min' if is_ranking else 'sum'
        top_20_global = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]
        
        chart_idx = 0
        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"### 📍 Region: {loc if loc else 'Global'}")
            region_keywords = [kw for kw in top_20_global if kw in loc_data[metric_name_col].unique()]

            for kw in region_keywords:
                kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
                chart_idx += 1
                
                with st.expander(f"Monthly Performance: {kw}", expanded=(loc == 'Germany')):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        fig = px.line(kw_data, x='dt', y=value_col, markers=True, height=350, title=f"Trend for {kw}")
                        
                        # --- INTEGRATE SCIKIT-LEARN PREDICTION ---
                        if show_forecast and len(kw_data) >= 2:
                            forecast_input = kw_data.rename(columns={value_col: 'Value'})
                            forecast = get_prediction(forecast_input) # Calls your Scikit-Learn logic
                            
                            if forecast is not None:
                                # Add the Scikit-Learn Confidence Interval
                                fig.add_trace(go.Scatter(
                                    x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
                                    y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
                                    fill='toself', fillcolor='rgba(255,165,0,0.1)',
                                    line=dict(color='rgba(255,255,255,0)'), name='AI Confidence', showlegend=False
                                ))
                                # Add the Scikit-Learn Prediction Line
                                fig.add_trace(go.Scatter(
                                    x=forecast['ds'], y=forecast['yhat'],
                                    mode='lines', name='SK-Learn Projection', 
                                    line=dict(color='orange', dash='dash')
                                ))

                        if is_ranking:
                            fig.update_layout(yaxis=dict(autorange="reversed", title="Rank (1 is Best)"))
                        st.plotly_chart(fig, use_container_width=True, key=f"sk_chart_{loc}_{chart_idx}")
                    
                    with c2:
                        st.write("**Monthly Data**")
                        table_data = kw_data[['dt', value_col]].copy()
                        table_data['dt'] = table_data['dt'].dt.strftime('%b %Y')
                        st.dataframe(table_data, hide_index=True, use_container_width=True, key=f"sk_tbl_{loc}_{chart_idx}")
