import streamlit as st
from config import APP_TITLE
from modules.data_loader import load_and_preprocess_data

st.set_page_config(page_title="Test Connection", layout="wide")

st.title("🚀 Module Connection Test")

try:
    df = load_and_preprocess_data()
    if not df.empty:
        st.success("Success! Modules and Data are connected.")
        st.write(df.head())
    else:
        st.warning("Connected to modules, but the Google Sheet returned no data.")
except Exception as e:
    st.error(f"Connection Error: {e}")
