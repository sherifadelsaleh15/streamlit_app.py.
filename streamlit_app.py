# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_engine
from modules.ui_components import render_sidebar_filters, render_pdf_download
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

# Load data
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Failed to load data: {str(e)}")
    st.stop()

# Sidebar navigation
sel_tab = st.sidebar.selectbox("Select Dashboard", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # Render sidebar filters
    tab_df = render_sidebar_filters(tab_df, sel_tab)
    
    # Main content
    st.title(f"Strategic Dashboard: {sel_tab}")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        if 'clicks' in tab_df.columns.str.lower().values:
            st.metric("Total Clicks", f"{tab_df['clicks'].sum():,.0f}")
    with col2:
        if 'impressions' in tab_df.columns.str.lower().values:
            st.metric("Total Impressions", f"{tab_df['impressions'].sum():,.0f}")
    with col3:
        if 'ctr' in tab_df.columns.str.lower().values:
            avg_ctr = tab_df['ctr'].mean()
            st.metric("Avg CTR", f"{avg_ctr:.2%}")
    
    # Gemini Status
    st.sidebar.divider()
    st.sidebar.subheader("🤖 AI Status")
    
    if ai_engine.is_gemini_available():
        st.sidebar.success("✅ Gemini: Ready")
    else:
        st.sidebar.error("❌ Gemini: Unavailable")
        with st.sidebar.expander("Fix Gemini"):
            st.markdown("""
            1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. Create/enable API key
            3. Enable Generative Language API
            4. Update key in `.streamlit/secrets.toml`:
            ```toml
            GEMINI_API_KEY = "your-key-here"
            GROQ_API_KEY = "your-key-here"
            ```
            """)
    
    # Strategic AI Report
    st.divider()
    st.subheader("🎯 Strategic AI Analysis")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        # Groq is always available
        if st.button("📊 Analyze with Groq", use_container_width=True):
            with st.spinner("Groq analyzing..."):
                st.session_state.ai_report = ai_engine.get_strategic_insight(
                    tab_df, sel_tab, use_gemini=False
                )
                st.rerun()
    
    with col2:
        # Gemini only if available
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
        
        # PDF download
        render_pdf_download(st.session_state.ai_report, sel_tab)
    
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
    
    for chat in reversed(st.session_state.chat_history[-5:]):  # Last 5 messages
        st.sidebar.markdown(f"**You:** {chat['q']}")
        st.sidebar.info(chat['a'])
        st.sidebar.markdown("---")
    
    # Export
    st.sidebar.divider()
    st.sidebar.subheader("📥 Export")
    
    # Excel export
    try:
        import xlsxwriter
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            tab_df.to_excel(writer, index=False, sheet_name='Data')
        st.sidebar.download_button(
            "📊 Export to Excel",
            data=output.getvalue(),
            file_name=f"{sel_tab}_data.xlsx"
        )
    except ImportError:
        st.sidebar.warning("xlsxwriter not installed")

else:
    st.warning(f"No data available for {sel_tab}")
