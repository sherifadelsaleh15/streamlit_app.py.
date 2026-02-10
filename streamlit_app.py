import streamlit as st
from groq import Groq
import google.generativeai as genai

# Securely fetch APIs from Streamlit Secrets
# If testing locally without secrets, use: GROQ_API_KEY = "your_key"
GROQ_API_KEY = st.secrets["GROQ_API_KEY"] if "GROQ_API_KEY" in st.secrets else ""
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else ""

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    """
    Generates insights using Gemini or Groq, pulling API keys from secrets.
    """
    try:
        data_summary = df.to_string()
        
        # Build Forecast Context if data is available
        forecast_context = ""
        if forecast_df is not None:
            # Get the last 4 predicted values
            f_summary = forecast_df[['ds', 'yhat']].tail(4).to_string()
            forecast_context = f"\n\nAI PREDICTION DATA:\n{f_summary}"

        system_msg = (
            "You are a Strategic Data Analyst. Use the data and predictions provided. "
            "Compare historical months and evaluate if the AI prediction shows growth or risk. "
            "Identify critical gaps and suggest one strategic action."
        )
        
        if custom_prompt:
            user_msg = f"Data Context:\n{data_summary}{forecast_context}\n\nUser Question: {custom_prompt}"
        else:
            user_msg = f"Analyze the {tab_name} data. Context:\n{data_summary}{forecast_context}"

        # --- GEMINI EXECUTION ---
        if engine == "gemini":
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{system_msg}\n\n{user_msg}")
            return response.text

        # --- GROQ EXECUTION ---
        if engine == "groq":
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content

    except Exception as e:
        return f"Error generating insight: {str(e)}"
