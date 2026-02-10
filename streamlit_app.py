import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction  # Your new Scikit-Learn logic

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
        with st.spinner("AI is analyzing trends..."):
            # We pass a sample forecast to the AI to make the report "Forward Looking"
            sample_forecast = None
            if 'Value' in tab_df.columns and len(tab_df) > 2:
                sample_forecast = get_prediction(tab_df.head(20))
                
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini", forecast_df=sample_forecast)
            st.markdown(report)

    st.divider()

    # --- DATA TABLE ---
    st.subheader("Data Explorer")
    st.dataframe(tab_df, use_container_width=True)
    
    st.divider()

    # --- TOP LISTS (BAR CHARTS) ---
    col1, col2 = st.columns(2)

    # 1. GA4 TOP PAGES
    if "TOP_PAGES" in sel_tab.upper() or "GA4" in sel_tab.upper():
        with col1:
            st.subheader("Top 15 Pages Ranking")
            page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
            num_cols = tab_df.select_dtypes('number').columns
            if page_col and len(num_cols) > 0:
                top_15_df = tab_df.groupby(page_col)[num_cols[0]].sum().sort_values(ascending=False).head(15).reset_index()
                fig_top = px.bar(top_15_df, x=num_cols[0], y=page_col, orientation='h', color=num_cols[0], template="plotly_white")
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)

    # 2. GSC KEYWORDS
    if "GSC" in sel_tab.upper() or "KEYWORD" in sel_tab.upper():
        with col2:
            st.subheader("Top 20 Keywords Ranking")
            kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
            click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
            if kw_col and click_col:
                top_20_df = tab_df.groupby(kw_col)[click_col].sum().sort_values(ascending=False).head(20).reset_index()
                fig_kw = px.bar(top_20_df, x=click_col, y=kw_col, orientation='h', color=click_col, template="plotly_white")
                fig_kw.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_kw, use_container_width=True)

    st.divider()

    # --- PERFORMANCE TRENDS WITH LIGHTWEIGHT FORECAST ---
    st.subheader("Performance Trends & AI Projection")
    show_forecast = st.checkbox("🔮 Show Lightweight Trend Forecast", value=True)
    
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
                        
                        # Create actual line chart
                        fig = px.line(chart_df, x='dt', y='Value', markers=True)
                        
                        # Add Forecast if enabled
                        if show_forecast and len(chart_df) >= 2:
                            forecast = get_prediction(chart_df)
                            if forecast is not None:
                                # Add Shaded Area (Confidence)
                                fig.add_trace(go.Scatter(
                                    x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
                                    y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
                                    fill='toself',
                                    fillcolor='rgba(255,165,0,0.1)',
                                    line=dict(color='rgba(255,255,255,0)'),
                                    name='Confidence', showlegend=False
                                ))
                                # Add Prediction Line
                                fig.add_trace(go.Scatter(
                                    x=forecast['ds'], y=forecast['yhat'],
                                    mode='lines', name='AI Trend',
                                    line=dict(color='orange', dash='dash')
                                ))

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
# --- PERFORMANCE TRENDS WITH INVERTED Y-AXIS FOR RANKINGS ---
# ... (inside your loc/metric loops) ...

# 1. Create the base line chart
fig = px.line(chart_df, x='dt', y='Value', markers=True)

# 2. Check if this is the Position Tracking tab
if "POSITION_TRACKING" in sel_tab.upper():
    # Invert Y-axis so Position 1 is at the top
    fig.update_layout(yaxis=dict(autorange="reversed", title="Search Position (Lower is Better)"))
    # Ensure the AI Trend line also respects the inverted axis
    line_color = 'green' # Green for SEO improvement
else:
    line_color = 'orange'

# ... (rest of your go.Scatter forecast logic) ...
