import streamlit as st
from groq import Groq
import google.generativeai as genai

# Securely pull keys from session or secrets
GROQ_KEY = st.secrets.get("GROQ_API_KEY", "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")
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        # --- DATA SUMMARIZATION FOR AI ---
        # Instead of raw rows, we send a summary to ensure the AI sees the totals
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['VALUE', 'CLICKS', 'SESSIONS', 'USERS'])), None)
        
        if loc_col and val_col:
            # Create a summary of totals per region to prevent the "AI seeing 0" error
            summary_df = df.groupby(loc_col)[val_col].sum().reset_index()
            data_context = f"Total metrics per Region:\n{summary_df.to_string()}\n\nDetailed Sample:\n{df.head(20).to_string()}"
        else:
            data_context = df.head(40).to_string()

        system_msg = (
            "You are a Senior Strategic Analyst. Analyze the data provided. "
            "If a user asks for a specific region (like Portugal or Saudi Arabia), "
            "look at the 'Total metrics' section first. Do not say data is 0 if the summary shows values."
        )

        prompt = custom_prompt if custom_prompt else f"Analyze trends for {tab_name}."

        # --- GEMINI ENGINE (Reports) ---
        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            # Using the specific version supported by your key
            model = genai.GenerativeModel(model_name='models/gemini-3-flash-preview')
            response = model.generate_content(f"{system_msg}\n\nContext:\n{data_context}\n\nTask: {prompt}")
            return response.text

        # --- GROQ ENGINE (Chat) ---
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Data:\n{data_context}\n\nQuestion: {prompt}"}
                ]
            )
            return response.choices[0].message.content

    except Exception as e:
        return f"AI Error: {str(e)}"
