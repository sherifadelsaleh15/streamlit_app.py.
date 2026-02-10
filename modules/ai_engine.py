import streamlit as st
from groq import Groq
import google.generativeai as genai

GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        # Include Region/Country in the context so AI can see them
        data_summary = df.to_string()
        
        # Neutral Persona
        system_msg = "Start with a 'Data Health Grade' (A, B, or C). Analyze all rows including Region/Country."
        
        user_msg = f"Analyze {tab_name} data:\n{data_summary}" if not custom_prompt else custom_prompt

        if engine == "gemini":
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Stable 2026 model string
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except:
                engine = "groq" # Fallback

        if engine == "groq":
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"
