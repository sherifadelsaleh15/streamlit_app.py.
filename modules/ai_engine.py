import streamlit as st
from groq import Groq
import google.generativeai as genai

# API Keys
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    """
    Unified AI Engine with Fixed Model Strings and Fallback Logic.
    """
    try:
        # Prepare context (Last 20 rows)
        data_summary = df.tail(20).to_string()
        
        system_msg = "You are a Senior Strategy Consultant."
        if custom_prompt:
            user_msg = f"Data: {data_summary}\n\nQuestion: {custom_prompt}"
        else:
            user_msg = f"Data for {tab_name}: {data_summary}\n\nTask: Provide 3 executive bullet points on trends and risks."

        # --- ENGINE: GEMINI ---
        if engine == "gemini":
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Try the standard model name
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(user_msg)
                return response.text
            except Exception as gem_err:
                # If Gemini fails, automatically fallback to Groq so the user gets a report
                st.warning("Gemini model error. Switching to Groq for your report...")
                engine = "groq"

        # --- ENGINE: GROQ ---
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

    except Exception as e:
        return f"❌ AI Engine Error: {str(e)}"
