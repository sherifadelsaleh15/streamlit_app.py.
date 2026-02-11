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
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICK' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    kw_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
    
    value_col = click_col if click_col else next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VALUE', 'VIEWS'])), None)
    date_col = 'dt'
    
    # Check if we are in GSC mode
    is_gsc = "GSC" in sel_tab.upper()

    # --- SIDEBAR FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- MAIN CONTENT ---
    st.title(f"Strategic View: {sel_tab}")

    # --- CENTERED LEADERBOARDS ---
    L, M, R = st.columns([1, 4, 1])
    with M:
        if is_gsc and kw_col and click_col and pos_col:
            st.subheader("Top 20 Keywords: Clicks & Avg Position")
            top_df = tab_df.groupby(kw_col).agg({click_col: 'sum', pos_col: 'mean'}).reset_index()
            top_df = top_df.sort_values(by=click_col, ascending=False).head(20)
            
            # Dual Axis Chart for Clicks (Bar) and Position (Line)
            fig_gsc = go.Figure()
            fig_gsc.add_trace(go.Bar(x=top_df[kw_col], y=top_df[click_col], name="Clicks", marker_color='#4285F4', yaxis='y1'))
            fig_gsc.add_trace(go.Scatter(x=top_df[kw_col], y=top_df[pos_col], name="Avg Position", line=dict(color='#DB4437', width=3), yaxis='y2'))
            
            fig_gsc.update_layout(
                template="plotly_white",
                yaxis=dict(title="Total Clicks", side="left"),
                yaxis2=dict(title="Avg Position", side="right", overlaying="y", autorange="reversed"),
                legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
            )
            st.plotly_chart(fig_gsc, use_container_width=True)
        else:
            # Maintain standard bar chart for GA4/Other tabs
            display_col = page_col if page_col else kw_col
            if display_col and value_col:
                st.subheader(f"Top 20 {display_col} by {value_col}")
                top_gen = tab_df.groupby(display_col)[value_col].sum().reset_index().sort_values(by=value_col, ascending=True).tail(20)
                fig_gen = px.bar(top_gen, x=value_col, y=display_col, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'])
                st.plotly_chart(fig_gen, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."):
            st.session_state.ai_report = get_ai_insight(tab_df, sel_tab)
    if "ai_report" in st.session_state and st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS (REGION > KEYWORD/PAGE) ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)
    item_col = kw_col if is_gsc else (page_col if page_col else kw_col)

    if item_col and value_col and date_col in tab_df.columns:
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]

        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"## Region: {loc if loc else 'Global'}")
            
            # Find Top 10 items for THIS region
            region_top = loc_data.groupby(item_col)[value_col].sum().sort_values(ascending=False).head(10).index.tolist()

            for item in region_top:
                item_data = loc_data[loc_data[item_col] == item].sort_values('dt')
                
                with st.expander(f"Data for: {item} | Total {value_col}: {item_data[value_col].sum()}", expanded=(loc == 'Germany')):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # GSC gets a dual line chart for Clicks vs Position
                        fig = px.line(item_data, x='dt', y=click_col if is_gsc else value_col, markers=True, height=350, title=f"Trend: {item}")
                        
                        if is_gsc and pos_col in item_data.columns:
                            fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[pos_col], name="Position", yaxis="y2", line=dict(dash='dot', color='#DB4437')))
                            fig.update_layout(yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"))

                        if show_forecast and len(item_data) >= 3:
                            f_in = item_data.rename(columns={value_col: 'Value', 'dt': 'ds'})
                            forecast = get_prediction(f_in)
                            if forecast is not None:
                                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Projection', line=dict(color='orange', dash='dash')))
                        
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_{loc}_{item}")
                    
                    with col2:
                        st.write("Monthly Stats")
                        table_view = item_data[['dt', click_col, pos_col]].dropna(axis=1).copy() if is_gsc else item_data[['dt', value_col]].copy()
                        table_view['dt'] = table_view['dt'].dt.strftime('%b %Y')
                        st.dataframe(table_view, hide_index=True)
