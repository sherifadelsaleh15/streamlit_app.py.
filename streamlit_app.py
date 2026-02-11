import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from groq import Groq

# Zero-indentation imports
from modules.data_loader import load_and_preprocess_data
from modules.ml_models import get_prediction

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# API KEYS
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# --- HELPER FUNCTIONS ---
def get_ai_insight(df, tab_name):
    try:
        data_summary = df.head(20).to_string()
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"Senior Strategic Analyst. Analyze this {tab_name} data and provide 3 executive bullet points:\n{data_summary}")
        return response.text
    except Exception as e: return f"AI Error: {str(e)}"

# 2. Authentication
if "password_correct" not in st.session_state:
    st.subheader("Strategy Login")
    pwd = st.text_input("Enter Key", type="password")
    if st.button("Submit"):
        if pwd == "strategic_2026":
            st.session_state["password_correct"] = True
            st.rerun()
    st.stop()

# 3. Data Loading
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data loading failed: {e}"); st.stop()

# 4. Sidebar Navigation
sel_tab = st.sidebar.selectbox("Dashboard Section", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # --- FAILSAFE COLUMN DETECTION ---
    is_gsc = "GSC" in sel_tab.upper() or "POSITION" in sel_tab.upper()
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), 'Location')
    click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    value_col = click_col if (is_gsc and click_col) else next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VALUE', 'VIEWS', 'CLICKS'])), 'Value')
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), 'Metric')
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'
    is_ranking = value_col and ('POSITION' in value_col.upper() or 'RANK' in value_col.upper())

    # --- SIDEBAR FILTERS ---
    if loc_col in tab_df.columns:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")
    
    # --- CENTERED LEADERBOARD ---
    display_col = page_col if (page_col and "PAGE" in sel_tab.upper()) else metric_name_col
    if display_col in tab_df.columns and value_col in tab_df.columns:
        st.subheader(f"Top Performance: {display_col}")
        agg_method = 'min' if is_ranking else 'sum'
        top_df = tab_df.groupby(display_col)[value_col].agg(agg_method).reset_index()
        top_df = top_df.sort_values(by=value_col, ascending=(agg_method=='min')).head(15)
        fig_main = px.bar(top_df, x=value_col, y=display_col, orientation='h', template="plotly_white")
        st.plotly_chart(fig_main, use_container_width=True, key="main_leaderboard")

    st.divider()

    # --- RESTORED: STRATEGIC AI REPORT (GEMINI) ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Gemini is analyzing..."):
            st.session_state.ai_report = get_ai_insight(tab_df, sel_tab)
    if "ai_report" in st.session_state:
        st.info(st.session_state.ai_report)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)
    if display_col in tab_df.columns and date_col in tab_df.columns:
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col in tab_df.columns else [None]
        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"#### Region: {loc if loc else 'Global'}")
            top_region_items = loc_data.groupby(display_col)[value_col].sum().sort_values(ascending=False).head(5).index.tolist()
            
            for i, item in enumerate(top_region_items):
                item_data = loc_data[loc_data[display_col] == item].sort_values('dt')
                with st.expander(f"Trend: {item}"):
                    fig = px.line(item_data, x='dt', y=value_col, markers=True)
                    # FIX: Unique key to prevent StreamlitDuplicateElementId
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{loc}_{i}_{item}")

    # --- CHAT WITH DATA (SMART & CONCISE) ---
    st.sidebar.divider()
    st.sidebar.subheader("💬 Chat with Data")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.sidebar.button("🗑️ Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # Show history in sidebar
    for chat in st.session_state.chat_history:
        with st.sidebar.chat_message(chat["role"]):
            st.write(chat["content"])

    if user_input := st.sidebar.chat_input("Ask about the numbers..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.sidebar.chat_message("user"):
            st.write(user_input)

        try:
            client = Groq(api_key=GROQ_KEY)
            
            # Smart Context Construction: Grouped totals by Month and Country
            # This allows Grok to see EXACTLY what happened in Jan, Feb, etc.
            summary_df = tab_df.groupby([loc_col, tab_df[date_col].dt.strftime('%Y-%m')])[value_col].sum().reset_index()
            context_str = summary_df.to_string(index=False)

            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": f"""You are a concise Data Assistant. Use this summary table:
                        {context_str}
                        
                        RULES:
                        1. Be extremely brief. Just give the answer and one short insight.
                        2. If asked for a specific country or month, pull the number directly from the table above.
                        3. If asked 'What about...?', use previous chat context to answer.
                        """
                    },
                    *st.session_state.chat_history
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            with st.sidebar.chat_message("assistant"):
                st.write(answer)
        except Exception as e:
            st.sidebar.error(f"Grok Error: {str(e)}")
