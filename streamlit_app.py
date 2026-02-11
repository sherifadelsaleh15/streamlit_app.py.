import streamlit as st
import pandas as pd
import plotly.express as px
import re
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight

# 1. MUST BE FIRST
st.set_page_config(layout="wide", page_title="2026 Strategy")

# 2. Simplified Login
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Login")
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Access Dashboard"):
        if pwd == "strategic_2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Wrong password")
    st.stop()

# 3. App Content
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Error loading CSVs: {e}")
    st.stop()

# Sidebar
sel_tab = st.sidebar.selectbox("Dashboard Section", list(df_dict.keys()))
df = df_dict[sel_tab].copy()

# Data Cleaning
val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'VALUE', 'POSITION'])), None)
loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)

if val_col:
    df[val_col] = pd.to_numeric(df[val_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

# Layout
st.title(f"🚀 {sel_tab} Analysis")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Performance Chart")
    if loc_col and val_col:
        fig_df = df.groupby(loc_col)[val_col].sum().reset_index()
        fig = px.pie(fig_df, values=val_col, names=loc_col, hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Strategic Chat")
    user_q = st.text_input("Compare countries or ask a question:", placeholder="How does KSA compare to Germany?")
    if user_q:
        with st.spinner("Thinking..."):
            answer = get_ai_strategic_insight(df, sel_tab, engine="groq", custom_prompt=user_q)
            st.write(answer)

st.divider()
if st.button("Generate Full AI Executive Report"):
    with st.spinner("Analyzing trends..."):
        report = get_ai_strategic_insight(df, sel_tab, engine="gemini")
        st.markdown(report)
