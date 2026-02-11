import streamlit as st
import pandas as pd
from modules.data_loader import load_and_preprocess_data

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# Global Keys
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"
GROQ_KEY = "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"

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

# 5. Routing to Specialized Files
if not tab_df.empty:
    if "GSC" in sel_tab.upper() or "POSITION" in sel_tab.upper():
        from tabs.gsc_tab import render_gsc_tab
        render_gsc_tab(tab_df, sel_tab, GEMINI_KEY)
    else:
        from tabs.performance_tab import render_performance_tab
        render_performance_tab(tab_df, sel_tab, GEMINI_KEY)
