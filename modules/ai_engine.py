import streamlit as st
from groq import Groq
import google.generativeai as genai

# --- 2026 API KEYS ---
# Note: Rotating these regularly is recommended for security.
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    """
    Strategic AI Engine (2026 Edition):
    - Uses Gemini 3 Flash (Advanced Reasoning)
    - Uses Llama 3.3 via Groq (Extreme Speed)
    """
    try:
        # 1. Prepare Data Context
        data_summary = df.tail(20).to_string()
        
        system_msg = (
            "You are a Senior Strategic Analyst. "
            "Start every report with a 'Data Health Grade' (A, B, or C) based on performance vs targets."
        )
        
        if custom_prompt:
            user_msg = f"Data Context:\n{data_summary}\n\nUser Question: {custom_prompt}"
        else:
            user_msg = f"Analyze the following {tab_name} data and provide 3 executive takeaways:\n\n{data_summary}"

        # --- ENGINE: GEMINI (Updated for 2026) ---
        if engine == "gemini":
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # 'gemini-3-flash-preview' is the current 2026 standard for high-speed reasoning
                model = genai.GenerativeModel('gemini-3-flash-preview')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except Exception as e:
                # If Gemini 404s or fails, we trigger the Groq fallback
                st.toast(f"Gemini Update Required: {str(e)}. Falling back to Groq...", icon="🔄")
                engine = "groq"

        # --- ENGINE: GROQ (Llama 3.3) ---
        if engine == "groq":
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.25
            )
            return response.choices[0].message.content

    except Exception as e:
        return f"❌ Critical Engine Error: {str(e)}"
