import streamlit as st
from groq import Groq
import google.generativeai as genai

# --- SECURE API HANDLING ---
# This prevents the app from crashing if secrets aren't set yet
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        data_summary = df.head(50).to_string() # Limit data to prevent token errors
        
        system_msg = (
            "You are a Strategic Data Analyst. "
            "Analyze the provided data trends. "
            "Identify key growth areas and risks."
        )

        if custom_prompt:
            user_msg = f"Data:\n{data_summary}\n\nQuestion: {custom_prompt}"
        else:
            user_msg = f"Analyze the {tab_name} dataset for trends:\n{data_summary}"

        # --- GEMINI ---
        if engine == "gemini" and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except Exception as e:
                return f"Gemini Error: {e}. Switching to Groq..."

        # --- GROQ ---
        if GROQ_API_KEY:
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )
            return response.choices[0].message.content
        
        return "Please set your API keys in .streamlit/secrets.toml"

    except Exception as e:
        return f"AI Engine Error: {str(e)}"
