import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import google.generativeai as genai
from groq import Groq

# Zero-indentation imports
from modules.data_loader import load_and_preprocess_data
from modules.ml_models import generate_forecast

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# Safe PDF Support
try:
    from fpdf import FPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# API KEYS
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# --- HELPER FUNCTIONS ---
def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        data_summary = df.head(15).to_string()
        system_msg = "Senior Strategic Analyst. Compare performance across regions and provide implications."
        user_msg = f"Tab: {tab_name}\nQuestion: {custom_prompt if custom_prompt else 'Analyze regional performance'}"

        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            # Use 1.5-flash and pro as fallbacks to avoid 404s
            for model_name in ['gemini-1.5-flash', 'gemini-pro']:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(f"{system_msg}\n{user_msg}\nData:\n{data_summary}")
                    return response.text
                except Exception:
                    continue
            return "Gemini unreachable."
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": f"{user_msg}\nData:\n{data_summary}"}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# 2. Authentication
if "password_correct" not in st.session_state:
    st.subheader("Strategy Login")
    pwd = st.text_input("Enter Key", type="password")
    if st.button("Submit"):
        if pwd == "strategic_2026":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Denied")
    st.stop()

# 3. Data Loading
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data loading failed: {e}")
    st.stop()

# 4. Sidebar Navigation & Filtering
sel_tab = st.sidebar.selectbox("Dashboard Section", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

# Restore Original Country/Region Filtering
loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)

if loc_col and not tab_df.empty:
    all_locs = sorted(tab_df[loc_col].unique().tolist())
    # Default to Germany if present, else all
    default_locs = [l for l in all_locs if l == 'Germany'] or all_locs
    selected_locs = st.sidebar.multiselect(f"Filter by {loc_col}", all_locs, default=default_locs)
    tab_df = tab_df[tab_df[loc_col].isin(selected_locs)]

# 5. Main Dashboard Layout (Restored Charts)
st.title(f"Strategic View: {sel_tab}")

if not tab_df.empty:
    # Identify Metrics and Dimensions
    val_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'VALUE', 'VALUE_POSITION'])), None)
    name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'METRIC'])), None)

    # Metric Row (Summary)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Count", len(tab_df))
    with col2:
        if val_col:
            st.metric(f"Total {val_col.replace('_', ' ')}", f"{tab_df[val_col].sum():,.0f}")
    with col3:
        if loc_col:
            st.metric("Active Regions", len(selected_locs))

    st.divider()

    # Regional Breakdown Chart (The Donut Chart)
    if loc_col and val_col:
        st.subheader("Performance by Region/Country")
        reg_df = tab_df.groupby(loc_col)[val_col].sum().reset_index()
        fig_reg = px.pie(reg_df, values=val_col, names=loc_col, hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_reg, use_container_width=True)

    # Metric Comparison Chart (Grouped Bar Chart)
    if val_col and name_col:
        st.subheader(f"Top 15 {name_col.replace('_', ' ')} by {val_col.replace('_', ' ')}")
        # Grouping by both metric name and country to see them side-by-side
        top_df = tab_df.groupby([name_col, loc_col])[val_col].sum().reset_index()
        fig_bar = px.bar(top_df.nlargest(15, val_col), x=val_col, y=name_col, 
                         color=loc_col, orientation='h', barmode='group')
        st.plotly_chart(fig_bar, use_container_width=True)

    # Forecast Section
    if val_col and 'dt' in tab_df.columns:
        st.divider()
        st.subheader("3-Month Strategic Forecast")
        forecast_df = generate_forecast(tab_df, val_col)
        if not forecast_df.empty:
            fig_trend = go.Figure()
            hist_df = tab_df.groupby('dt')[val_col].sum().reset_index()
            fig_trend.add_trace(go.Scatter(x=hist_df['dt'], y=hist_df[val_col], name="Historical"))
            fig_trend.add_trace(go.Scatter(x=forecast_df['dt'], y=forecast_df[val_col], name="Forecast", line=dict(dash='dash')))
            st.plotly_chart(fig_trend, use_container_width=True)

    # AI Insight Section
    st.divider()
    if st.button("Generate Regional Analysis"):
        with st.spinner("Analyzing..."):
            report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.markdown(report)
else:
    st.warning("No data available for the selected filters.")
