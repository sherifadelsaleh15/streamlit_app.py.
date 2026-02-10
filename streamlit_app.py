import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction 

st.set_page_config(layout="wide", page_title="Strategic OKR Dashboard")

# 1. Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 2. Load Data
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

    # --- REPORT SECTION (NOW FORECAST-AWARE) ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("AI is analyzing historical trends and future projections..."):
            # We provide the AI with a sample forecast from the first metric to give it 'future' context
            sample_forecast = None
            if 'Value' in tab_df.columns and not tab_df.empty:
                sample_forecast = get_prediction(tab_df.head(20)) # Get a trend overview
            
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini", forecast_df=sample_forecast)
            st.markdown(report)
            st.download_button("Download Report", report, file_name=f"{sel_tab}_ai_analysis.txt")

    st.divider()

    # --- DATA TABLE ---
    st.subheader("Data Explorer")
    st.dataframe(tab_df, use_container_width=True)
    
    st.divider()

    # --- ENHANCED OKR CHART LOGIC ---
    st.subheader("Individual Performance & AI Forecast")
    show_forecast = st.checkbox("🔮 Enable AI Predictive Forecasting", value=True)
    
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
                        fig = px.line(chart_df, x='dt', y='Value', markers=True, line_shape="spline")
                        
                        # --- PROPHET INTEGRATION ---
                        if show_forecast and len(chart_df) >= 2:
                            forecast = get_prediction(chart_df)
                            if forecast is not None:
                                # Shaded Confidence Interval
                                fig.add_trace(go.Scatter(
                                    x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
                                    y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
                                    fill='toself',
                                    fillcolor='rgba(255,165,0,0.15)',
                                    line=dict(color='rgba(255,255,255,0)'),
                                    name="Confidence Interval",
                                    showlegend=False
                                ))
                                # Prediction Line
                                fig.add_trace(go.Scatter(
                                    x=forecast['ds'], y=forecast['yhat'],
                                    mode='lines', name='AI Prediction',
                                    line=dict(color='orange', dash='dot', width=3)
                                ))
                        
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{chart_counter}")
                        st.write("---")

    # --- SIDEBAR CHAT ---
    st.sidebar.divider()
    user_q = st.sidebar.text_input("Ask AI about this data:", key="user_input")
    if user_q:
        with st.sidebar:
            with st.spinner("Consulting AI..."):
                ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
                st.session_state.chat_history.append((user_q, ans))
    
    if st.session_state.chat_history:
        for q, a in st.session_state.chat_history[::-1]:
            st.sidebar.info(f"**You:** {q}")
            st.sidebar.write(f"**AI:** {a}")
            st.sidebar.divider()
