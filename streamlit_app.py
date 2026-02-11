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

# --- AI HELPER ---
def get_ai_insight(df, tab_name):
    try:
        data_summary = df.head(15).to_string()
        genai.configure(api_key=GEMINI_KEY)
        # Fix for 404 Error: Using 2026 stable endpoints
        model_options = ['gemini-2.0-flash', 'gemini-3-flash-preview']
        for m_name in model_options:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(f"Analyze {tab_name} performance:\n{data_summary}")
                return response.text
            except: continue
        return "AI Error: Model not responding."
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
    
    # Generic Column Detection
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'LOCATION'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICK' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
    
    # Universal Value Assignment
    value_col = click_col if click_col else next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VALUE', 'VIEWS'])), None)
    name_col = kw_col if (is_gsc or kw_col) else page_col
    date_col = 'dt'

    # --- SIDEBAR FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- SIDEBAR: CHAT ---
    st.sidebar.divider()
    st.sidebar.subheader("Chat with Data")
    user_q = st.sidebar.text_input("Ask a question about this data:", key="user_input")
    if user_q:
        client = Groq(api_key=GROQ_KEY)
        ans = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Tab: {sel_tab}. Q: {user_q}"}])
        st.sidebar.info(ans.choices[0].message.content)

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")

    # --- CENTERED LEADERBOARDS ---
    L, M, R = st.columns([1, 4, 1])
    with M:
        if is_gsc and kw_col and click_col and pos_col:
            st.subheader("Top 20 Keywords: Clicks & Avg Position")
            kw_perf = tab_df.groupby(kw_col).agg({click_col: 'sum', pos_col: 'mean'}).reset_index()
            kw_perf = kw_perf.sort_values(by=click_col, ascending=False).head(20)
            
            fig_gsc = go.Figure()
            fig_gsc.add_trace(go.Bar(x=kw_perf[kw_col], y=kw_perf[click_col], name="Clicks", marker_color='#4285F4', yaxis='y1'))
            fig_gsc.add_trace(go.Scatter(x=kw_perf[kw_col], y=kw_perf[pos_col], name="Avg Position", line=dict(color='#DB4437', width=3), yaxis='y2'))
            fig_gsc.update_layout(template="plotly_white", yaxis=dict(title="Clicks"), 
                                  yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"),
                                  legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_gsc, use_container_width=True)

        elif name_col and value_col:
            st.subheader(f"Top Performance View: {name_col}")
            top_gen = tab_df.groupby(name_col)[value_col].sum().reset_index().sort_values(by=value_col, ascending=True).tail(20)
            fig_gen = px.bar(top_gen, x=value_col, y=name_col, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'], text=value_col)
            st.plotly_chart(fig_gen, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."): st.markdown(get_ai_insight(tab_df, sel_tab))

    st.divider()

    # --- TRENDS: BRANCHED BY GSC VS OTHERS ---
    if is_gsc:
        st.subheader("Monthly Performance Trends (By Keyword)")
        top_items = tab_df.groupby(kw_col)[click_col].sum().sort_values(ascending=False).head(20).index.tolist()
        
        for item in top_items:
            item_data = tab_df[tab_df[kw_col] == item].sort_values('dt')
            with st.expander(f"Keyword Trend: {item}"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    fig_k = px.line(item_data, x='dt', y=click_col, markers=True)
                    if pos_col in item_data.columns:
                        fig_k.add_trace(go.Scatter(x=item_data['dt'], y=item_data[pos_col], name="Position", yaxis="y2", line=dict(dash='dot')))
                        fig_k.update_layout(yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"))
                    st.plotly_chart(fig_k, use_container_width=True, key=f"k_tr_{item}")
                with c2:
                    st.dataframe(item_data[['dt', click_col, pos_col]].dropna(axis=1), hide_index=True)
    else:
        st.subheader("Monthly Performance Trends (By Region)")
        if loc_col and value_col and date_col in tab_df.columns:
            loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany')
            for loc in loc_list:
                loc_data = tab_df[tab_df[loc_col] == loc].sort_values('dt')
                with st.expander(f"Region Trend: {loc}", expanded=(loc == 'Germany')):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        fig_loc = px.line(loc_data.groupby('dt')[value_col].sum().reset_index(), x='dt', y=value_col, markers=True)
                        st.plotly_chart(fig_loc, use_container_width=True, key=f"loc_tr_{loc}")
                    with c2:
                        st.write("Regional Stats")
                        st.dataframe(loc_data.groupby('dt')[value_col].sum().reset_index(), hide_index=True)

else:
    st.info("Please select a dashboard section to view data.")
