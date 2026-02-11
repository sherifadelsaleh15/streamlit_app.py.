# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_engine
from config import APP_TITLE, PASSWORD

# Page config
st.set_page_config(layout="wide", page_title=APP_TITLE)

# Initialize AI Engine
ai_engine = get_ai_engine()

# Password protection
def check_password():
    if "password_correct" not in st.session_state:
        st.subheader("Digital Strategy Login")
        pwd = st.text_input("Enter Password", type="password")
        if st.button("Submit"):
            if pwd == PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Access Denied")
        return False
    return True

if not check_password():
    st.stop()

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_report" not in st.session_state:
    st.session_state.ai_report = ""

# Load data using YOUR working loader
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Failed to load data: {str(e)}")
    st.stop()

# Sidebar navigation
sel_tab = st.sidebar.selectbox("Select Dashboard", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # Show Gemini status in sidebar
    st.sidebar.divider()
    st.sidebar.subheader("🤖 AI Status")
    
    if ai_engine.is_gemini_available():
        st.sidebar.success("✅ Gemini: Ready")
    else:
        st.sidebar.error("❌ Gemini: Unavailable")
        if ai_engine.get_gemini_error():
            st.sidebar.caption(f"Error: {ai_engine.get_gemini_error()[:100]}...")
    
    # Main content
    st.title(f"Strategic Dashboard: {sel_tab}")
    
    # Show data info
    with st.expander("📊 Data Overview"):
        st.write(f"**Rows:** {len(tab_df)}")
        st.write(f"**Columns:** {', '.join(tab_df.columns)}")
        if 'dt' in tab_df.columns:
            st.write(f"**Date Range:** {tab_df['dt'].min()} to {tab_df['dt'].max()}")
    
    # Strategic AI Report
    st.divider()
    st.subheader("🎯 Strategic AI Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Analyze with Groq", use_container_width=True):
            with st.spinner("Groq analyzing..."):
                st.session_state.ai_report = ai_engine.get_strategic_insight(
                    tab_df, sel_tab, use_gemini=False
                )
                st.rerun()
    
    with col2:
        if ai_engine.is_gemini_available():
            if st.button("🧠 Analyze with Gemini", use_container_width=True):
                with st.spinner("Gemini analyzing..."):
                    st.session_state.ai_report = ai_engine.get_strategic_insight(
                        tab_df, sel_tab, use_gemini=True
                    )
                    st.rerun()
        else:
            st.button("🧠 Gemini Unavailable", disabled=True, use_container_width=True)
    
    if st.session_state.ai_report:
        st.markdown("---")
        st.markdown(st.session_state.ai_report)
    
    # Sidebar Chat
    st.sidebar.divider()
    st.sidebar.subheader("💬 Data Chat")
    user_q = st.sidebar.text_input("Ask about the data", key="chat_input")
    
    if user_q and user_q != st.session_state.get("last_chat", ""):
        with st.sidebar:
            with st.spinner("Thinking..."):
                ans = ai_engine.chat(tab_df, sel_tab, user_q)
                st.session_state.chat_history.append({"q": user_q, "a": ans})
                st.session_state.last_chat = user_q
    
    for chat in reversed(st.session_state.chat_history[-5:]):
        st.sidebar.markdown(f"**You:** {chat['q']}")
        st.sidebar.info(chat['a'])
        st.sidebar.markdown("---")
