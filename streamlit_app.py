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

    # --- REPORT SECTION ---
    st.subheader("Report")
    if st.button("Generate Report"):
        report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
        st.write(report)
        st.download_button("Download Report", report, file_name="report.txt")

    st.divider()

    # --- SPECIALIZED TOP LISTS (GA4 & GSC) ---
    if "TOP_PAGES" in sel_tab.upper() or "GA4" in sel_tab.upper():
        st.subheader("Top 15 Pages")
        page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL'])), None)
        metric_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['VIEWS', 'SESSIONS', 'USERS'])), tab_df.select_dtypes('number').columns[0])
        
        if page_col:
            top_pages = tab_df.groupby(page_col)[metric_col].sum().sort_values(ascending=False).head(15).reset_index()
            fig_pages = px.bar(top_pages, x=metric_col, y=page_col, orientation='h', title=f"Top 15 Pages by {metric_col}")
            fig_pages.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_pages, use_container_width=True)
            # Note: Users can download this as PNG using the camera icon on the chart

    if "GSC" in sel_tab.upper():
        st.subheader("Top 20 Keywords")
        kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
        click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), tab_df.select_dtypes('number').columns[0])
        
        if kw_col:
            top_kw = tab_df.groupby(kw_col)[click_col].sum().sort_values(ascending=False).head(20).reset_index()
            fig_kw = px.bar(top_kw, x=click_col, y=kw_col, orientation='h', title=f"Top 20 Keywords by {click_col}")
            fig_kw.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_kw, use_container_width=True)

    st.divider()

    # --- MAIN CHART SECTION ---
    st.subheader("Performance Trends")
    st.info("Hover over charts and click the Camera icon to download as Image/PDF")
    
    # [Logic for individual charts per Location remains same as previous step]
    # (Inserting the robust chart loop from previous code block here)
    num_cols = [c for c in tab_df.select_dtypes('number').columns if not any(x in c.upper() for x in ['ID', 'YEAR', 'MONTH'])]
    locations = sorted(tab_df[loc_col].unique()) if loc_col else [None]
    
    for loc in locations:
        loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
        if not loc_data.empty:
            if loc: st.write(f"Location: {loc}")
            cols = st.columns(2)
            for i, col_name in enumerate(num_cols):
                with cols[i % 2]:
                    fig = px.line(loc_data, x='dt', y=col_name, title=f"{col_name} - {loc if loc else ''}")
                    st.plotly_chart(fig, use_container_width=True)

    # --- DATA TABLE SECTION ---
    st.subheader("Data Table")
    st.dataframe(tab_df, use_container_width=True)
    st.download_button("Download Table CSV", tab_df.to_csv(index=False), file_name="data_table.csv")

    # --- SIDEBAR CHAT ---
    st.sidebar.divider()
    user_q = st.sidebar.text_input("Ask about data:")
    if user_q:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
        st.session_state.chat_history.append((user_q, ans))
    
    if st.session_state.chat_history:
        for q, a in st.session_state.chat_history[::-1]:
            st.sidebar.write(f"User: {q}")
            st.sidebar.write(f"Assistant: {a}")
