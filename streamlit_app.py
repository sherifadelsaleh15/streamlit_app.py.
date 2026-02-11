import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from groq import Groq
import time

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
    """
    Fixed Model Targeting:
    Prioritizes Gemini 1.5 Flash (the model with available tokens in your dashboard).
    Includes automatic fallback to Grok if Gemini hits a quota limit.
    """
    # TPM Fix: Send only the most critical data
    cols = [c for c in df.columns if c in ['dt', 'Location', 'Value', 'Users', 'Metric']]
    data_summary = df[cols].head(10).to_string(index=False)
    
    prompt = f"Senior Strategic Analyst. Analyze this {tab_name} data and provide 3 executive bullet points:\n{data_summary}"

    # Attempt 1: Gemini 1.5 Flash (Targeting your available 'Gemini 3 Flash' quota)
    try:
        genai.configure(api_key=GEMINI_KEY)
        # Using 1.5-flash as it matches the standard 'Flash' tier quotas in your screenshot
        model = genai.GenerativeModel('gemini-1.5-flash') 
        response = model.generate_content(prompt)
        return response.text
    except Exception as gemini_err:
        # Attempt 2: Fallback to Grok/Llama if Gemini is exhausted
        try:
            client = Groq(api_key=GROQ_KEY)
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            return f"**[Strategic Fallback Report]**\n\n{res.choices[0].message.content}"
        except:
            return f"AI Error: Both Gemini and Grok are unavailable. (Last Error: {str(gemini_err)})"

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
    # --- FAILSAFE COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), 'Location')
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['USERS', 'SESSIONS', 'VALUE', 'CLICKS', 'VIEWS'])), 'Value')
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), 'Metric')
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")

    # Leaderboard Chart
    L, M, R = st.columns([1, 4, 1])
    with M:
        display_col = page_col if (page_col and "PAGE" in sel_tab.upper()) else metric_name_col
        if display_col in tab_df.columns and value_col in tab_df.columns:
            st.subheader(f"Top 20 {display_col}")
            top_df = tab_df.groupby(display_col)[value_col].sum().nlargest(20).reset_index()
            fig_main = px.bar(top_df, x=value_col, y=display_col, orientation='h', template="plotly_white")
            st.plotly_chart(fig_main, use_container_width=True, key="main_chart")

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing data..."):
            st.session_state.ai_report = get_ai_insight(tab_df, sel_tab)
    if "ai_report" in st.session_state:
        st.info(st.session_state.ai_report)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader("Monthly Performance Trends")
    if date_col in tab_df.columns:
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany')
        for i, loc in enumerate(loc_list):
            loc_data = tab_df[tab_df[loc_col] == loc]
            st.markdown(f"#### Region: {loc}")
            
            # UNIQUE KEY FIX: prevents DuplicateElementId error
            fig = px.line(loc_data.groupby('dt')[value_col].sum().reset_index(), x='dt', y=value_col, markers=True)
            st.plotly_chart(fig, use_container_width=True, key=f"trend_{loc}_{i}")

    # --- SIDEBAR CHAT (GROK) ---
    st.sidebar.divider()
    st.sidebar.subheader("💬 Chat with Data")
    if "msgs" not in st.session_state: st.session_state.msgs = []
    
    for m in st.session_state.msgs:
        st.sidebar.chat_message(m["role"]).write(m["content"])

    if user_in := st.sidebar.chat_input("Ask about numbers..."):
        st.session_state.msgs.append({"role": "user", "content": user_in})
        
        # Exact context for "Saudi Arabia" style questions
        context = tab_df.groupby([loc_col, tab_df[date_col].dt.strftime('%Y-%m')])[value_col].sum().reset_index().to_string(index=False)
        
        client = Groq(api_key=GROQ_KEY)
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"Brief Data Assistant. Use this table: {context}. Give exact numbers."},
                *st.session_state.msgs
            ]
        )
        st.session_state.msgs.append({"role": "assistant", "content": res.choices[0].message.content})
        st.rerun()
