import streamlit as st
from groq import Groq
import google.generativeai as genai

# These are the keys you provided
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    """
    AI Engine using your provided keys.
    - Groq (Llama 3): Fast Chat
    - Gemini (1.5 Flash): Deep Summaries
    """
    try:
        # Standardize data context for the AI
        data_summary = df.tail(25).to_string()
        
        if custom_prompt:
            # Chat Mode (Groq)
            system_msg = f"You are a fast data assistant. Use this data: {data_summary}"
            user_msg = custom_prompt
        else:
            # Report Mode (Gemini)
            system_msg = "You are a Senior Strategy Consultant."
            user_msg = f"Based on this data for {tab_name}: {data_summary}, provide 3 executive takeaways."

        # Engine Logic
        if engine == "groq":
            # Using your Groq Key
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

        elif engine == "gemini":
            # Using your Gemini Key
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{system_msg}\n\n{user_msg}")
            return response.text

    except Exception as e:
        return f"❌ AI Engine Error: {str(e)}"
