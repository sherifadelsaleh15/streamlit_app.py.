# config.py
import os
from pathlib import Path

# API Keys - Use Streamlit secrets in production
try:
    import streamlit as st
    GROQ_KEY = st.secrets.get("GROQ_API_KEY", "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")
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")
except:
    GROQ_KEY = os.getenv("GROQ_API_KEY", "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")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")

# Google Sheets configuration - Comment out if using sample data
# SHEET_ID = "1L04CvR2MWLPMFQrv0K58ggG0Qe6lLTHJq3cl8hCOI3U"

# Set to True to use sample data instead of Google Sheets
USE_SAMPLE_DATA = True

# Tab names - these will be used for both sample data and sheet names
TABS = [
    "GSC Performance",
    "GSC Countries", 
    "GSC Devices",
    "GSC Queries",
    "Rank Tracking"
]

# App settings
APP_TITLE = "2026 Strategic Dashboard"
PASSWORD = "strategic_2026"
