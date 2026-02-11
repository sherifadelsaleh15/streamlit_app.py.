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
    is_gsc = "GSC" in sel_tab.upper() or "POSITION" in sel_tab.upper()
    
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    
    # Specific SEO Columns
    click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    
    # Logic for choosing primary value
    if is_gsc and click_col:
        value_col = click_col
    else:
        value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['SESSIONS', 'USERS', 'VALUE', 'VIEWS', 'CLICKS'])), None)
    
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
    date_col = 'dt'
    
    is_ranking = value_col and ('POSITION' in value_col.upper() or 'RANK' in value_col.upper())

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
        display_col = page_col if (page_col and "PAGE" in sel_tab.upper()) else metric_name_col
        if display_col and value_col:
            st.subheader(f"Top 20 {display_col} by {value_col}")
            agg_method = 'min' if is_ranking else 'sum'
            top_df = tab_df.groupby(display_col)[value_col].agg(agg_method).reset_index()
            top_df = top_df.sort_values(by=value_col, ascending=(agg_method=='min')).head(20)
            
            fig_main = px.bar(top_df, x=value_col, y=display_col, orientation='h', template="plotly_white", 
                              color_discrete_sequence=['#4285F4' if is_gsc else '#34A853'])
            if is_ranking: fig_main.update_layout(xaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_main, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."):
            st.session_state.ai_report = get_ai_insight(tab_df, sel_tab)
    if "ai_report" in st.session_state and st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)
    
    item_col = page_col if (page_col and "PAGE" in sel_tab.upper()) else metric_name_col

    if item_col and value_col and date_col in tab_df.columns:
        loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]

        for loc in loc_list:
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"## Region: {loc if loc else 'Global'}")
            
            top_region_items = (
                loc_data.groupby(item_col)[value_col]
                .sum()
                .sort_values(ascending=False if not is_ranking else True)
                .head(10)
                .index.tolist()
            )

            for item in top_region_items:
                item_data = loc_data[loc_data[item_col] == item].sort_values('dt')
                
                # Dynamic Expander Label
                if is_gsc and pos_col:
                    label = f"Keyword: {item} | Clicks: {item_data[click_col].sum()} | Avg Pos: {round(item_data[pos_col].mean(), 1)}"
                else:
                    label = f"Data for: {item} | Total {value_col}: {item_data[value_col].sum()}"

                with st.expander(label, expanded=(loc == 'Germany')):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if is_gsc and pos_col and click_col:
                            # --- GSC DUAL AXIS CHART ---
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[click_col], name="Clicks", line=dict(color='#4285F4', width=3)))
                            fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[pos_col], name="Avg Position", yaxis="y2", line=dict(color='#DB4437', dash='dot')))
                            
                            fig.update_layout(
                                template="plotly_white",
                                yaxis=dict(title="Clicks", titlefont=dict(color="#4285F4"), tickfont=dict(color="#4285F4")),
                                yaxis2=dict(title="Position", titlefont=dict(color="#DB4437"), tickfont=dict(color="#DB4437"), 
                                            overlaying="y", side="right", autorange="reversed"),
                                legend=dict(orientation="h", y=1.1)
                            )
                        else:
                            # --- STANDARD PERFORMANCE CHART ---
                            fig = px.line(item_data, x='dt', y=value_col, markers=True, height=350, title=f"Trend: {item}")
                            if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed"))
                        
                        # Forecast Logic (Applied to Primary Value)
                        if show_forecast and len(item_data) >= 3:
                            f_in = item_data.rename(columns={value_col: 'Value', 'dt': 'ds'})
                            forecast = get_prediction(f_in)
                            if forecast is not None:
                                fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Projection', line=dict(color='orange', dash='dash')))
                        
                        st.plotly_chart(fig, use_container_width=True, key=f"trend_{loc}_{item}")
                    
                    with col2:
                        st.write("Monthly Stats")
                        cols_to_show = ['dt', value_col]
                        if is_gsc and pos_col: cols_to_show.append(pos_col)
                        
                        table_view = item_data[cols_to_show].copy()
                        table_view['dt'] = table_view['dt'].dt.strftime('%b %Y')
                        st.dataframe(table_view, hide_index=True)
