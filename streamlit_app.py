import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from modules.ui_components import apply_custom_css, render_header, render_footer

# 1. Page Configuration
st.set_page_config(page_title="Strategic Dashboard", layout="wide")
apply_custom_css()

# 2. Session State for Chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 3. Data Loading
df_dict = load_and_preprocess_data()
sel_tab = st.sidebar.selectbox("Select Strategy Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # --- FILTERS ---
    # Location Filter
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    if loc_col:
        all_locs = sorted(tab_df[loc_col].unique())
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # Objective Filter
    obj_col = next((c for c in tab_df.columns if 'OBJECTIVE' in c.upper()), None)
    if obj_col:
        all_objs = sorted(tab_df[obj_col].unique())
        sel_objs = st.sidebar.multiselect("Filter Objectives", all_objs, default=all_objs)
        tab_df = tab_df[tab_df[obj_col].isin(sel_objs)]

    # 4. Main UI
    render_header("Strategic Intelligence", f"Current View: {sel_tab}")

    # --- Gemini Report ---
    st.subheader("Executive Analysis")
    if st.button("Generate Report (via Gemini)"):
        with st.spinner("Analyzing data"):
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.markdown(report)
            st.download_button(
                label="Download Report", 
                data=report, 
                file_name=f"{sel_tab}_report.txt",
                mime="text/plain"
            )

    st.divider()

    # --- 5. Data Table View ---
    st.subheader("Source Data Table")
    st.dataframe(tab_df, use_container_width=True)
    
    # Download CSV button for the filtered table
    csv_data = tab_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Table as CSV",
        data=csv_data,
        file_name=f"{sel_tab}_data.csv",
        mime='text/csv'
    )

    st.divider()

    # --- 6. Chart Logic ---
    st.subheader("Performance Trends")
    
    metric_name_col = next((c for c in tab_df.columns if 'METRIC' in c.upper()), None)

    # Wide Format (GSC/GA4) or Long Format (OKR) handling
    if metric_name_col:
        unique_metrics = sorted(tab_df[metric_name_col].unique())
        if loc_col:
            unique_locations = sorted(tab_df[loc_col].unique())
            for loc in unique_locations:
                st.markdown(f"Location: {loc}")
                loc_data = tab_df[tab_df[loc_col] == loc]
                cols = st.columns(2)
                for i, met in enumerate(unique_metrics):
                    chart_df = loc_data[loc_data[metric_name_col] == met]
                    if not chart_df.empty:
                        with cols[i % 2]:
                            fig = px.line(chart_df, x='dt', y='Value', title=f"{met} - {loc}", markers=True)
                            st.plotly_chart(fig, use_container_width=True)
    else:
        num_cols = [c for c in tab_df.select_dtypes('number').columns 
                    if not any(x in c.upper() for x in ['ID', 'YEAR', 'MONTH', 'POSITION'])]
        if loc_col:
            unique_locations = sorted(tab_df[loc_col].unique())
            for loc in unique_locations:
                st.markdown(f"Location: {loc}")
                loc_data = tab_df[tab_df[loc_col] == loc]
                cols = st.columns(2)
                for i, col in enumerate(num_cols):
                    with cols[i % 2]:
                        fig = px.line(loc_data, x='dt', y=col, title=f"{col} - {loc}", markers=True)
                        st.plotly_chart(fig, use_container_width=True)

    # 7. Sidebar Chat
    st.sidebar.divider()
    if st.sidebar.button("Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

    user_q = st.sidebar.text_input("Question:")
    if user_q:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
        st.session_state.chat_history.append((user_q, ans))
    for q, a in st.session_state.chat_history[::-1]:
        st.sidebar.write(f"User: {q}")
        st.sidebar.write(f"Assistant: {a}")

    render_footer()
