user_msg = f"Dashboard Tab: {tab_name}\n\nUser Question: {custom_prompt if custom_prompt else f'Compare the regional performance in {tab_name}'}"

# --- ENGINES ---
        if engine == "gemini":
     if engine == "gemini":
genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel(model_name='models/gemini-3-flash-preview')
            response = model.generate_content(f"{system_msg}\n\n{user_msg}")
            response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}")
            # Use 'gemini-1.5-flash' - this is the current standard name
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}")
            except Exception:
                # Fallback to gemini-pro if flash is having versioning issues
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}")
            
return response.text
else:
client = Groq(api_key=GROQ_KEY)
