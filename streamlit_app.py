import streamlit as st
import pandas as pd
from modules.data_loader import load_and_preprocess_data
from modules.ai_engine import get_ai_strategic_insight
import plotly.express as px

st.set_page_config(layout="wide")

# Initialize Chat History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

df_dict = load_and_preprocess_data()
sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # --- REGION FILTERING & CHART LABELING ---
    region_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
    if region_col:
        all_regs = sorted(tab_df[region_col].unique())
        sel_regs = st.sidebar.multiselect(f"Select {region_col}", all_regs, default=all_regs)
        tab_df = tab_df[tab_df[region_col].isin(sel_regs)]

    # --- MAIN UI ---
    st.title(f"Strategic Dashboard: {sel_tab}")

    # 1. GENERATE REPORT (GEMINI)
    if st.button("Generate Report (via Gemini)"):
        report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
        st.markdown(report)
        # Download Button
        st.download_button("📩 Download Report", report, file_name=f"{sel_tab}_report.txt")

    # 2. CHARTS WITH REGION LABELS
    st.subheader("Performance Breakdown")
    # Identify numeric columns
    val_cols = [c for c in tab_df.select_dtypes('number').columns if not any(x in c.upper() for x in ['ID', 'YEAR'])]
    
    cols = st.columns(2)
    for i, col_name in enumerate(val_cols):
        with cols[i % 2]:
            # Use Plotly so the Region is visible in the legend/hover
            fig = px.line(tab_df, x='dt', y=col_name, color=region_col if region_col else None, 
                          title=f"{col_name} by {region_col if region_col else 'Date'}")
            st.plotly_chart(fig, use_container_width=True)

    # 3. CHAT WITH RESET
    st.sidebar.divider()
    st.sidebar.subheader("Chat")
    if st.sidebar.button("🗑️ Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

    user_input = st.sidebar.text_input("Ask a question:")
    if user_input:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_input)
        st.session_state.chat_history.append((user_input, ans))

    for q, a in st.session_state.chat_history[::-1]:
        st.sidebar.write(f"**You:** {q}")
        st.sidebar.info(a)
