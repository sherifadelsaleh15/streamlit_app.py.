import streamlit as st
from groq import Groq
import google.generativeai as genai

# API Keys
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    """
    Unified AI Engine with Fixed Gemini Model Path.
    """
    try:
        # Prepare context
        data_summary = df.tail(20).to_string()
        
        if custom_prompt:
            system_msg = "You are a fast data assistant."
            user_msg = f"Data: {data_summary}\n\nQuestion: {custom_prompt}"
        else:
            system_msg = "You are a Senior Strategy Consultant."
            user_msg = f"Data for {tab_name}: {data_summary}\n\nTask: Provide 3 executive bullet points."

        # Engine 1: Groq
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

        # Engine 2: Gemini
        elif engine == "gemini":
            genai.configure(api_key=GEMINI_API_KEY)
            # Use 'gemini-1.5-flash-latest' for better compatibility
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            # Simple content generation
            response = model.generate_content([system_msg, user_msg])
            return response.text

    except Exception as e:
        return f"❌ AI Engine Error: {str(e)}"
