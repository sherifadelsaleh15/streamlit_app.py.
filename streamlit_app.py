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
                response = model.generate_content(f"Strategic Analyst. Analyze {tab_name} data:\n{data_summary}")
                return response.text
            except Exception: continue
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
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'
    is_ranking = value_col and 'POSITION' in value_col.upper()

    # --- SIDEBAR FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")

    L, M, R = st.columns([1, 4, 1])
    with M:
        # Top chart logic (remains centered)
        p_col = page_col if page_col else metric_name_col
        if p_col and value_col:
            st.subheader(f"Top 20 {p_col} by {value_col}")
            top_p = tab_df.groupby(p_col)[value_col].sum().reset_index().sort_values(by=value_col, ascending=True).tail(20)
            fig_p = px.bar(top_p, x=value_col, y=p_col, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'], text=value_col)
            st.plotly_chart(fig_p, use_container_width=True)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS (BY REGION -> BY PAGE) ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)
    
    # Identify which column represents the "Page" or "Keyword"
    trend_item_col = page_col if page_col else metric_name_col

    if trend_item_col and value_col and date_col in tab_df.columns:
        # Get regions (Germany first)
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]

        for loc in loc_list:
            # 1. Filter data to ONLY this region
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            
            st.markdown(f"## Region: {loc if loc else 'Global'}")
            
            # 2. Find the top 10 most visited pages/items ONLY for this region
            top_pages_in_region = (
                loc_data.groupby(trend_item_col)[value_col]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .index.tolist()
            )

            # 3. Create an expander for each of those top pages
            for page in top_pages_in_region:
                page_data = loc_data[loc_data[trend_item_col] == page].sort_values(date_col)
                
                with st.expander(f"📊 {page} ({value_col}: {page_data[value_col].sum()})", expanded=False):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        fig = px.line(page_data, x=date_col, y=value_col, markers=True, height=300, title=f"Trend for {page}")
                        if show_forecast and len(page_data) >= 3:
                            f_in = page_data.rename(columns={value_col: 'Value', date_col: 'ds'})
                            forecast = get_prediction(f_in)
                            if forecast is not None:
                                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='AI Projection', line=dict(color='orange', dash='dash')))
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_{loc}_{page}")
                    
                    with c2:
                        st.write("Monthly Breakdown")
                        display_df = page_data[[date_col, value_col]].copy()
                        display_df[date_col] = display_df[date_col].dt.strftime('%b %Y')
                        st.dataframe(display_df, hide_index=True)
            st.write("---") # Visual separator between regions

else:
    st.info("No data available for the selected view.")
