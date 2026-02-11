import streamlit as st
from groq import Groq
import google.generativeai as genai

# --- SECURE API HANDLING ---
# We retrieve the key by its NAME in the secrets.toml file.
# Do NOT paste the actual gsk_ or AIza... strings here.
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        # Pre-processing data context
        data_summary = df.head(30).to_string() 
        
        system_msg = (
            "You are a Strategic Data Analyst. "
            "Analyze the following data trends carefully. "
            "Identify growth opportunities and potential risks."
        )

        user_msg = (
            f"Question: {custom_prompt}\n\nData Context:\n{data_summary}" 
            if custom_prompt else 
            f"Summarize trends for {tab_name}:\n{data_summary}"
        )

        # --- GEMINI LOGIC ---
        if engine == "gemini" and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except Exception as e:
                return f"Gemini Error: {str(e)}"

        # --- GROQ LOGIC ---
        if GROQ_API_KEY:
            try:
                client = Groq(api_key=GROQ_API_KEY)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Groq Error: {str(e)}"
        
        return "Missing API configuration. Please check Streamlit Secrets."

    except Exception as e:
        return f"AI Engine Exception: {str(e)}"
