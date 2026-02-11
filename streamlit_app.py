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

# Safe PDF Library Import
try:
    from fpdf import FPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# API KEYS
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# --- HELPER FUNCTIONS ---

def generate_pdf(report_text, tab_name):
    if not PDF_SUPPORT:
        return None
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"Strategic Report: {tab_name}", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        clean_text = report_text.encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(0, 10, txt=clean_text)
        return pdf.output(dest='S').encode('latin-1')
    except Exception:
        return None

def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        data_summary = df.head(15).to_string()
        system_msg = "Senior Strategic Analyst. Provide business implications and regional comparisons."
        user_msg = f"Tab: {tab_name}\nQuestion: {custom_prompt if custom_prompt else 'Analyze data'}"

        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            # Use 1.5-flash as the primary stable model
            for model_name in ['gemini-1.5-flash', 'gemini-pro']:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(f"{system_msg}\n{user_msg}\nData:\n{data_summary}")
                    return response.text
                except Exception:
                    continue
            return "Gemini models currently unreachable."
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"{user_msg}\nData:\n{data_summary}"}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# 2. Authentication
def check_password():
    if "password_correct" not in st.session_state:
        st.subheader("Strategy Login")
        pwd = st.text_input("Enter Key", type="password")
        if st.button("Submit"):
            if pwd == "strategic_2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Denied")
        return False
    return True

if not check_password():
    st.stop()

# 3. State Setup
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "ai_report" not in st.session_state: st.session_state.ai_report = ""
if "last_q" not in st.session_state: st.session_state.last_q = ""

# 4. Data Loading
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data loading failed: {e}")
    st.stop()

# 5. Sidebar Navigation and Chat
sel_tab = st.sidebar.selectbox("Dashboard Section", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # Sidebar Filters
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
    if loc_col:
        u_locs = sorted(tab_df[loc_col].unique().tolist(), key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect("Filter Regions", u_locs, default=u_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # Sidebar Exports
    st.sidebar.divider()
    st.sidebar.subheader("Exports")
    if st.session_state.ai_report and PDF_SUPPORT:
        pdf_data = generate_pdf(st.session_state.ai_report, sel_tab)
        if pdf_data:
            st.sidebar.download_button("Download Report (PDF)", data=pdf_data, file_name=f"Analysis_{sel_tab}.pdf")
    
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            tab_df.to_excel(writer, index=False)
        st.sidebar.download_button("Download Data (Excel)", data=buf.getvalue(), file_name=f"Data_{sel_tab}.xlsx")
    except:
        pass

    # Sidebar Chat (Groq)
    st.sidebar.divider()
    st.sidebar.subheader("Strategic Chat")
    q = st.sidebar.text_input("Ask about this view", key="chat_input")
    if q and q != st.session_state.last_q:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=q)
        st.session_state.chat_history.append({"q": q, "a": ans})
        st.session_state.last_q = q

    for c in reversed(st.session_state.chat_history):
        st.sidebar.text(f"User: {c['q']}")
        st.sidebar.info(c['a'])

    # 6. Main Dashboard Area
    st.title(f"Strategic View: {sel_tab}")
    
    # Identify Data Columns
    val_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'VALUE', 'VALUE_POSITION'])), None)
    name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'METRIC'])), None)
    
    if val_col and name_col:
        st.subheader("Performance Overview")
        top_data = tab_df.groupby(name_col)[val_col].sum().nlargest(15).reset_index()
        fig = px.bar(top_data, x=val_col, y=name_col, orientation='h', color_discrete_sequence=['#004B95'])
        st.plotly_chart(fig, use_container_width=True, key="main_bar")

    # Forecasting (from modules/ml_models.py)
    if val_col and 'dt' in tab_df.columns:
        st.divider()
        st.subheader("3-Month Strategic Forecast")
        forecast_df = generate_forecast(tab_df, val_col)
        if not forecast_df.empty:
            fig_trend = go.Figure()
            hist_df = tab_df.groupby('dt')[val_col].sum().reset_index()
            fig_trend.add_trace(go.Scatter(x=hist_df['dt'], y=hist_df[val_col], name="Historical", line=dict(color='gray')))
            fig_trend.add_trace(go.Scatter(x=forecast_df['dt'], y=forecast_df[val_col], name="Forecast", line=dict(dash='dash', color='blue')))
            st.plotly_chart(fig_trend, use_container_width=True, key="trend_chart")

    # Strategic AI Analysis (Gemini)
    st.divider()
    st.subheader("Executive Analysis")
    if st.button("Generate Strategic AI Report"):
        with st.spinner("Analyzing performance data..."):
            st.session_state.ai_report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.rerun()
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)
