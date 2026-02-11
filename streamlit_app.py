import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from utils import get_prediction

# Must be the very first Streamlit command
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# --- 1. LOGIN SECURITY ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.subheader("🔒 Digital Strategy Login")
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()  # Prevents code from running until password is correct

# --- 2. INITIALIZE SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_report" not in st.session_state:
    st.session_state.ai_report = ""

# --- 3. DATA LOADING ---
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data Loading Error: {e}")
    st.stop()

sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'

    # --- 4. DATA CLEANING (NUCLEAR OPTION) ---
    if value_col:
        def clean_currency(x):
            if isinstance(x, str):
                clean_str = re.sub(r'[^\d.]', '', x) 
                return clean_str if clean_str else '0'
            return x
        tab_df[value_col] = tab_df[value_col].apply(clean_currency)
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    # ... Rest of your original Sidebar, Leaderboards, and Trend logic ...
