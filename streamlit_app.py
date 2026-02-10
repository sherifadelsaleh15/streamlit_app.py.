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
    if st.button("Generate Comparison Report"):
        report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
        st.write(report)
        st.download_button("Download Report", report, file_name=f"{sel_tab}_comparison.txt")

    st.divider()

    # --- DATA TABLE ---
    st.subheader("Data Table")
    st.dataframe(tab_df, use_container_width=True)
    st.download_button("Download Table CSV", tab_df.to_csv(index=False), file_name=f"{sel_tab}_data.csv")

    st.divider()

    # --- TOP LISTS (GA4/GSC ONLY) ---
    if "TOP_PAGES" in sel_tab.upper() or "GA4" in sel_tab.upper():
        st.subheader("Top 15 Pages")
        page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL'])), None)
        num_cols = tab_df.select_dtypes('number').columns
        if page_col and len(num_cols) > 0:
            top_15_df = tab_df.groupby(page_col)[num_cols[0]].sum().sort_values(ascending=False).head(15).reset_index()
            fig_top = px.bar(top_15_df, x=num_cols[0], y=page_col, orientation='h', title="Top 15 Pages Ranking")
            st.plotly_chart(fig_top, use_container_width=True)
            st.download_button("Download Top 15 Data", top_15_df.to_csv(index=False), file_name="top_15.csv")

    if "GSC" in sel_tab.upper():
        st.subheader("Top 20 Keywords")
        kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
        click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
        if kw_col and click_col:
            top_20_df = tab_df.groupby(kw_col)[click_col].sum().sort_values(ascending=False).head(20).reset_index()
            fig_kw = px.bar(top_20_df, x=click_col, y=kw_col, orientation='h', title="Top 20 Keywords Ranking")
            st.plotly_chart(fig_kw, use_container_width=True)
            st.download_button("Download Top 20 Data", top_20_df.to_csv(index=False), file_name="top_20.csv")

    st.divider()

    # --- SEPARATE OKR CHART LOGIC ---
    st.subheader("Individual Performance Charts")
    
    metric_name_col = next((c for c in tab_df.columns if 'METRIC' in c.upper()), None)
    has_value_col = 'Value' in tab_df.columns

    # Loop through Locations first, then Metrics, to keep everything separate
    locations = sorted(tab_df[loc_col].unique()) if loc_col else [None]
    
    for loc in locations:
        loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
        
        if metric_name_col and has_value_col:
            # OKR Style (Long format)
            unique_metrics = sorted(loc_data[metric_name_col].unique())
            for met in unique_metrics:
                chart_df = loc_data[loc_data[metric_name_col] == met]
                if not chart_df.empty:
                    # Individual container for each OKR
                    with st.container():
                        st.markdown(f"### {met} - {loc if loc else ''}")
                        fig = px.line(chart_df, x='dt', y='Value', markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                        # Specific CSV for just this chart
                        st.download_button(f"Download Data for {met}", chart_df.to_csv(index=False), file_name=f"{met}_{loc}.csv", key=f"dl_{met}_{loc}")
                        st.write("---")
        else:
            # GA4/GSC Style (Wide format)
            num_cols = [c for c in loc_data.select_dtypes('number').columns 
                        if not any(x in c.upper() for x in ['ID', 'YEAR', 'MONTH', 'POSITION'])]
            for col_name in num_cols:
                if not loc_data[col_name].dropna().empty:
                    with st.container():
                        st.markdown(f"### {col_name} - {loc if loc else ''}")
                        fig = px.line(loc_data, x='dt', y=col_name, markers=True)
                        st.plotly_chart(fig, use_container_width=True)
                        st.download_button(f"Download Data for {col_name}", loc_data[['dt', col_name]].to_csv(index=False), file_name=f"{col_name}_{loc}.csv", key=f"dl_{col_name}_{loc}")
                        st.write("---")

    # --- SIDEBAR CHAT ---
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
