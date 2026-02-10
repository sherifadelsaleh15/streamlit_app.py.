import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight

st.set_page_config(layout="wide")

# 1. Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 2. Load Data
df_dict = load_and_preprocess_data()
sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # --- FILTERS ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    if loc_col:
        all_locs = sorted(tab_df[loc_col].unique())
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- REPORT SECTION (MONTH VS NEXT MONTH) ---
    st.subheader("Monthly Comparison Report")
    if st.button("Generate Comparison Report"):
        with st.spinner("Calculating month-over-month variance..."):
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.write(report)
            st.download_button("Download Report", report, file_name=f"{sel_tab}_comparison.txt")

    st.divider()

    # --- DATA TABLE ---
    st.subheader("Data Table")
    st.dataframe(tab_df, use_container_width=True)
    st.download_button("Download Table CSV", tab_df.to_csv(index=False), file_name=f"{sel_tab}_data.csv")

    st.divider()

    # --- TOP 15 / TOP 20 SECTION ---
    if "TOP_PAGES" in sel_tab.upper() or "GA4" in sel_tab.upper():
        st.subheader("Top 15 Pages")
        page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL'])), None)
        num_cols = tab_df.select_dtypes('number').columns
        if page_col and len(num_cols) > 0:
            top_15_df = tab_df.groupby(page_col)[num_cols[0]].sum().sort_values(ascending=False).head(15).reset_index()
            fig_top = px.bar(top_15_df, x=num_cols[0], y=page_col, orientation='h', title="Top 15 Pages")
            st.plotly_chart(fig_top, use_container_width=True)
            # Download specific chart data
            st.download_button("Download Top 15 Chart Data", top_15_df.to_csv(index=False), file_name="top_15_pages.csv")

    if "GSC" in sel_tab.upper():
        st.subheader("Top 20 Keywords")
        kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
        click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
        if kw_col and click_col:
            top_20_df = tab_df.groupby(kw_col)[click_col].sum().sort_values(ascending=False).head(20).reset_index()
            fig_kw = px.bar(top_20_df, x=click_col, y=kw_col, orientation='h', title="Top 20 Keywords")
            st.plotly_chart(fig_kw, use_container_width=True)
            # Download specific chart data
            st.download_button("Download Top 20 Chart Data", top_20_df.to_csv(index=False), file_name="top_20_keywords.csv")

    # --- MAIN CHARTS ---
    st.subheader("Performance Trends")
    st.info("To download a chart as an image, hover over it and click the camera icon.")
    
    # Logic for individual charts per Location
    num_cols = [c for c in tab_df.select_dtypes('number').columns if not any(x in c.upper() for x in ['ID', 'YEAR', 'MONTH', 'POSITION'])]
    locations = sorted(tab_df[loc_col].unique()) if loc_col else [None]
    
    for loc in locations:
        loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
        if not loc_data.empty:
            if loc: st.write(f"Location: {loc}")
            cols = st.columns(2)
            for i, col_name in enumerate(num_cols):
                with cols[i % 2]:
                    fig = px.line(loc_data, x='dt', y=col_name, title=f"{col_name} - {loc if loc else ''}", markers=True)
                    st.plotly_chart(fig, use_container_width=True)

    # --- SIDEBAR CHAT & RESET ---
    st.sidebar.divider()
    if st.sidebar.button("Reset Chat History"):
        st.session_state.chat_history = []
        st.rerun()

    user_q = st.sidebar.text_input("Ask about data:", key="user_input")
    if user_q:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
        st.session_state.chat_history.append((user_q, ans))
    
    if st.session_state.chat_history:
        for q, a in st.session_state.chat_history[::-1]:
            st.sidebar.write(f"User: {q}")
            st.sidebar.write(f"Assistant: {a}")
