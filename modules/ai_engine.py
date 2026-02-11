import streamlit as st
from groq import Groq
import google.generativeai as genai

# API Keys
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        # --- FIX: AGGREGATE SUMMARY FOR AI ---
        # This ensures the AI sees the totals for ALL selected regions, not just the first rows.
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'SESSIONS', 'VALUE'])), None)
        
        if loc_col and val_col:
            summary_stats = df.groupby(loc_col)[val_col].sum().reset_index().to_string()
            data_context = f"Total metrics per Region/Country:\n{summary_stats}\n\nDetailed rows (Sample):\n{df.head(20).to_string()}"
        else:
            data_context = df.head(50).to_string()

        system_msg = "You are a Strategic Data Analyst. Use the summarized data provided to answer precisely."
        user_msg = f"Data Context:\n{data_context}\n\nQuestion: {custom_prompt if custom_prompt else f'Analyze {tab_name}'}"

        # --- GEMINI ---
        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel(model_name='models/gemini-3-flash-preview')
            response = model.generate_content(f"{system_msg}\n\n{user_msg}")
            return response.text

        # --- GROQ ---
        else:
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
        return f"AI Engine Error: {str(e)}"
