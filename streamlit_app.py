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
    # --- UNIVERSAL COLUMN DETECTION ---
    # Metric (Y-Axis)
    click_col = next((c for c in tab_df.columns if 'CLICK' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    value_col = click_col if click_col else next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VALUE', 'VIEWS', 'FOLLOWERS'])), None)
    
    # Label (X-Axis)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'PAGE', 'URL', 'METRIC', 'PLATFORM'])), None)
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'LOCATION'])), None)
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
        # SPECIAL CASE: GSC (Keyword + Clicks + Position)
        if "GSC" in sel_tab.upper() and metric_name_col and click_col and pos_col:
            st.subheader("Keyword Performance: Clicks vs. Avg Position")
            kw_perf = tab_df.groupby(metric_name_col).agg({click_col: 'sum', pos_col: 'mean'}).reset_index()
            kw_perf = kw_perf.sort_values(by=click_col, ascending=False).head(20)
            
            fig_gsc = go.Figure()
            fig_gsc.add_trace(go.Bar(x=kw_perf[metric_name_col], y=kw_perf[click_col], name="Clicks", marker_color='#4285F4', yaxis='y1'))
            fig_gsc.add_trace(go.Scatter(x=kw_perf[metric_name_col], y=kw_perf[pos_col], name="Avg Position", line=dict(color='#DB4437', width=3), yaxis='y2'))
            fig_gsc.update_layout(template="plotly_white", yaxis=dict(title="Clicks"), 
                                  yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"),
                                  legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_gsc, use_container_width=True)

        # GENERAL CASE: All other sheets (GA4, Social, Feed)
        elif metric_name_col and value_col:
            st.subheader(f"Top 20 {metric_name_col.replace('_', ' ')} by {value_col.replace('_', ' ')}")
            is_ranking = 'POSITION' in value_col.upper() or 'RANK' in value_col.upper()
            agg_type = 'mean' if is_ranking else 'sum'
            
            top_gen = tab_df.groupby(metric_name_col)[value_col].agg(agg_type).reset_index()
            top_gen = top_gen.sort_values(by=value_col, ascending=is_ranking).head(20)
            
            fig_gen = px.bar(top_gen.iloc[::-1], x=value_col, y=metric_name_col, orientation='h', 
                             template="plotly_white", color_discrete_sequence=['#34A853'], text=value_col)
            if is_ranking: fig_gen.update_layout(xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_gen, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."): st.markdown(get_ai_insight(tab_df, sel_tab))

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader(f"Monthly Performance Trends (Top {metric_name_col if metric_name_col else 'Items'})")
    if metric_name_col and value_col and date_col in tab_df.columns:
        is_pos = 'POSITION' in value_col.upper()
        top_items = tab_df.groupby(metric_name_col)[value_col].agg('mean' if is_pos else 'sum').sort_values(ascending=is_pos).head(20).index.tolist()
        
        # Display regional groupings if region exists
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]

        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"### Group: {loc if loc else 'Global'}")
            
            for item in [i for i in top_items if i in loc_data[metric_name_col].unique()]:
                item_data = loc_data[loc_data[metric_name_col] == item].sort_values('dt')
                with st.expander(f"Trend for: {item}"):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        fig_tr = px.line(item_data, x='dt', y=value_col, markers=True, title=f"{item} Trend")
                        if is_pos: fig_tr.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(fig_tr, use_container_width=True, key=f"tr_{item}_{loc}")
                    with c2:
                        st.dataframe(item_data[['dt', value_col]].assign(dt=lambda x: x['dt'].dt.strftime('%b %Y')), hide_index=True)

else:
    st.info("No data detected. Please check your source sheet.")
