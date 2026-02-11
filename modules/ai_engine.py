import streamlit as st
from groq import Groq
import google.generativeai as genai
import pandas as pd

# --- API KEYS ---
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    if df.empty:
        return "The dataset is empty. Please check your data source."
        
    try:
        # Identify columns
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'SESSIONS', 'VALUE'])), None)
        date_col = 'dt'

        # Build Context
        summary = ""
        if loc_col and val_col and date_col in df.columns:
            # Create a simplified monthly summary for the AI
            monthly = df.copy()
            monthly['Month'] = monthly[date_col].dt.strftime('%b %Y')
            summary = monthly.groupby([loc_col, 'Month'])[val_col].sum().reset_index().to_string(index=False)
        else:
            summary = df.head(20).to_string()

        system_msg = "You are a Strategic Data Analyst. Compare markets like Germany and KSA. Be concise and highlight trends."
        user_msg = f"Data for {tab_name}:\n{summary}\n\nQuestion: {custom_prompt if custom_prompt else 'Analyze this.'}"

        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash') # Using stable flash model
            return model.generate_content(f"{system_msg}\n{user_msg}").text
        else:
            client = Groq(api_key=GROQ_KEY)
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
            )
            return res.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"
