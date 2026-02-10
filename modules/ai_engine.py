import streamlit as st
from groq import Groq
import google.generativeai as genai

GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        data_summary = df.to_string()
        
        # New Strict Instructions: No listing, only analysis
        system_msg = (
            "You are a Data Analyst. Do not list column names or row counts. "
            "Instead, identify the highest and lowest performing regions. "
            "Compare the latest month vs the previous month. "
            "Identify any anomalies where values dropped to zero. "
            "Focus on 'Value' or metric trends. If data is missing, say so."
        )
        
        user_msg = f"Analyze the following {tab_name} data and provide a strategic summary:\n\n{data_summary}"
        if custom_prompt:
            user_msg = f"Data:\n{data_summary}\n\nQuestion: {custom_prompt}"

        if engine == "gemini":
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except:
                engine = "groq"

        if engine == "groq":
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"
