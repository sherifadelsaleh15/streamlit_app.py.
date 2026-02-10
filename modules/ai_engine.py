import streamlit as st
from groq import Groq
import google.generativeai as genai

# Standardize the variable names here
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    """
    Unified AI Engine:
    - Groq for Fast Sidebar Chat
    - Gemini for Deep Executive Summaries
    """
    try:
        # Prepare data context (Last 25 rows for relevance)
        data_summary = df.tail(25).to_string()
        
        if custom_prompt:
            # Mode: Chat (User asking questions)
            system_msg = f"You are a helpful data assistant. Context: {data_summary}"
            user_msg = custom_prompt
        else:
            # Mode: Report (Standard Analysis)
            system_msg = "You are a Senior Strategy Consultant."
            user_msg = f"Analyze these {tab_name} OKRs: {data_summary}. Provide 3 executive bullet points."

        # Engine 1: Groq (using GROQ_API_KEY)
        if engine == "groq":
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content

        # Engine 2: Gemini (using GEMINI_API_KEY)
        elif engine == "gemini":
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Combine system and user message for Gemini
            response = model.generate_content(f"{system_msg}\n\nTask: {user_msg}")
            return response.text

    except Exception as e:
        return f"❌ AI Engine Error: {str(e)}"
