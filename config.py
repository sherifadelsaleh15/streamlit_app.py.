# config.py
import os
from pathlib import Path

# API Keys - Use Streamlit secrets in production
try:
    import streamlit as st
    GROQ_KEY = st.secrets.get("GROQ_API_KEY", "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")
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")
except:
    # Fallback for local development
    GROQ_KEY = os.getenv("GROQ_API_KEY", "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")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")

# Data paths
DATA_PATH = Path("data")
CACHE_PATH = Path("cache")

# Create directories if they don't exist
DATA_PATH.mkdir(exist_ok=True)
CACHE_PATH.mkdir(exist_ok=True)

# App settings
APP_TITLE = "2026 Strategic Dashboard"
PASSWORD = "strategic_2026"
