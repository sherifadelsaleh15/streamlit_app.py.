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

# Google Sheets configuration - YOUR ACTUAL SHEET ID
SHEET_ID = "1L04CvR2MWLPMFQrv0K58ggG0Qe6lLTHJq3cl8hCOI3U"  # Your sheet ID

# Tab names - match exactly what's in your Google Sheet
TABS = [
    "GSC Performance",  # Change to match your actual tab names
    "GSC Countries",
    "GSC Devices", 
    "GSC Queries",
    "Rank Tracking"
]

# App settings
APP_TITLE = "2026 Strategic Dashboard"
PASSWORD = "strategic_2026"
