import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
from modules.ui_components import apply_custom_css, render_header, render_footer

# 1. Page Config
st.set_page_config(page_title="OKR Strategic Dashboard", layout="wide")
apply_custom_css()

# 2. Session State for Chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 3. Load Data
df_dict = load_and_preprocess_data()

# 4. Sidebar Filters
st.sidebar.title("Dashboard Filters")

sel_tab = st.sidebar.selectbox("Select Strategy Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # --- Objective Filter ---
    obj_col = next((c for c in tab_df.columns if 'OBJECTIVE' in c.upper()), None)
    if obj_col:
        all_objs = sorted(tab_df[obj_col].unique())
        sel_objs = st.sidebar.multiselect("Filter Objectives", all_objs, default=all_objs)
        tab_df = tab_df[tab_df[obj_col].isin(sel_objs)]

    # --- Location Filter ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    if loc_col:
        all_locs = sorted(tab_df[loc_col].unique())
        sel_locs = st.sidebar.multiselect(f"Filter {loc_col}", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- Chat Reset Button ---
    st.sidebar.divider()
    if st.sidebar.button("🗑️ Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # --- Sidebar Chat (Groq) ---
    st.sidebar.subheader("Data Chat")
    user_q = st.sidebar.text_input("Ask a question about this data:")
    if user_q:
        with st.sidebar:
            with st.spinner("Analyzing..."):
                ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
                st.session_state.chat_history.append((user_q, ans))

    for q, a in st.session_state.chat_history[::-1]:
        st.sidebar.markdown(f"**You:** {q}")
        st.sidebar.info(a)

    # 5. Main Dashboard UI
    render_header("Strategic Intelligence", f"Current View: {sel_tab}")

    # --- Gemini Report Section ---
    st.subheader("Executive Analysis")
    if st.button("Generate Report (via Gemini)"):
        with st.spinner("Gemini is analyzing all rows and locations..."):
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.markdown(report)
            st.download_button(
                label="📩 Download Report as Text",
                data=report,
                file_name=f"OKR_Report_{sel_tab}.txt",
                mime="text/plain"
            )

    st.divider()

    # --- 6. Individual Charts (Metric + Location) ---
    st.subheader("Detailed Performance Trends")
    
    metric_name_col = next((c for c in tab_df.columns if 'METRIC' in c.upper()), None)

    if loc_col and metric_name_col:
        unique_locations = sorted(tab_df[loc_col].unique())
        unique_metrics = sorted(tab_df[metric_name_col].unique())

        for loc in unique_locations:
            st.markdown(f"#### 🌏 {loc}")
            loc_data = tab_df[tab_df[loc_col] == loc]
            
            # Display charts in 2 columns for this location
            chart_cols = st.columns(2)
            for i, met in enumerate(unique_metrics):
                chart_df = loc_data[loc_data[metric_name_col] == met]
                
                if not chart_df.empty:
                    with chart_cols[i % 2]:
                        # Title strictly identifying Metric and Location
                        fig = px.line(
                            chart_df, 
                            x='dt', 
                            y='Value', 
                            title=f"{met} — {loc}",
                            markers=True
                        )
                        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
                        st.plotly_chart(fig, use_container_width=True)
    else:
        # Fallback for GSC/GA4 where metrics are columns
        num_cols = [c for c in tab_df.select_dtypes('number').columns if not any(x in c.upper() for x in ['ID', 'YEAR'])]
        cols = st.columns(2)
        for i, col in enumerate(num_cols):
            with cols[i % 2]:
                fig = px.line(tab_df, x='dt', y=col, color=loc_col if loc_col else None, title=f"{col} Overview")
                st.plotly_chart(fig, use_container_width=True)

    render_footer()

else:
    st.warning("Please upload or select a valid data tab to begin.")
