import streamlit as st
from groq import Groq
import google.generativeai as genai

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    """
    Dual-AI Engine:
    - Gemini: Best for high-level summaries and reading large tables.
    - Groq: Best for fast, conversational chat in the sidebar.
    """
    try:
        # 1. Fetch Keys from Secrets
        GROQ_KEY = st.secrets["GROQ_API_KEY"]
        GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
        
        # 2. Prepare the Data Context
        # We take a sample or the tail to stay within token limits while providing enough context
        data_sample = df.tail(30).to_string()
        
        # 3. Define the Personas & Prompts
        if custom_prompt:
            # Persona for the Groq Sidebar Chat
            system_prompt = f"You are a helpful Data Assistant. Answer based on this data: {data_sample}"
            user_payload = custom_prompt
        else:
            # Persona for the Gemini Executive Summary
            system_prompt = f"You are a Senior Strategy Consultant. Analyze these OKRs for {tab_name}."
            user_payload = f"Based on this data: {data_sample}, provide 3 executive bullet points on performance, risks, and next steps."

        # 4. Engine Logic
        if engine == "groq":
            client = Groq(api_key=GROQ_KEY)
            # Using Llama 3 for fast, accurate chat responses
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_payload}
                ],
                temperature=0.2 # Lower temperature = more factual data analysis
            )
            return response.choices[0].message.content

        elif engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            # Gemini 1.5 Flash is highly efficient for data summarization
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"{system_prompt}\n\nTask: {user_payload}"
            response = model.generate_content(full_prompt)
            return response.text

    except KeyError:
        return "⚠️ API Keys missing! Add GROQ_API_KEY and GEMINI_API_KEY to your Streamlit Secrets."
    except Exception as e:
        return f"❌ Intelligence Engine Error: {str(e)}"

def format_data_for_ai(df):
    """
    Optional helper to clean up data before sending to AI
    to ensure the AI doesn't get confused by IDs or nulls.
    """
    # Remove technical columns that AI doesn't need to 'read'
    cols_to_drop = [c for c in df.columns if 'ID' in c.upper() or 'dt' in c]
    clean_df = df.drop(columns=cols_to_drop, errors='ignore')
    return clean_df.tail(20).to_string()
