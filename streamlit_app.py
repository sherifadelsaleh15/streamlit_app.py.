import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import google.generativeai as genai
from groq import Groq

# Zero-indentation imports
from modules.data_loader import load_and_preprocess_data
from modules.ml_models import generate_forecast, get_prediction

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# API KEYS
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# --- HELPER FUNCTIONS ---
def get_ai_insight(df, tab_name):
    try:
        data_summary = df.head(15).to_string()
        genai.configure(api_key=GEMINI_KEY)
        model_options = ['gemini-2.0-flash', 'gemini-3-flash-preview', 'gemini-2.5-flash']
        for m_name in model_options:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"Senior Strategic Analyst. Analyze: {tab_name} data:\n{data_summary}")
                return response.text
            except: continue
        return "AI Error: Model endpoints unavailable."
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
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    value_col = click_col if (is_gsc and click_col) else next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VALUE', 'VIEWS', 'CLICKS'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'
    is_ranking = value_col and ('POSITION' in value_col.upper() or 'RANK' in value_col.upper())

    # --- SIDEBAR FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- MAIN CONTENT ---
    col_title, col_dl = st.columns([4, 1])
    with col_title:
        st.title(f"Strategic View: {sel_tab}")
    with col_dl:
        csv_main = tab_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Sheet", data=csv_main, file_name=f"{sel_tab}_data.csv", mime='text/csv')

    # Leaderboard Logic (Same as original)
    L, M, R = st.columns([1, 4, 1])
    with M:
        display_col = page_col if (page_col and "PAGE" in sel_tab.upper()) else metric_name_col
        if display_col and value_col:
            st.subheader(f"Top 20 {display_col} by {value_col}")
            agg_method = 'min' if is_ranking else 'sum'
            top_df = tab_df.groupby(display_col)[value_col].agg(agg_method).reset_index()
            top_df = top_df.sort_values(by=value_col, ascending=(agg_method=='min')).head(20)
            fig_main = px.bar(top_df, x=value_col, y=display_col, orientation='h', template="plotly_white", 
                              color_discrete_sequence=['#4285F4' if is_gsc else '#34A853'])
            if is_ranking: fig_main.update_layout(xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_main, use_container_width=True)

    st.divider()

    # --- TRENDS SECTION ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)
    item_col = page_col if (page_col and "PAGE" in sel_tab.upper()) else metric_name_col

    if item_col and value_col and date_col in tab_df.columns:
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]
        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"## Region: {loc if loc else 'Global'}")
            top_region_items = loc_data.groupby(item_col)[value_col].sum().sort_values(ascending=False).head(10).index.tolist()
            for item in top_region_items:
                item_data = loc_data[loc_data[item_col] == item].sort_values('dt')
                with st.expander(f"{item} Trend Details"):
                    fig = px.line(item_data, x='dt', y=value_col, markers=True)
                    st.plotly_chart(fig, use_container_width=True)

    # --- CHAT WITH DATA (NEW & SMART GROK) ---
    st.sidebar.divider()
    st.sidebar.subheader("💬 Chat with Data")

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Reset Button
    if st.sidebar.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()

    # Display History
    for msg in st.session_state.messages:
        with st.sidebar.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if user_query := st.sidebar.chat_input("Ask about this data..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.sidebar.chat_message("user"):
            st.markdown(user_query)

        try:
            client = Groq(api_key=GROQ_KEY)
            
            # Smart Data Summary for Context
            monthly_perf = tab_df.groupby([pd.Grouper(key=date_col, freq='M'), loc_col])[value_col].sum().reset_index()
            monthly_perf[date_col] = monthly_perf[date_col].dt.strftime('%b %Y')
            data_context = monthly_perf.to_string(index=False)

            # System Instructions: Smart, Concise, Conversational
            sys_prompt = f"""You are a Strategic Data Scientist. 
            CONTEXT: {data_context}
            
            RULES:
            1. Be EXTREMELY concise. No "Based on the data..." or "I hope this helps".
            2. If the user asks about a specific month/region, provide only the number and a 1-sentence insight.
            3. Use the chat history for follow-up context.
            4. If data is missing for a specific request, say "No data for [Month/Region]".
            """

            full_messages = [{"role": "system", "content": sys_prompt}] + \
                            st.session_state.messages[-5:] # Last 5 messages for follow-up

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=full_messages,
                temperature=0.1 # High precision
            )
            
            answer = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.sidebar.chat_message("assistant"):
                st.markdown(answer)

        except Exception as e:
            st.sidebar.error(f"Grok Error: {str(e)}")
