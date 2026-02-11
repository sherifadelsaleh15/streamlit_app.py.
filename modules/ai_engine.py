import streamlit as st
from groq import Groq
import google.generativeai as genai

# --- API KEYS ---
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        # 1. Identify Columns
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'SESSIONS', 'VALUE'])), None)
        metric_col = next((c for c in df.columns if any(x in c.upper() for x in ['METRIC', 'TYPE', 'KEYWORD', 'QUERY'])), None)
        date_col = 'dt'

        # 2. Build Advanced Data Context
        if loc_col and val_col:
            # TOTALS SUMMARY
            group_total = [loc_col]
            if metric_col: group_total.append(metric_col)
            totals_str = df.groupby(group_total)[val_col].sum().reset_index().to_string(index=False)

            # MONTHLY BREAKDOWN SUMMARY (This makes it "Smarter")
            # We convert dates to string so the AI can read "Jan 2026" easily
            monthly_df = df.copy()
            monthly_df['Month'] = monthly_df[date_col].dt.strftime('%b %Y')
            
            group_month = [loc_col, 'Month']
            if metric_col: group_month.insert(1, metric_col)
            
            monthly_str = monthly_df.groupby(group_month)[val_col].sum().reset_index().to_string(index=False)

            data_context = f"""
            SYSTEM DATA SUMMARY:
            
            [OVERALL TOTALS]:
            {totals_str}
            
            [MONTHLY BREAKDOWN]:
            {monthly_str}
            
            [RAW SAMPLE]:
            {df.head(10).to_string()}
            """
        else:
            data_context = df.head(50).to_string()

        # 3. Construct Prompts
        system_msg = """You are a Strategic Data Analyst. 
        - Use the [MONTHLY BREAKDOWN] to answer questions about specific dates (like January).
        - Use the [OVERALL TOTALS] for general performance questions.
        - If the user asks for a specific country not in the raw sample, trust the Breakdown tables provided above.
        - Be direct, professional, and highlight trends."""
        
        user_msg = f"Tab: {tab_name}\nData:\n{data_context}\n\nUser Question: {custom_prompt if custom_prompt else f'Analyze the performance for {tab_name}'}"

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
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ]
            )
            return response.choices[0].message.content

    except Exception as e:
        return f"AI Logic Error: {str(e)}"
