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
            "You are a Strategic Data Analyst. "
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
                
                # UPDATED TO GEMINI 3 FLASH PREVIEW (Your key's supported model)
                model = genai.GenerativeModel(model_name='models/gemini-3-flash-preview')
                
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except Exception as e:
                return f"Gemini Error with Gemini 3: {str(e)}"

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
