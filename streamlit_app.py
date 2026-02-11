GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# Configure Gemini once at startup
genai.configure(api_key=GEMINI_KEY)

# Get available models
@st.cache_resource
def get_gemini_model():
    """Get the best available Gemini model"""
    try:
        # List available models
        models = genai.list_models()
        
        # Priority order of models to try
        model_preferences = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro',
            'gemini-pro-vision'
        ]
        
        # Find first available model from preferences
        available_models = [m.name for m in models]
        
        for preferred in model_preferences:
            # Check if model exists in any format
            for avail in available_models:
                if preferred in avail:
                    # Extract the clean model name
                    model_name = avail.split('/')[-1]
                    try:
                        test_model = genai.GenerativeModel(model_name)
                        # Test with a simple prompt
                        test_model.generate_content("test", generation_config={'max_output_tokens': 10})
                        return model_name
                    except:
                        continue
        
        return None
    except Exception as e:
        st.error(f"Gemini initialization error: {str(e)}")
        return None

# PDF HELPER
def generate_pdf(report_text, tab_name):
if not PDF_SUPPORT:
@@ -90,28 +131,27 @@ def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
user_msg = f"Dashboard Tab: {tab_name}\n\nUser Question: {custom_prompt if custom_prompt else f'Compare the regional performance in {tab_name} and provide strategic recommendations.'}"

if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            # Get the best available model
            gemini_model_name = get_gemini_model()

            # FIXED: Use 'models/gemini-1.5-flash' format for v1beta API
            # OR use the simpler 'gemini-pro' which is more stable
            try:
                # Try gemini-1.5-flash first
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}")
            except Exception as e1:
                try:
                    # Fallback to gemini-1.5-flash without 'models/' prefix
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}")
                except Exception as e2:
                    try:
                        # Final fallback to gemini-pro (most stable)
                        model = genai.GenerativeModel('gemini-pro')
                        response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}")
                    except Exception as e3:
                        return f"AI Logic Error: Gemini API failed. Tried multiple models. Latest error: {str(e3)}"
            if not gemini_model_name:
                return "AI Logic Error: No Gemini models available. Please check your API key and permissions."

            return response.text
            try:
                # Initialize model with the correct name
                model = genai.GenerativeModel(gemini_model_name)
                
                # Generate response with appropriate parameters
                response = model.generate_content(
                    f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}",
                    generation_config={
                        'temperature': 0.2,
                        'max_output_tokens': 2048,
                    }
                )
                return response.text
            except Exception as e:
                return f"AI Logic Error: Gemini API failed with model {gemini_model_name}. Error: {str(e)}"
else:
client = Groq(api_key=GROQ_KEY)
response = client.chat.completions.create(
@@ -219,11 +259,18 @@ def check_password():
# Gemini Report
st.divider()
st.subheader("Strategic AI Report")
    if st.button("Generate Analysis"):
    
    # Check if Gemini is available before showing button
    gemini_available = get_gemini_model() is not None
    
    if st.button("Generate Analysis", disabled=not gemini_available):
with st.spinner("Analyzing with Gemini..."):
st.session_state.ai_report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
st.rerun()

    if not gemini_available:
        st.warning("⚠️ Gemini AI is currently unavailable. Please check your API key and try again later. Using Groq for analysis is still available in the sidebar chat.")
    
if st.session_state.ai_report:
st.markdown(st.session_state.ai_report)

@@ -244,5 +291,4 @@ def check_password():
with st.expander(f"Data for: {kw}"):
fig = px.line(kw_data, x='dt', y=value_col, markers=True, title=f"Trend: {kw}")
if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed"))
                    # Added unique keys to prevent DuplicateElementId error
st.plotly_chart(fig, use_container_width=True, key=f"trend_{loc_idx}_{kw_idx}")
