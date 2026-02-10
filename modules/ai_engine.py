import streamlit as st
from groq import Groq
import google.generativeai as genai

# Safe-check for secrets
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        if engine == "gemini":
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"Analyze this data: {df.head().to_string()}")
            return res.text
        else:
            return "Groq engine is ready."
    except Exception as e:
        return f"AI Error: {str(e)}"
