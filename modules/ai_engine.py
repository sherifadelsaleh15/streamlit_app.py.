import streamlit as st
from groq import Groq
import google.generativeai as genai

# --- SECURE API HANDLING ---
# Pulling the variable names from secrets.toml
GROQ_API_KEY = st.secrets.get("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, "")
GEMINI_API_KEY = st.secrets.get("AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0", "")

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        # Limit data context to prevent token overflow
        data_summary = df.head(40).to_string() 
        
        system_msg = (
            "You are a Strategic Data Analyst. "
            "Analyze the provided data trends. "
            "Identify key growth areas and risks. "
            "Keep the response professional and concise."
        )

        if custom_prompt:
            user_msg = f"Data Context:\n{data_summary}\n\nQuestion: {custom_prompt}"
        else:
            user_msg = f"Analyze the {tab_name} dataset for trends:\n{data_summary}"

        # --- GEMINI ENGINE ---
        if engine == "gemini" and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except Exception as e:
                return f"Gemini Error: {str(e)}. Attempting fallback..."

        # --- GROQ ENGINE (Chat with Data) ---
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
        
        return "API keys not found. Please check your secrets.toml"

    except Exception as e:
        return f"AI Engine Error: {str(e)}"
