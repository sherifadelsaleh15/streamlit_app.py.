# config.py
import os
from pathlib import Path

# API Keys - Use Streamlit secrets in production
try:
    import streamlit as st
    # Try to get from secrets, fallback to hardcoded for development
    GROQ_KEY = st.secrets.get("GROQ_API_KEY", "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")
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")
except:
    # Fallback for local development
    GROQ_KEY = os.getenv("GROQ_API_KEY", "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")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")

# Google Sheets configuration
SHEET_ID = "1L04CvR2MWLPMFQrv0K58ggG0Qe6lLTHJq3cl8hCOI3U"  # Your Google Sheet ID
TABS = {
    "GSC Performance": 0,  # First sheet
    "GSC Countries": 1426359845,  # Sheet ID for countries
    "GSC Devices": 1190098117,  # Sheet ID for devices
    "GSC Queries": 0,  # Adjust based on your sheet
    "Rank Tracking": 0,  # Adjust based on your sheet
}

# Data paths
DATA_PATH = Path("data")
CACHE_PATH = Path("cache")

# Create directories if they don't exist
DATA_PATH.mkdir(exist_ok=True)
CACHE_PATH.mkdir(exist_ok=True)

# App settings
APP_TITLE = "2026 Strategic Dashboard"
PASSWORD = "strategic_2026"

# Cache settings
CACHE_TTL = 3600  # 1 hour in seconds
