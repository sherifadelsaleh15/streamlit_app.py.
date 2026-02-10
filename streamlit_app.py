import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight

st.set_page_config(layout="wide")

# Initialize Chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

df_dict = load_and_preprocess_data()
sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # --- 1. FILTERS (OBJECTIVE & COUNTRY) ---
    st.sidebar.title("Filters")
    
    # Objective Filter
    obj_col = next((c for c in tab_df.columns if 'OBJECTIVE' in c.upper()), None)
    if obj_col:
        all_objs = sorted(tab_df[obj_col].unique())
        sel_objs = st.sidebar.multiselect("Select Objectives", all_objs, default=all_objs)
        tab_df = tab_df[tab_df[obj_col].isin(sel_objs)]

    # Country/Region Filter
    country_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
    if country_col:
        all_countries = sorted(tab_df[country_col].unique())
        sel_countries = st.sidebar.multiselect(f"Select {country_col}", all_countries, default=all_countries)
        tab_df = tab_df[tab_df[country_col].isin(sel_countries)]

    # --- 2. REPORT SECTION ---
    st.title(f"Strategic Analysis: {sel_tab}")
    
    if st.button("Generate Report (via Gemini)"):
        with st.spinner("Analyzing..."):
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.markdown(report)
            st.download_button("📩 Download Report", report, file_name=f"Report_{sel_tab}.txt")

    # --- 3. SEPARATE CHARTS PER COUNTRY ---
    st.divider()
    st.subheader("Regional Performance (Individual Charts)")

    if country_col:
        # Loop through each selected country and create its own section
        for country in sel_countries:
            country_specific_df = tab_df[tab_df[country_col] == country]
            
            with st.expander(f"📊 {country} Performance", expanded=True):
                # Get numeric columns for metrics
                val_cols = [c for c in country_specific_df.select_dtypes('number').columns if not any(x in c.upper() for x in ['ID', 'YEAR'])]
                
                chart_cols = st.columns(len(val_cols)) if len(val_cols) > 0 else []
                
                for i, m_name in enumerate(val_cols):
                    with chart_cols[i % len(chart_cols)]:
                        fig = px.line(country_specific_df, x='dt', y=m_name, title=f"{country}: {m_name}")
                        st.plotly_chart(fig, use_container_width=True)
    else:
        # Fallback if no country column exists
        st.info("No Country/Region column found to separate charts.")

    # --- 4. SIDEBAR CHAT & RESET ---
    st.sidebar.divider()
    if st.sidebar.button("🗑️ Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

    user_q = st.sidebar.text_input("Ask about this data:")
    if user_q:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
        st.session_state.chat_history.append((user_q, ans))

    for q, a in st.session_state.chat_history[::-1]:
        st.sidebar.write(f"**You:** {q}")
        st.sidebar.info(a)
