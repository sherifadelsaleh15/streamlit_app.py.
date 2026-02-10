import streamlit as st
from groq import Groq
import google.generativeai as genai

GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        # Strictly limit the AI to the dataframe content
        data_summary = df.to_string()
        
        # This prompt forces the AI to ignore its training data/web knowledge
        system_msg = (
            "You are a local data processor. Use ONLY the provided data. "
            "If the information is not in the data, say 'Not found in data'. "
            "Do not use external web knowledge or search the internet."
        )
        
        user_msg = f"Table Data:\n{data_summary}\n\nTask: Analyze {tab_name} rows only."
        if custom_prompt:
            user_msg = f"Table Data:\n{data_summary}\n\nUser Question: {custom_prompt}"

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
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"
