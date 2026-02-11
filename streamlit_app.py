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
                response = model.generate_content(f"Analyze: {tab_name} data:\n{data_summary}")
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
    # --- DETECTION LOGIC ---
    is_gsc = "GSC" in sel_tab.upper()
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICK' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
    
    # Universal Metrics
    value_col = click_col if is_gsc else next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VIEWS', 'VALUE'])), None)
    item_col = kw_col if is_gsc else (page_col if page_col else kw_col)
    date_col = 'dt'

    # --- SIDEBAR FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")

    L, M, R = st.columns([1, 4, 1])
    with M:
        if item_col and value_col:
            st.subheader(f"Top 20 {item_col} Performance")
            top_main = tab_df.groupby(item_col)[value_col].sum().reset_index().sort_values(by=value_col, ascending=True).tail(20)
            fig_main = px.bar(top_main, x=value_col, y=item_col, orientation='h', template="plotly_white", 
                              color_discrete_sequence=['#4285F4' if is_gsc else '#34A853'], text=value_col)
            st.plotly_chart(fig_main, use_container_width=True)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)

    if loc_col and item_col and value_col and date_col in tab_df.columns:
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany')
        
        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc]
            st.markdown(f"## Region: {loc}")
            
            # Find top 10 items for THIS region
            top_region_items = loc_data.groupby(item_col)[value_col].sum().sort_values(ascending=False).head(10).index.tolist()

            for item in top_region_items:
                item_data = loc_data[loc_data[item_col] == item].sort_values('dt')
                
                # Format label: GSC shows Clicks + Avg Pos, GA4 shows Views
                label_suffix = f"Clicks: {item_data[click_col].sum()} | Avg Pos: {round(item_data[pos_col].mean(), 1)}" if is_gsc else f"Views: {item_data[value_col].sum()}"
                
                with st.expander(f"{item} | {label_suffix}", expanded=(loc == 'Germany')):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        # Dual Axis for GSC
                        if is_gsc and pos_col:
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[click_col], name="Clicks", line=dict(color='#4285F4', width=4)))
                            fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[pos_col], name="Position", yaxis="y2", line=dict(color='#DB4437', dash='dot')))
                            fig.update_layout(
                                template="plotly_white",
                                yaxis=dict(title="Clicks"),
                                yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"),
                                legend=dict(orientation="h", y=1.1)
                            )
                        else:
                            # Standard Line for GA4
                            fig = px.line(item_data, x='dt', y=value_col, markers=True, template="plotly_white")
                        
                        st.plotly_chart(fig, use_container_width=True, key=f"tr_{loc}_{item}")
                    
                    with c2:
                        st.write("Monthly Detail")
                        st.dataframe(item_data[['dt', value_col] + ([pos_col] if is_gsc else [])].assign(dt=lambda x: x['dt'].dt.strftime('%b %Y')), hide_index=True)
