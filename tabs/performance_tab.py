import streamlit as st
import plotly.express as px
import google.generativeai as genai

def render_performance_tab(tab_df, sel_tab, api_key):
    # Detect Layout Columns
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PLATFORM'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'VIEWS', 'USERS'])), None)

    if not page_col or not value_col:
        st.warning(f"Could not detect data columns for {sel_tab}. Found: {list(tab_df.columns)}")
        return

    st.title(f"Performance Analysis: {sel_tab}")

    # Leaderboard
    top_df = tab_df.groupby(page_col)[value_col].sum().nlargest(20).reset_index()
    fig = px.bar(top_df, x=value_col, y=page_col, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'])
    st.plotly_chart(fig, use_container_width=True)

    # Gemini Report Button
    if st.button("Generate AI Insights"):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"Analyze this {sel_tab} data: {tab_df.head(10).to_string()}")
        st.markdown(response.text)
