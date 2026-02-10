import streamlit as st
from groq import Groq
import google.generativeai as genai

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    # Using st.secrets is safer than hardcoding strings!
    GROQ_KEY = st.secrets.get("GROQ_API_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
    
    # Prep data
    data_summary = df.tail(20).to_string()
    system_msg = (
        "You are a Strategic Data Analyst. "
        "Always include a 'Data Health Grade' (A, B, or C) at the start of your report."
    )
    
    user_msg = custom_prompt if custom_prompt else f"Analyze OKR trends for {tab_name}."
    full_query = f"{user_msg}\n\nContext Data (Last 20 rows):\n{data_summary}"

    # --- Engine: Gemini ---
    if engine == "gemini":
        try:
            genai.configure(api_key=GEMINI_KEY)
            # Gemini 1.5 Pro/Flash uses system_instruction in the constructor
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=system_msg
            )
            response = model.generate_content(full_query)
            return response.text
        except Exception as e:
            st.toast(f"Gemini Error: {str(e)}. Falling back to Groq...", icon="🔄")
            engine = "groq" # Trigger fallback

    # --- Engine: Groq ---
    if engine == "groq":
        try:
            client = Groq(api_key=GROQ_KEY)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": full_query}
                ],
                temperature=0.3
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"❌ Critical Error: Both engines failed. {str(e)}"
