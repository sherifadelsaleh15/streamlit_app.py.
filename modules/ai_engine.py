# modules/ai_engine.py
import streamlit as st
import pandas as pd
from groq import Groq
import google.generativeai as genai
from config import GROQ_KEY, GEMINI_KEY

class AIEngine:
    """Centralized AI engine for handling both Groq and Gemini"""
    
    def __init__(self):
        self.groq_client = None
        self.gemini_model = None
        self.gemini_error = None
        self._setup_clients()
    
    def _setup_clients(self):
        """Initialize AI clients"""
        # Setup Groq
        try:
            self.groq_client = Groq(api_key=GROQ_KEY)
        except Exception as e:
            st.error(f"Groq initialization failed: {str(e)}")
            self.groq_client = None
        
        # Setup Gemini with your key
        try:
            genai.configure(api_key=GEMINI_KEY)
            # Try gemini-pro first (most stable)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            # Test the model
            test_response = self.gemini_model.generate_content("test")
            self.gemini_error = None
        except Exception as e:
            self.gemini_model = None
            self.gemini_error = str(e)
    
    def is_gemini_available(self):
        """Check if Gemini is available"""
        return self.gemini_model is not None and self.gemini_error is None
    
    def get_gemini_error(self):
        """Get Gemini error message"""
        return self.gemini_error
    
    def _prepare_data_context(self, df, tab_name):
        """Prepare data context for AI analysis - works with your column naming"""
        try:
            # Find columns based on your standardized naming
            loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['COUNTRY', 'REGION', 'GEO', 'LOCATION'])), None)
            val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'IMPRESSIONS', 'CTR', 'POSITION', 'VALUE'])), None)
            metric_col = next((c for c in df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'DEVICE'])), None)
            
            context_parts = [f"DASHBOARD: {tab_name}"]
            
            # Add data summary
            context_parts.append(f"\n[DATA OVERVIEW]")
            context_parts.append(f"Rows: {len(df)}")
            context_parts.append(f"Date range: {df['dt'].min()} to {df['dt'].max()}" if 'dt' in df.columns else "No date column")
            
            # Add regional breakdown if available
            if loc_col and val_col:
                summary = df.groupby(loc_col)[val_col].agg(['sum', 'mean', 'count']).reset_index()
                context_parts.append(f"\n[PERFORMANCE BY {loc_col.upper()}]:")
                context_parts.append(summary.to_string())
            
            # Add top metrics if available
            if metric_col and val_col:
                top_metrics = df.groupby(metric_col)[val_col].sum().nlargest(10).reset_index()
                context_parts.append(f"\n[TOP 10 {metric_col.upper()}]:")
                context_parts.append(top_metrics.to_string())
            
            # Add sample data
            context_parts.append(f"\n[RAW DATA SAMPLE]:")
            context_parts.append(df.head(10).to_string())
            
            return "\n".join(context_parts)
            
        except Exception as e:
            return f"Error preparing context: {str(e)}\nDataFrame columns: {df.columns.tolist()}"
    
    def get_strategic_insight(self, df, tab_name, custom_prompt=None, use_gemini=False):
        """Get AI-powered strategic insights"""
        
        data_context = self._prepare_data_context(df, tab_name)
        
        system_prompt = """You are a Senior Strategic Analyst specializing in digital marketing and business intelligence.

Your task is to analyze the provided data and deliver:
1. KEY INSIGHTS: What are the most important patterns, trends, and anomalies?
2. COMPARATIVE ANALYSIS: How do different regions/categories compare?
3. BUSINESS IMPLICATIONS: What do these numbers mean for the business?
4. RECOMMENDATIONS: Specific, actionable next steps.

Be direct, professional, and data-driven. Focus on strategic value."""

        user_prompt = f"""
{data_context}

USER QUERY: {custom_prompt if custom_prompt else f'Analyze the performance in {tab_name} and provide strategic recommendations.'}

Provide a concise but comprehensive strategic analysis:
"""
        
        try:
            if use_gemini:
                return self._call_gemini(system_prompt, user_prompt)
            else:
                return self._call_groq(system_prompt, user_prompt)
        except Exception as e:
            return f"AI Analysis Error: {str(e)}"
    
    def _call_groq(self, system_prompt, user_prompt):
        """Call Groq API"""
        if not self.groq_client:
            return "Groq client not available. Please check your API key."
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Groq API Error: {str(e)}"
    
    def _call_gemini(self, system_prompt, user_prompt):
        """Call Gemini API"""
        if not self.is_gemini_available():
            return f"Gemini unavailable: {self.gemini_error}"
        
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Gemini API Error: {str(e)}"
    
    def chat(self, df, tab_name, question):
        """Simple chat interface for data questions"""
        return self.get_strategic_insight(df, tab_name, custom_prompt=question, use_gemini=False)

# Singleton instance
@st.cache_resource
def get_ai_engine():
    """Get or create AI Engine singleton"""
    return AIEngine()
