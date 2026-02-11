import streamlit as st
from groq import Groq
import google.generativeai as genai
import pandas as pd

# --- API KEYS ---
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    if df.empty:
        return "No data available for analysis."
        
    try:
        # 1. Identify Columns
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'SESSIONS', 'VALUE'])), None)
        metric_col = next((c for c in df.columns if any(x in c.upper() for x in ['METRIC', 'TYPE', 'KEYWORD', 'QUERY'])), None)
        date_col = 'dt'

        # 2. Build Comparison Data Context
        data_context = ""
        if loc_col and val_col and date_col in df.columns:
            monthly_df = df.copy()
            monthly_df['Month'] = monthly_df[date_col].dt.strftime('%b %Y')
            
            # Pivot for Comparison Matrix
            try:
                comparison_matrix = monthly_df.groupby([loc_col, 'Month', metric_col if metric_col else loc_col])[val_col].sum().unstack(level=0).fillna(0)
                matrix_str = comparison_matrix.to_string()
            except:
                matrix_str = "Comparison matrix currently unavailable for this dataset structure."
            
            group_total = [loc_col]
            if metric_col: group_total.append(metric_col)
            totals_str = df.groupby(group_total)[val_col].sum().reset_index().to_string(index=False)

            data_context = f"MATRIX:\n{matrix_str}\n\nTOTALS:\n{totals_str}"
        else:
            data_context = df.head(30).to_string()

        # 3. System Instructions
        system_msg = "You are a Senior Strategic Analyst. Compare regions, identify leads/lags, and explain the 'why' behind the numbers."
        user_msg = f"Tab: {tab_name}\nPrompt: {custom_prompt if custom_prompt else 'Analyze this data.'}\n\nData Context:\n{data_context}"

        # --- ENGINES ---
        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel(model_name='models/gemini-3-flash-preview')
            response = model.generate_content(f"{system_msg}\n\n{user_msg}")
            return response.text
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
            )
            return response.choices[0].message.content

    except Exception as e:
        return f"AI Logic Error: {str(e)}"
