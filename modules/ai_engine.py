import google.generativeai as genai
import streamlit as st

def get_ai_strategic_insight(df, tab_name):
    """
    Connects to Google Gemini to analyze the specific data from your Google Sheet.
    """
    try:
        # Using the key you provided
        api_key = st.secrets.get("GEMINI_API_KEY", "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0")
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # We send the last 20 rows so the AI sees the most recent trends
        data_summary = df.tail(20).to_string()
        
        prompt = f"""
        You are a Senior Strategy Consultant for a global tech company. 
        Analyze this OKR performance data for the '{tab_name}' department.
        
        Data Context:
        {data_summary}
        
        Please provide:
        1. **Executive Summary**: 2 sentences on how we are doing.
        2. **Predictive Warning**: Based on the numbers, what is the biggest risk for next month?
        3. **Action Plan**: One specific tactic to improve these results.
        
        Keep it professional, short, and executive-ready.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI is resting: {str(e)}"
