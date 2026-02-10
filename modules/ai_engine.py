import streamlit as st
from groq import Groq
import google.generativeai as genai

# Securely fetch APIs from Streamlit Secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    """
    Generates insights using Gemini or Groq, now securely pulling API keys.
    """
    try:
        data_summary = df.to_string()
        
        # Build Forecast Context if data is available
        forecast_context = ""
        if forecast_df is not None:
            # We take the last 4 rows of the forecast to give AI the 'future' view
            f_summary = forecast_df[['ds', 'yhat']].tail(4).to_string()
            forecast_context = f"\n\nAI PREDICTION DATA:\n{f_summary}"

        system_msg = (
            "You are a Strategic Data Analyst. Use the data and predictions provided. "
            "Compare historical months and evaluate if the AI prediction shows growth or risk. "
            "Identify critical gaps where values are 0 and suggest one strategic action."
        )
        
        # ... [Rest of your logic for user_msg, Gemini, and Groq execution] ...
