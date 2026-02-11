import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from groq import Groq

# Zero-indentation imports
from modules.data_loader import load_and_preprocess_data
from modules.ml_models import generate_forecast, get_prediction

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# API KEYS
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# --- HELPER FUNCTIONS ---
def get_ai_insight(df, tab_name):
    try:
        data_summary = df.head(15).to_string()
        genai.configure(api_key=GEMINI_KEY)
        model_options = ['gemini-2.0-flash', 'gemini-3-flash-preview', 'gemini-2.5-flash']
        for m_name in model_options:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"Senior Strategic Analyst. Analyze: {tab_name} data:\n{data_summary}")
                return response.text
            except: continue
        return "AI Error: Model endpoints unavailable."
    except Exception as e: return f"AI Error: {str(e)}"

# 2. Authentication
if "password_correct" not in st.session_state:
    st.subheader("Strategy Login")
    pwd = st.text_input("Enter Key", type="password")
    if st.button("Submit"):
        if pwd == "strategic_2026":
            st.session_state["password_correct"] = True
            st.rerun()
    st.stop()

# 3. Data Loading
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data loading failed: {e}"); st.stop()

# 4. Sidebar Navigation
sel_tab = st.sidebar.selectbox("Dashboard Section", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # --- BROAD COLUMN DETECTION (Fixes loading issues) ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICK' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    
    # Identify labels for GSC vs GA4
    kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    
    # Generic metrics for GA4/Others
    value_col = click_col if click_col else next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VALUE', 'VIEWS', 'SESSIONS'])), None)
    
    date_col = 'dt'
    is_gsc = "GSC" in sel_tab.upper() or "POSITION" in sel_tab.upper()

    # --- SIDEBAR FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")

    # --- CENTERED LEADERBOARDS ---
    L, M, R = st.columns([1, 4, 1])
    with M:
        # 1. GSC / POSITION TRACKING VIEW
        if is_gsc and kw_col and (click_col or pos_col):
            st.subheader(f"Top 20 Keywords: Performance")
            agg_dict = {}
            if click_col: agg_dict[click_col] = 'sum'
            if pos_col: agg_dict[pos_col] = 'mean'
            
            kw_perf = tab_df.groupby(kw_col).agg(agg_dict).reset_index()
            sort_col = click_col if click_col else pos_col
            kw_perf = kw_perf.sort_values(by=sort_col, ascending=(not click_col)).head(20)

            fig_gsc = go.Figure()
            if click_col:
                fig_gsc.add_trace(go.Bar(x=kw_perf[kw_col], y=kw_perf[click_col], name="Clicks", marker_color='#4285F4', yaxis='y1'))
            if pos_col:
                fig_gsc.add_trace(go.Scatter(x=kw_perf[kw_col], y=kw_perf[pos_col], name="Position", line=dict(color='#DB4437', width=3), yaxis='y2'))
            
            fig_gsc.update_layout(template="plotly_white", yaxis=dict(title="Clicks"), 
                                  yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"),
                                  legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_gsc, use_container_width=True)

        # 2. GA4 / TOP PAGES VIEW
        elif (page_col or kw_col) and value_col:
            label = page_col if page_col else kw_col
            st.subheader(f"Top Performance: {label}")
            top_p = tab_df.groupby(label)[value_col].sum().reset_index().sort_values(by=value_col, ascending=True).tail(20)
            fig_p = px.bar(top_p, x=value_col, y=label, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'], text=value_col)
            fig_p.update_traces(textposition='outside')
            st.plotly_chart(fig_p, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."): st.markdown(get_ai_insight(tab_df, sel_tab))

    st.divider()

    # --- TRENDS ---
    st.subheader("Monthly Performance Trends")
    # Determine the trend item based on tab type
    trend_item_col = kw_col if is_gsc else (page_col if page_col else kw_col)
    
    if trend_item_col and value_col and date_col in tab_df.columns:
        # Get top 15 items for trends
        top_items = tab_df.groupby(trend_item_col)[value_col].sum().sort_values(ascending=False).head(15).index.tolist()
        
        # Non-GSC shows Region expanders
        if not is_gsc and loc_col:
            loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany')
            for loc in loc_list:
                loc_data = tab_df[tab_df[loc_col] == loc]
                with st.expander(f"Region: {loc}", expanded=(loc == 'Germany')):
                    for item in [i for i in top_items if i in loc_data[trend_item_col].unique()]:
                        item_trend = loc_data[loc_data[trend_item_col] == item].sort_values('dt')
                        st.line_chart(item_trend.set_index('dt')[value_col])
        
        # GSC shows Keyword expanders
        else:
            for item in top_items:
                with st.expander(f"Keyword Trend: {item}"):
                    item_trend = tab_df[tab_df[trend_item_col] == item].sort_values('dt')
                    fig_tr = px.line(item_trend, x='dt', y=value_col, markers=True)
                    if pos_col and pos_col in item_trend.columns:
                        fig_tr.add_trace(go.Scatter(x=item_trend['dt'], y=item_trend[pos_col], name="Position", yaxis="y2"))
                        fig_tr.update_layout(yaxis2=dict(overlaying="y", side="right", autorange="reversed"))
                    st.plotly_chart(fig_tr, use_container_width=True)

else:
    st.info("No data found. Check if the tab names in your sheet match the dashboard selection.")
