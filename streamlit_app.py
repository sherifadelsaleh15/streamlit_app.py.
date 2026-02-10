import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Added for advanced chart overlays
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction # Ensure you added the function to utils.py

st.set_page_config(layout="wide")

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

    # --- REPORT SECTION ---
    st.subheader("Report")
    if st.button("Generate Comparison Report"):
        report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
        st.write(report)
        st.download_button("Download Report", report, file_name=f"{sel_tab}_comparison.txt")

    st.divider()

    # --- DATA TABLE ---
    st.subheader("Data Table")
    st.dataframe(tab_df, use_container_width=True)
    st.download_button("Download Table CSV", tab_df.to_csv(index=False), file_name=f"{sel_tab}_data.csv")

    st.divider()

    # --- TOP LISTS (UNCHANGED) ---
    # ... [Keep your Top 15 Pages and Top 20 Keywords code here] ...

    st.divider()

    # --- ENHANCED OKR CHART LOGIC WITH PREDICTION ---
    st.subheader("Individual Performance & AI Forecast")
    
    # NEW: Toggle to show/hide forecast globally
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
                        
                        # Create the Base Line Chart
                        fig = px.line(chart_df, x='dt', y='Value', markers=True)
                        
                        # --- START PROPHET INTEGRATION ---
                        if show_forecast and len(chart_df) >= 2:
                            forecast = get_prediction(chart_df)
                            if forecast is not None:
                                # Add the shaded confidence interval
                                fig.add_trace(go.Scatter(
                                    x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
                                    y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
                                    fill='toself',
                                    fillcolor='rgba(255,165,0,0.2)',
                                    line=dict(color='rgba(255,255,255,0)'),
                                    hoverinfo="skip",
                                    showlegend=True,
                                    name="Confidence Interval"
                                ))
                                # Add the predicted trend line
                                fig.add_trace(go.Scatter(
                                    x=forecast['ds'], y=forecast['yhat'],
                                    mode='lines',
                                    name='AI Prediction',
                                    line=dict(color='orange', dash='dash')
                                ))
                        # --- END PROPHET INTEGRATION ---

                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{chart_counter}")
                        st.download_button(f"Download Data for {met}", chart_df.to_csv(index=False), 
                                         file_name=f"{met}_{loc}.csv", key=f"dl_{chart_counter}")
                        st.write("---")
        
        # ... [Handle the 'else' case for num_cols if needed, similar to above] ...

    # --- SIDEBAR CHAT (UNCHANGED) ---
    # ... [Keep your sidebar chat code here] ...
