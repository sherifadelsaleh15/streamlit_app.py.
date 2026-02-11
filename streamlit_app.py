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
        model_options = ['gemini-2.0-flash', 'gemini-3-flash-preview']
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
    # --- SPECIFIC COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'LOCATION'])), None)
    
    # Identify Clicks AND Position for GSC
    click_col = next((c for c in tab_df.columns if 'CLICK' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    date_col = 'dt'

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
        if "GSC" in sel_tab.upper() and kw_col and click_col and pos_col:
            st.subheader("Keyword Performance: Clicks vs. Avg Position")
            
            # Aggregate data by Keyword
            kw_perf = tab_df.groupby(kw_col).agg({click_col: 'sum', pos_col: 'mean'}).reset_index()
            # Sort by Top Clicks
            kw_perf = kw_perf.sort_values(by=click_col, ascending=False).head(20)

            # Create a Dual-Metric Chart (Bar for Clicks, Line for Position)
            fig_gsc = go.Figure()
            # Bars for Clicks
            fig_gsc.add_trace(go.Bar(x=kw_perf[kw_col], y=kw_perf[click_col], name="Clicks", marker_color='#4285F4', yaxis='y1'))
            # Line for Position
            fig_gsc.add_trace(go.Scatter(x=kw_perf[kw_col], y=kw_perf[pos_col], name="Avg Position", line=dict(color='#DB4437', width=3), yaxis='y2'))

            fig_gsc.update_layout(
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(title="Total Clicks", side="left"),
                yaxis2=dict(title="Avg Position", side="right", overlaying="y", autorange="reversed"),
                margin=dict(l=20, r=20, t=50, b=100)
            )
            st.plotly_chart(fig_gsc, use_container_width=True)
        
        elif any(x in sel_tab.upper() for x in ["GA4", "PAGE", "DATA"]):
            # Standard GA4 Leaderboard if not GSC
            val_col = click_col if click_col else next((c for c in tab_df.columns if 'SESSIONS' in c.upper() or 'VIEWS' in c.upper()), None)
            name_col = kw_col if kw_col else next((c for c in tab_df.columns if 'PAGE' in c.upper()), None)
            if name_col and val_col:
                top_ga4 = tab_df.groupby(name_col)[val_col].sum().reset_index().sort_values(by=val_col, ascending=True).tail(20)
                fig_ga4 = px.bar(top_ga4, x=val_col, y=name_col, orientation='h', color_discrete_sequence=['#34A853'], template="plotly_white")
                st.plotly_chart(fig_ga4, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."): st.write(get_ai_insight(tab_df, sel_tab))

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS (BY KEYWORD) ---
    st.subheader("Monthly Performance Trends (Top Keywords)")
    if kw_col and click_col and date_col in tab_df.columns:
        # Get top 20 keywords globally for the charts
        top_k_list = tab_df.groupby(kw_col)[click_col].sum().sort_values(ascending=False).head(20).index.tolist()
        
        # Display Trends
        for kw in top_k_list:
            kw_data = tab_df[tab_df[kw_col] == kw].sort_values('dt')
            with st.expander(f"Trend for: {kw}"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    fig_trend = px.line(kw_data, x='dt', y=click_col, markers=True, title=f"Clicks Trend: {kw}")
                    if pos_col in kw_data.columns:
                        fig_trend.add_trace(go.Scatter(x=kw_data['dt'], y=kw_data[pos_col], name="Position", yaxis="y2", line=dict(dash='dot')))
                        fig_trend.update_layout(yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"))
                    st.plotly_chart(fig_trend, use_container_width=True, key=f"trend_{kw}")
                with c2:
                    st.write("Metric Details")
                    st.dataframe(kw_data[['dt', click_col, pos_col]].dropna(axis=1), hide_index=True)

else:
    st.info("No data found. Please check your Google Sheet connection.")
