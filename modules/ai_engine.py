import streamlit as st
from groq import Groq
import google.generativeai as genai

# --- API KEY CONFIGURATION ---
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        data_summary = df.head(30).to_string() 
        
        system_msg = (
            "You are a Strategic Data Analyst for 2026 trends. "
            "Analyze the data provided and give clear, professional insights."
        )

        user_msg = (
            f"Question: {custom_prompt}\n\nData Context:\n{data_summary}" 
            if custom_prompt else 
            f"Please summarize the main trends for the {tab_name} dataset:\n{data_summary}"
        )

        # --- GEMINI LOGIC ---
        if engine == "gemini":
            try:
                genai.configure(api_key=GEMINI_KEY)
                
                # Using the explicit model path to bypass versioning conflicts
                # 'models/gemini-1.5-flash' is the most compatible for 2026
                model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
                
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except Exception as e:
                # This block will now help you debug by listing what your API can actually see
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                return (f"Gemini 404 Error. Your API key supports these models: {available_models}. "
                        f"Technical details: {str(e)}")

        # --- GROQ LOGIC ---
        if engine == "groq":
            try:
                client = Groq(api_key=GROQ_KEY)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Groq connection failed: {str(e)}"
        
    except Exception as e:
        return f"AI Engine Error: {str(e)}"

    return "AI Engine not initialized."
