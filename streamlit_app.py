import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction

# --- CRITICAL: MUST BE FIRST ---
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# --- LOGIN SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.subheader("🔒 Strategic Login")
    pwd_input = st.text_input("Password", type="password")
    
    # Password is: strategic_2026
    if st.button("Login"):
        if pwd_input == "strategic_2026":
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Incorrect Password")
    return False

if not check_password():
    st.stop()

# --- APP INITIALIZATION ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_report" not in st.session_state:
    st.session_state.ai_report = ""

# --- DATA LOADING ---
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data Source Error: {e}")
    st.stop()

# Tab Selection
tabs = list(df_dict.keys())
if not tabs:
    st.warning("No data files found in the source folder.")
    st.stop()

sel_tab = st.sidebar.selectbox("Select Dashboard", tabs)
raw_df = df_dict[sel_tab].copy()

if not raw_df.empty:
    # 1. Clean Data
    val_col = next((c for c in raw_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    loc_col = next((c for c in raw_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    metric_name_col = next((c for c in raw_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    date_col = 'dt'

    if val_col:
        def clean_val(x):
            if isinstance(x, str):
                s = re.sub(r'[^\d.]', '', x)
                return s if s else '0'
            return x
        raw_df[val_col] = pd.to_numeric(raw_df[val_col].apply(clean_val), errors='coerce').fillna(0)

    # 2. Filters
    view_df = raw_df.copy()
    if loc_col:
        u_locs = sorted(raw_df[loc_col].unique().tolist())
        sel_locs = st.sidebar.multiselect("Filter Regions", u_locs, default=u_locs)
        view_df = view_df[view_df[loc_col].isin(sel_locs)]

    # 3. Sidebar Chat
    st.sidebar.divider()
    st.sidebar.subheader("Strategic Chat")
    user_q = st.sidebar.text_input("Ask about comparisons (e.g. KSA vs Germany)")
    if user_q:
        with st.sidebar:
            with st.spinner("AI analyzing..."):
                ans = get_ai_strategic_insight(raw_df, sel_tab, engine="groq", custom_prompt=user_q)
                st.session_state.chat_history.append({"q": user_q, "a": ans})

    for chat in reversed(st.session_state.chat_history):
        st.sidebar.info(f"Q: {chat['q']}")
        st.sidebar.write(chat['a'])
        st.sidebar.divider()

    # 4. Main UI
    st.title(f"📊 {sel_tab}")
    
    # Strategic Report
    if st.button("Generate Executive Analysis"):
        with st.spinner("Running deep analysis..."):
            st.session_state.ai_report = get_ai_strategic_insight(raw_df, sel_tab, engine="gemini")
    
    if st.session_state.ai_report:
        st.info("### Strategic AI Insights")
        st.markdown(st.session_state.ai_report)

    # Chart
    if metric_name_col and val_col:
        st.subheader("Top Performers")
        top_data = view_df.groupby(metric_name_col)[val_col].sum().sort_values(ascending=False).head(15).reset_index()
        fig = px.bar(top_data, x=val_col, y=metric_name_col, orientation='h', template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
