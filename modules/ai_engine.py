import streamlit as st
from groq import Groq
import google.generativeai as genai

GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        # --- FIX 1: Provide full context including all Columns (Region, Country, etc.) ---
        # We use a sample if the file is huge, but ensure we keep column names
        data_context = df.to_string() if len(df) < 100 else df.sample(100).to_string()
        
        system_msg = (
            "You are a Global Strategic Analyst. "
            "You must identify performance by Region, Country, and Objective. "
            "Start every report with a 'Data Health Grade' (A, B, or C)."
        )
        
        if custom_prompt:
            user_msg = f"Data Content:\n{data_context}\n\nQuestion: {custom_prompt}"
        else:
            user_msg = f"Analyze the {tab_name} sheet. Break down performance by Region/Country and identify the top 3 rows:\n\n{data_context}"

        # --- ENGINE: GEMINI ---
        if engine == "gemini":
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-2.0-flash') # Using latest stable
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text + "\n\n---\n*Report: **Gemini 2.0***"
            except:
                engine = "groq"

        # --- ENGINE: GROQ ---
        if engine == "groq":
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )
            return response.choices[0].message.content + "\n\n---\n*Report: **Groq (Llama 3.3)***"

    except Exception as e:
        return f"❌ Engine Error: {str(e)}"
