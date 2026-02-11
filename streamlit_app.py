import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from groq import Groq
import time

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
    """Gemini Token & Rate Limit Fix."""
    try:
        # 1. RPM Limit Check (ensuring ~5 requests per minute)
        if "last_gemini_call" in st.session_state:
            elapsed = time.time() - st.session_state.last_gemini_call
            if elapsed < 12: 
                return "⚠️ Rate limit safety: Please wait a few seconds before generating another report."

        # 2. TPM Limit Check: Compress data to minimize input tokens
        cols_to_send = [c for c in df.columns if c in ['dt', 'Location', 'Value', 'Users', 'Metric', 'Country']]
        data_summary = df[cols_to_send].head(15).to_string(index=False)
        
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        response = model.generate_content(
            f"Senior Strategic Analyst. Analyze: {tab_name} data:\n{data_summary}\n"
            "Provide 3 hyper-concise executive bullet points."
        )
        
        st.session_state.last_gemini_call = time.time()
        return response.text
    except Exception as e: 
        return f"AI Error (Quota/Token): {str(e)}"

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
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'VIEWS'])), 'Value')
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), 'Metric')
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'
    is_ranking = value_col and 'POSITION' in value_col.upper()

    # --- SIDEBAR FILTERS ---
    if loc_col in tab_df.columns:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")

    # --- CENTERED LEADERBOARDS ---
    L, M, R = st.columns([1, 4, 1])
    with M:
        display_col = page_col if (page_col and "PAGE" in sel_tab.upper()) else metric_name_col
        if display_col in tab_df.columns and value_col in tab_df.columns:
            st.subheader(f"Top 20 {display_col} by {value_col}")
            agg_method = 'min' if is_ranking else 'sum'
            top_df = tab_df.groupby(display_col)[value_col].agg(agg_method).reset_index()
            top_df = top_df.sort_values(by=value_col, ascending=(agg_method=='min')).head(20)
            
            fig_main = px.bar(top_df, x=value_col, y=display_col, orientation='h', template="plotly_white", 
                              color_discrete_sequence=['#4285F4' if is_gsc else '#34A853'])
            if is_ranking: fig_main.update_layout(xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_main, use_container_width=True, key="main_leaderboard_unique")

    st.divider()

    # --- STRATEGIC AI REPORT (GEMINI) ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Gemini is analyzing (respecting rate limits)..."):
            st.session_state.ai_report = get_ai_insight(tab_df, sel_tab)
    if "ai_report" in st.session_state:
        st.info(st.session_state.ai_report)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)
    item_col = page_col if (page_col and "PAGE" in sel_tab.upper()) else metric_name_col

    if item_col in tab_df.columns and date_col in tab_df.columns:
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col in tab_df.columns else [None]

        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"## Region: {loc if loc else 'Global'}")
            top_region_items = loc_data.groupby(item_col)[value_col].sum().sort_values(ascending=False).head(10).index.tolist()

            for i, item in enumerate(top_region_items):
                item_data = loc_data[loc_data[item_col] == item].sort_values('dt')
                
                with st.expander(f"Data for: {item} | Total: {item_data[value_col].sum()}", expanded=(loc == 'Germany')):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        fig = px.line(item_data, x='dt', y=value_col, markers=True, height=350, title=f"Trend: {item}")
                        
                        if show_forecast and len(item_data) >= 3:
                            f_in = item_data.rename(columns={value_col: 'Value', 'dt': 'ds'})
                            forecast = get_prediction(f_in)
                            if forecast is not None:
                                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Projection', line=dict(color='orange', dash='dash')))
                        
                        if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed"))
                        # UNIQUE KEY FIX
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_{loc}_{i}_{item}")
                    
                    with col2:
                        st.write("Monthly Stats")
                        table_view = item_data[['dt', value_col]].copy()
                        table_view['dt'] = table_view['dt'].dt.strftime('%b %Y')
                        st.dataframe(table_view, hide_index=True)

    # --- CHAT WITH DATA (GROK) ---
    st.sidebar.divider()
    st.sidebar.subheader("💬 Chat with Data")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.sidebar.button("🗑️ Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

    for chat in st.session_state.chat_history:
        with st.sidebar.chat_message(chat["role"]):
            st.write(chat["content"])

    if user_input := st.sidebar.chat_input("Ask about the numbers..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.sidebar.chat_message("user"):
            st.write(user_input)

        try:
            client = Groq(api_key=GROQ_KEY)
            summary_df = tab_df.groupby([loc_col, tab_df[date_col].dt.strftime('%Y-%m')])[value_col].sum().reset_index()
            context_str = summary_df.to_string(index=False)

            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": f"You are a concise Data Assistant. Use this summary table:\n{context_str}\n\nRULES: 1. Be brief. 2. Give exact numbers. 3. Use history for follow-ups."},
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
