# config.py
import os
from pathlib import Path

# API Keys
try:
    import streamlit as st
    GROQ_KEY = st.secrets.get("GROQ_API_KEY", "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")
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")
except:
    GROQ_KEY = os.getenv("GROQ_API_KEY", "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")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")

# ✅ YOUR CORRECT SHEET ID (extracted from your shared URL)
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

# ✅ CORRECT TAB NAMES - exactly as they appear in your sheet
TABS = [
    "GA4_Data",
    "Position_Tracking_Standard", 
    "GA4_Top_Pages",
    "SOCIAL_MEDIA",
    "MASTER_FEED"
]

# Set to False to use real Google Sheets
USE_SAMPLE_DATA = False

# App settings
APP_TITLE = "2026 Strategic Dashboard - OKR Data"
PASSWORD = "strategic_2026"
