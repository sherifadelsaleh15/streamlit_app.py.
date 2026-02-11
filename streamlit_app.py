import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import google.generativeai as genai
from groq import Groq

# Correctly importing your custom modules based on your folder structure
from modules.data_loader import load_and_preprocess_data
from modules.ml_models import generate_forecast

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# Safe PDF Support
try:
    from fpdf import FPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# API KEYS
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# --- HELPER FUNCTIONS ---

def generate_pdf(report_text, tab_name):
    if not PDF_SUPPORT: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Strategic Report: {tab_name}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    clean_text = report_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        data_summary = df.head(15).to_string()
        system_msg = "Senior Strategic Analyst. Compare performance and provide business implications."
        user_msg = f"Tab: {tab_name}\nQuestion: {custom_prompt if custom_prompt else 'Analyze data'}"

        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            # Standardized model names to bypass 404 errors
            for model_name in ['gemini-1.5-flash', 'gemini-pro']:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(f"{system_msg}\n{user_msg}\nData:\n{data_summary}")
                    return response.text
                except Exception:
                    continue
            return "Gemini service temporarily unavailable."
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": f"{user_msg}\nData:\n{data_summary}"}]
            )
            return
