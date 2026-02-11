import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
        # Updated 2026 Model Endpoints to fix 404 error
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
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    # Priority for Clicks in GSC
    click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
    value_col = click_col if click_col else next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'
    is_ranking = value_col and 'POSITION' in value_col.upper()

    # --- SIDEBAR FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- SIDEBAR: CHAT WITH DATA ---
    st.sidebar.divider()
    st.sidebar.subheader("Chat with Data")
    user_q = st.sidebar.text_input("Ask a question about this data:", key="user_input")
    if user_q:
        client = Groq(api_key=GROQ_KEY)
        ans = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {sel_tab}. Q: {user_q}"}])
        st.sidebar.info(ans.choices[0].message.content)

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")

    # --- CENTERED LEADERBOARDS ---
    L, M, R = st.columns([1, 4, 1])
    with M:
        if "GSC" in sel_tab.upper() and metric_name_col and value_col:
            st.subheader(f"Top 20 Keywords by {value_col.replace('_', ' ')}")
            top_k = tab_df.groupby(metric_name_col)[value_col].sum().reset_index()
            # Sort ascending for Plotly horizontal bottom-to-top rendering
            top_k = top_k.sort_values(by=value_col, ascending=True).tail(20)
            fig_k = px.bar(top_k, x=value_col, y=metric_name_col, orientation='h', template="plotly_white", color_discrete_sequence=['#4285F4'], text=value_col)
            fig_k.update_traces(textposition='outside')
            st.plotly_chart(fig_k, use_container_width=True)

        if any(x in sel_tab.upper() for x in ["GA4", "PAGE", "DATA"]) and (page_col or metric_name_col) and value_col:
            st.subheader("Top Performance View")
            p_col = page_col if page_col else metric_name_col
            top_p = tab_df.groupby(p_col)[value_col].sum().reset_index().sort_values(by=value_col, ascending=True).tail(20)
            fig_p = px.bar(top_p, x=value_col, y=p_col, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'], text=value_col)
            fig_p.update_traces(textposition='outside')
            st.plotly_chart(fig_p, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if "ai_report" not in st.session_state: st.session_state.ai_report = ""
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."): st.session_state.ai_report = get_ai_insight(tab_df, sel_tab)
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)
    trend_col = metric_name_col if metric_name_col else page_col

    if trend_col and value_col and date_col in tab_df.columns:
        agg_sort = 'min' if is_ranking else 'sum'
        top_items = tab_df.groupby(trend_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]

        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"### Region: {loc if loc else 'Global'}")
            for item in [i for i in top_items if i in loc_data[trend_col].unique()]:
                item_data = loc_data[loc_data[trend_col] == item].sort_values('dt')
                with st.expander(f"Data for: {item} in {loc}", expanded=(loc == 'Germany')):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        fig = px.line(item_data, x='dt', y=value_col, markers=True, height=350)
                        if show_forecast and len(item_data) >= 3:
                            f = get_prediction(item_data.rename(columns={value_col: 'Value', 'dt': 'ds'}))
                            if f is not None: fig.add_trace(go.Scatter(x=f['ds'], y=f['yhat'], mode='lines', name='Projection', line=dict(color='orange', dash='dash')))
                        if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(fig, use_container_width=True, key=f"ch_{item}_{loc}")
                    with c2:
                        st.dataframe(item_data[['dt', value_col]].assign(dt=lambda x: x['dt'].dt.strftime('%b %Y')), hide_index=True)
