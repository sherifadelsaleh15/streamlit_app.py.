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
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"Senior Strategic Analyst. Analyze: {tab_name} data:\n{data_summary}")
        return response.text
    except Exception as e: return f"AI Error: {str(e)}"

# --- TAB SPECIFIC RENDERERS ---

def render_gsc_tab(df, tab_name):
    """Isolated logic for GSC: Region > Keyword > Clicks & Position Charts"""
    st.title(f"Search Console Strategy: {tab_name}")
    
    # Identify Columns
    loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
    kw_col = next((c for c in df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD'])), None)
    click_col = next((c for c in df.columns if 'CLICK' in c.upper()), None)
    pos_col = next((c for c in df.columns if 'POSITION' in c.upper()), None)
    date_col = 'dt'

    if not all([loc_col, kw_col, click_col, pos_col]):
        st.error("GSC Columns missing (Clicks, Position, or Keyword)")
        return

    # Filter Regions
    all_locs = sorted(df[loc_col].dropna().unique().tolist())
    sel_locs = st.sidebar.multiselect(f"Filter Regions ({tab_name})", all_locs, default=all_locs)
    df = df[df[loc_col].isin(sel_locs)]

    # 1. Top 20 Global Keywords for this tab
    top_20 = df.groupby(kw_col)[click_col].sum().sort_values(ascending=True).tail(20).reset_index()
    fig_main = px.bar(top_20, x=click_col, y=kw_col, orientation='h', title="Top Keywords by Clicks", template="plotly_white", color_discrete_sequence=['#4285F4'])
    st.plotly_chart(fig_main, use_container_width=True)

    st.divider()
    st.subheader("Monthly Performance Trends (Region > Keywords)")
    
    # 2. Loop through Regions
    loc_list = sorted([str(x) for x in df[loc_col].unique()], key=lambda x: x != 'Germany')
    for loc in loc_list:
        st.markdown(f"## Region: {loc}")
        loc_data = df[df[loc_col] == loc]
        
        # Get Top 10 Keywords for THIS Region
        top_kws = loc_data.groupby(kw_col)[click_col].sum().sort_values(ascending=False).head(10).index.tolist()
        
        for kw in top_kws:
            kw_data = loc_data[loc_data[kw_col] == kw].sort_values(date_col)
            label = f"Keyword: {kw} | Clicks: {kw_data[click_col].sum()} | Avg Pos: {round(kw_data[pos_col].mean(), 1)}"
            
            with st.expander(label, expanded=(loc == 'Germany')):
                c1, c2 = st.columns([3, 1])
                with c1:
                    fig = go.Figure()
                    # Left Axis: Clicks
                    fig.add_trace(go.Scatter(x=kw_data[date_col], y=kw_data[click_col], name="Clicks", line=dict(color='#4285F4', width=3)))
                    # Right Axis: Position
                    fig.add_trace(go.Scatter(x=kw_data[date_col], y=kw_data[pos_col], name="Position", yaxis="y2", line=dict(color='#DB4437', dash='dot')))
                    
                    fig.update_layout(
                        template="plotly_white",
                        yaxis=dict(title="Clicks"),
                        yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"),
                        legend=dict(orientation="h", y=1.1)
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"gsc_{loc}_{kw}")
                with c2:
                    st.write("Monthly Stats")
                    st.dataframe(kw_data[[date_col, click_col, pos_col]].assign(dt=lambda x: x[date_col].dt.strftime('%b %Y')), hide_index=True)

def render_ga4_tab(df, tab_name):
    """Original stable logic for GA4/Pages"""
    st.title(f"GA4 Performance: {tab_name}")
    # ... (Your existing working logic for GA4 goes here)
    # Keeping it simple for this demonstration
    st.write("GA4 Content Loaded")
    st.dataframe(df.head())

# --- MAIN APP LOGIC ---

if "password_correct" not in st.session_state:
    st.subheader("Strategy Login")
    pwd = st.text_input("Enter Key", type="password")
    if st.button("Submit"):
        if pwd == "strategic_2026":
            st.session_state["password_correct"] = True
            st.rerun()
    st.stop()

try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data loading failed: {e}"); st.stop()

sel_tab = st.sidebar.selectbox("Dashboard Section", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # ROUTING: Choose the specialized code based on the tab name
    if "GSC" in sel_tab.upper():
        render_gsc_tab(tab_df, sel_tab)
    else:
        # Default/GA4 Logic
        # (This is where your existing general code lives to maintain its settings)
        st.title(f"Strategic View: {sel_tab}")
        # ... rest of your original generic code ...
        st.info("Generic GA4/Page logic rendering...")
        st.dataframe(tab_df.head())
