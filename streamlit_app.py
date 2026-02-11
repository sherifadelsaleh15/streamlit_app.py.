import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from modules.data_loader import load_and_preprocess_data
# We will define the logic for get_ai_strategic_insight locally to ensure it works with your specific context
from utils import get_prediction
from groq import Groq
import google.generativeai as genai

# 1. Page Config
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# --- API KEYS ---
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# --- CORE FUNCTIONS ---

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None, forecast_df=None):
    try:
        # 1. Identify Columns
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'SESSIONS', 'VALUE'])), None)
        metric_col = next((c for c in df.columns if any(x in c.upper() for x in ['METRIC', 'TYPE', 'KEYWORD', 'QUERY'])), None)
        date_col = 'dt'

        # 2. Build Comparison Data Context
        if loc_col and val_col:
            monthly_df = df.copy()
            monthly_df['Month'] = monthly_df[date_col].dt.strftime('%b %Y')
            
            # Comparison Matrix (Region vs Metric vs Month)
            comparison_matrix = monthly_df.groupby([loc_col, 'Month', metric_col if metric_col else loc_col])[val_col].sum().unstack(level=0).fillna(0)
            
            # Simple Totals
            group_total = [loc_col]
            if metric_col: group_total.append(metric_col)
            totals_str = df.groupby(group_total)[val_col].sum().reset_index().to_string(index=False)

            data_context = f"""
            SYSTEM STRATEGIC DATA:
            [REGIONAL COMPARISON MATRIX (Monthly)]:
            {comparison_matrix.to_string()}
            
            [LIFETIME TOTALS PER REGION]:
            {totals_str}
            """
        else:
            data_context = df.head(50).to_string()

        # 3. Enhanced Comparison Instructions
        system_msg = """You are a Senior Strategic Analyst. 
        - When asked to compare countries, use the COMPARISON MATRIX to find differences in growth, volume, and monthly trends.
        - Identify which market is leading and which is lagging.
        - If data for a month is 0 in the matrix, interpret it as 'No Activity' for that specific period.
        - Be critical: don't just state the numbers, explain what the gap between markets means for the business."""

        user_msg = f"Dashboard Tab: {tab_name}\n\nUser Question: {custom_prompt if custom_prompt else f'Compare the regional performance in {tab_name}'}"

        # --- ENGINES ---
        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel(model_name='models/gemini-3-flash-preview')
            response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}")
            return response.text
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"{user_msg}\n\nData Context:\n{data_context}"}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"AI Logic Error: {str(e)}"

def check_password():
    ADMIN_PASSWORD = "strategic_2026" 
    def password_entered():
        if st.session_state["password"] == ADMIN_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False
            
    if "password_correct" not in st.session_state:
        st.subheader("🔒 Digital Strategy Login")
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Dashboard Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else: 
        return True

# --- MAIN APP EXECUTION ---

if not check_password():
    st.stop()

# 3. Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_report" not in st.session_state:
    st.session_state.ai_report = ""

# 4. Load Data
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data Loading Error: {e}")
    st.stop()

sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # Identify Columns
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'

    # Nuclear Cleaning
    if value_col:
        def clean_currency(x):
            if isinstance(x, str):
                clean_str = re.sub(r'[^\d.]', '', x) 
                return clean_str if clean_str else '0'
            return x
        tab_df[value_col] = tab_df[value_col].apply(clean_currency)
        tab_df[value_col] = pd.to_numeric(tab_df[value_col], errors='coerce').fillna(0)

    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # Sidebar Filter
    if loc_col:
        raw_locs = tab_df[loc_col].dropna().unique()
        all_locs = sorted([str(x) for x in raw_locs], key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # Chat with Data (Groq)
    st.sidebar.divider()
    st.sidebar.subheader("Chat with Data")
    user_q = st.sidebar.text_input("Ask a question about this data:", key="user_input")
    if user_q:
        with st.sidebar:
            ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
            st.session_state.chat_history.append({"q": user_q, "a": ans})
    
    for chat in reversed(st.session_state.chat_history):
        st.sidebar.info(f"User: {chat['q']}")
        st.sidebar.write(f"AI: {chat['a']}")
        st.sidebar.divider()

    # Main Visuals
    st.title(f"Strategic View: {sel_tab}")
    
    # GSC Chart
    if "GSC" in sel_tab.upper() and metric_name_col:
        st.subheader("Top 20 Keywords")
        agg_k = 'min' if is_ranking else 'sum'
        top_k = tab_df.groupby(metric_name_col)[value_col].agg(agg_k).reset_index()
        top_k = top_k.sort_values(by=value_col, ascending=(agg_k=='min')).head(20)
        fig_k = px.bar(top_k, x=value_col, y=metric_name_col, orientation='h', color_discrete_sequence=['#4285F4'])
        if is_ranking: fig_k.update_layout(xaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_k, use_container_width=True)

    # Gemini Report
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."):
            st.session_state.ai_report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    # Monthly Trends
    st.divider()
    st.subheader("Monthly Performance Trends")
    if metric_name_col and value_col and date_col in tab_df.columns:
        agg_sort = 'min' if is_ranking else 'sum'
        top_20_list = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()

        for loc in (tab_df[loc_col].unique() if loc_col else [None]):
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"**Region: {loc if loc else 'Global'}**")
            region_keywords = [kw for kw in top_20_list if kw in loc_data[metric_name_col].unique()]

            for kw in region_keywords:
                kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
                with st.expander(f"Data for: {kw}"):
                    fig = px.line(kw_data, x='dt', y=value_col, markers=True, title=f"Trend: {kw}")
                    if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig, use_container_width=True)
