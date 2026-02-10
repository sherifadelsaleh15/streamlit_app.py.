import streamlit as st
from groq import Groq
import google.generativeai as genai

# API Keys - Ensure these are correct for your environment
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    """
    Generates strategic insights by comparing current data against subsequent 
    time periods and identifying regional performance trends.
    """
    try:
        # Convert the filtered dataframe to a string for AI context
        data_summary = df.to_string()
        
        # --- SYSTEM PROMPT LOGIC ---
        # Forces the AI to act as a professional analyst and perform comparisons
        system_msg = (
            "You are a Strategic Data Analyst. Use ONLY the provided data table. "
            "Your goal is to compare the performance of each month against the following month. "
            "Instructions:\n"
            "1. Do not list column names or row counts.\n"
            "2. Identify the percentage or numerical change between consecutive months.\n"
            "3. Highlight which Region/Country is the top performer and which is declining.\n"
            "4. If a value is 0 or missing, identify it as a critical gap.\n"
            "5. Maintain a neutral, professional tone without using emojis or icons.\n"
            "6. If the answer is not in the data, strictly say 'Information not found in current data'."
        )
        
        # Define the task based on whether it's a general report or a specific user question
        if custom_prompt:
            user_msg = f"Data Context:\n{data_summary}\n\nUser Question: {custom_prompt}"
        else:
            user_msg = (
                f"Analyze the {tab_name} data. Focus on Month-over-Month (MoM) variance. "
                f"Compare the results of the earliest month to the next month in the sequence. "
                f"Summarize the strategic takeaways for this specific dataset:\n\n{data_summary}"
            )

        # --- GEMINI EXECUTION ---
        if engine == "gemini":
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Using 1.5 Flash for fast, efficient data processing
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                return response.text
            except Exception as e:
                # Fallback to Groq if Gemini fails
                engine = "groq"

        # --- GROQ EXECUTION ---
        if engine == "groq":
            client = Groq(api_key=GROQ_API_KEY)
            # Using Llama 3.3 70B for high-quality logical reasoning
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.1, # Low temperature for factual accuracy
                max_tokens=1024
            )
            return response.choices[0].message.content

    except Exception as e:
        return f"Error generating insight: {str(e)}"
