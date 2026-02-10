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
    # --- IMPROVED COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    # Target value (Clicks for GSC, Sessions/Users for GA4)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    # Metric Name (Keyword for GSC)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    # Page Name (For GA4)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'

    if value_col:
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # --- FILTERS ---
    if loc_col:
        raw_locs = tab_df[loc_col].dropna().unique()
        all_locs = sorted([str(x) for x in raw_locs], key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- CHAT WITH DATA ---
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

    # --- DYNAMIC LEADERBOARDS ---
    # Top 20 Keywords logic (GSC)
    if "GSC" in sel_tab.upper() and metric_name_col:
        st.subheader("Top 20 GSC Keywords")
        agg_k = 'min' if is_ranking else 'sum'
        top_k = tab_df.groupby(metric_name_col)[value_col].agg(agg_k).reset_index()
        top_k = top_k.sort_values(by=value_col, ascending=(agg_k=='min')).head(20)
        fig_k = px.bar(top_k, x=value_col, y=metric_name_col, orientation='h', template="plotly_white", color_discrete_sequence=['#4285F4'])
        if is_ranking: fig_k.update_layout(xaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_k, use_container_width=True)

    # Top 20 Pages logic (GA4)
    if ("GA4" in sel_tab.upper() or "PAGE" in sel_tab.upper()) and page_col:
        st.subheader("Top 20 GA4 Pages")
        top_p = tab_df.groupby(page_col)[value_col].sum().reset_index()
        top_p = top_p.sort_values(by=value_col, ascending=False).head(20)
        fig_p = px.bar(top_p, x=value_col, y=page_col, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'])
        st.plotly_chart(fig_p, use_container_width=True)

    st.divider()

    # --- GEMINI REPORT ---
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
        st.download_button("Download AI Report (TXT)", st.session_state.ai_report, f"Report_{sel_tab}.txt")

    st.divider()

    # --- KEYWORD TRENDS ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show Scikit-Learn Forecasts", value=True)
    
    if metric_name_col and value_col and date_col in tab_df.columns:
        agg_sort = 'min' if is_ranking else 'sum'
        top_20_list = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]
        
        c_idx = 0
        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"Region: {loc if loc else 'Global'}")
            region_keywords = [kw for kw in top_20_list if kw in loc_data[metric_name_col].unique()]

            for kw in region_keywords:
                kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
                c_idx += 1
                with st.expander(f"Data for: {kw} in {loc}", expanded=(loc == 'Germany')):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        fig = px.line(kw_data, x='dt', y=value_col, markers=True, height=350, title=f"Trend: {kw} ({loc})")
                        if show_forecast and len(kw_data) >= 2:
                            f_in = kw_data.rename(columns={value_col: 'Value'})
                            forecast = get_prediction(f_in)
                            if forecast is not None:
                                fig.add_trace(go.Scatter(x=pd.concat([forecast['ds'], forecast['ds'][::-1]]), y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]), fill='toself', fillcolor='rgba(255,165,0,0.1)', line=dict(color='rgba(255,255,255,0)'), showlegend=False))
                                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Projection', line=dict(color='orange', dash='dash')))
                        if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed", title="Rank"))
                        st.plotly_chart(fig, use_container_width=True, key=f"ch_{loc}_{c_idx}")
                    with col2:
                        st.write("Monthly Data")
                        table_data = kw_data[['dt', value_col]].copy()
                        table_data['dt'] = table_data['dt'].dt.strftime('%b %Y')
                        st.dataframe(table_data, hide_index=True, key=f"tbl_{loc}_{c_idx}")
                        csv = table_data.to_csv(index=False).encode('utf-8')
                        st.download_button("Download CSV", csv, f"{kw}_{loc}.csv", key=f"dl_{loc}_{c_idx}")
