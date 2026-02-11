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

# --- AI HELPER ---
def get_ai_insight(df, tab_name):
    try:
        data_summary = df.head(15).to_string()
        genai.configure(api_key=GEMINI_KEY)
        model_options = ['gemini-2.0-flash', 'gemini-3-flash-preview']
        for m_name in model_options:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"Analyze: {tab_name} data:\n{data_summary}")
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
    # --- SPECIFIC COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'LOCATION'])), None)
    
    # Identify Clicks vs Position
    click_col = next((c for c in tab_df.columns if 'CLICK' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    
    # Logic: If GSC, prioritize Clicks for the main chart
    primary_val = click_col if click_col else pos_col
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    date_col = 'dt'

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
        if metric_name_col and primary_val:
            is_pos = (primary_val == pos_col)
            label = "Average Position" if is_pos else "Total Clicks"
            st.subheader(f"Top 20 Keywords by {label}")

            # Aggregation: Mean for Position, Sum for Clicks
            agg_func = 'mean' if is_pos else 'sum'
            top_k = tab_df.groupby(metric_name_col)[primary_val].agg(agg_func).reset_index()
            
            # Sorting: Position 1 is "best" (ascending), Clicks 1000 is "best" (descending)
            top_k = top_k.sort_values(by=primary_val, ascending=not is_pos).head(20)
            
            # Plotly renders bottom-up, so we reverse for display
            fig_k = px.bar(top_k.iloc[::-1], x=primary_val, y=metric_name_col, orientation='h', 
                           template="plotly_white", color_discrete_sequence=['#4285F4'], text=primary_val)
            
            if is_pos:
                fig_k.update_layout(xaxis=dict(autorange="reversed", title="Average Position (Lower is Better)"))
            
            fig_k.update_traces(texttemplate='%{text:.1f}' if is_pos else '%{text}', textposition='outside')
            st.plotly_chart(fig_k, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."): st.write(get_ai_insight(tab_df, sel_tab))

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader("Monthly Performance Trends")
    if metric_name_col and primary_val and date_col in tab_df.columns:
        # Get top 10 for the trend views
        top_items = tab_df.groupby(metric_name_col)[primary_val].agg('mean' if primary_val == pos_col else 'sum').sort_values(ascending=(primary_val == pos_col)).head(10).index.tolist()
        
        for item in top_items:
            item_data = tab_df[tab_df[metric_name_col] == item].sort_values('dt')
            with st.expander(f"Trend for: {item}"):
                fig_t = px.line(item_data, x='dt', y=primary_val, markers=True)
                if primary_val == pos_col:
                    fig_t.update_layout(yaxis=dict(autorange="reversed", title="Position"))
                st.plotly_chart(fig_t, use_container_width=True, key=f"tr_{item}")

else:
    st.info("No data found. Please check your Google Sheet tab names.")
