@@ -14,60 +14,54 @@ def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, fo
        metric_col = next((c for c in df.columns if any(x in c.upper() for x in ['METRIC', 'TYPE', 'KEYWORD', 'QUERY'])), None)
        date_col = 'dt'

        # 2. Build Advanced Data Context
        # 2. Build Comparison Data Context
        if loc_col and val_col:
            # TOTALS SUMMARY
            group_total = [loc_col]
            if metric_col: group_total.append(metric_col)
            totals_str = df.groupby(group_total)[val_col].sum().reset_index().to_string(index=False)

            # MONTHLY BREAKDOWN SUMMARY (This makes it "Smarter")
            # We convert dates to string so the AI can read "Jan 2026" easily
            # Create a pivot-style summary for the AI to compare regions easily
            monthly_df = df.copy()
            monthly_df['Month'] = monthly_df[date_col].dt.strftime('%b %Y')

            group_month = [loc_col, 'Month']
            if metric_col: group_month.insert(1, metric_col)
            # Comparison Matrix (Region vs Metric vs Month)
            comparison_matrix = monthly_df.groupby([loc_col, 'Month', metric_col if metric_col else loc_col])[val_col].sum().unstack(level=0).fillna(0)

            monthly_str = monthly_df.groupby(group_month)[val_col].sum().reset_index().to_string(index=False)
            # Simple Totals
            group_total = [loc_col]
            if metric_col: group_total.append(metric_col)
            totals_str = df.groupby(group_total)[val_col].sum().reset_index().to_string(index=False)

            data_context = f"""
            SYSTEM DATA SUMMARY:
            SYSTEM STRATEGIC DATA:
            
            [OVERALL TOTALS]:
            {totals_str}
            [REGIONAL COMPARISON MATRIX (Monthly)]:
            {comparison_matrix.to_string()}
            
            [MONTHLY BREAKDOWN]:
            {monthly_str}
            
            [RAW SAMPLE]:
            {df.head(10).to_string()}
            [LIFETIME TOTALS PER REGION]:
            {totals_str}
            """
        else:
            data_context = df.head(50).to_string()

        # 3. Construct Prompts
        system_msg = """You are a Strategic Data Analyst. 
        - Use the [MONTHLY BREAKDOWN] to answer questions about specific dates (like January).
        - Use the [OVERALL TOTALS] for general performance questions.
        - If the user asks for a specific country not in the raw sample, trust the Breakdown tables provided above.
        - Be direct, professional, and highlight trends."""
        # 3. Enhanced Comparison Instructions
        system_msg = """You are a Senior Strategic Analyst. 
        - When asked to compare countries, use the COMPARISON MATRIX to find differences in growth, volume, and monthly trends.
        - Identify which market is leading and which is lagging.
        - If data for a month is 0 in the matrix, interpret it as 'No Activity' for that specific period.
        - Be critical: don't just state the numbers, explain what the gap between markets means for the business."""

        user_msg = f"Tab: {tab_name}\nData:\n{data_context}\n\nUser Question: {custom_prompt if custom_prompt else f'Analyze the performance for {tab_name}'}"
        user_msg = f"Dashboard Tab: {tab_name}\n\nUser Question: {custom_prompt if custom_prompt else f'Compare the regional performance in {tab_name}'}"

        # --- ENGINES ---
        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel(model_name='models/gemini-3-flash-preview')
            response = model.generate_content(f"{system_msg}\n\n{user_msg}")
            response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}")
            return response.text
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                    {"role": "user", "content": f"{user_msg}\n\nData Context:\n{data_context}"}
                ]
            )
            return response.choices[0].message.content
