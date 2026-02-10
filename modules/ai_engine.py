import streamlit as st
from groq import Groq
import google.generativeai as genai

def get_ai_strategic_insight(df, tab_name, engine="groq"):
    """
    Unified AI Engine: Pulls keys securely from st.secrets
    """
    try:
        # Access keys securely from the secrets file
        GROQ_KEY = st.secrets["GROQ_API_KEY"]
        GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
        
        # Prepare the data context (Latest 30 entries)
        data_summary = df.tail(30).to_string()
        prompt = f"Analyze these {tab_name} OKRs: {data_summary}. Provide a 3-point executive summary."

        if engine == "groq":
            client = Groq(api_key=GROQ_KEY)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content

        elif engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
            
    except KeyError:
        return "⚠️ Secrets not found. Please add your keys to .streamlit/secrets.toml"
    except Exception as e:
        return f"AI Engine Error: {str(e)}"
