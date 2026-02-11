import streamlit as st
import pandas as pd
import os
import sys

# Ensure Python looks in the current directory for the tabs folder
sys.path.append(os.path.dirname(__file__))

from modules.data_loader import load_and_preprocess_data

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

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
    # ROUTING TO SEPARATE FILES
    if "GSC" in sel_tab.upper():
        from tabs.gsc_tab import render_gsc
        render_gsc(tab_df, sel_tab)
    else:
        from tabs.ga4_tab import render_ga4
        render_ga4(tab_df, sel_tab)
