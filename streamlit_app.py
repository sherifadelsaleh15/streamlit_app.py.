import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import io
from modules.data_loader import load_and_preprocess_data
from utils import get_prediction
from groq import Groq
import google.generativeai as genai

# PDF Library Import
try:
    from fpdf import FPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# 1. Page Config
st.set_page_config(layout="wide", page_title="2026 Strategic Dashboard")

# API KEYS
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

# PDF GENERATOR
def generate_pdf(report_text, tab_name):
    if not PDF_SUPPORT:
        return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Strategic Report: {tab_name}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    # Filter text for latin-1 compatibility
    clean_text = report_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# AI LOGIC ENGINE
def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'SESSIONS', 'VALUE'])), None)
        metric_col = next((c for c in df.columns if any(x in c.upper() for x in ['METRIC', 'TYPE', 'KEYWORD', 'QUERY'])), None)
        date_col = 'dt'

        if loc_col and val_col:
            monthly_df = df.copy()
            monthly_df['Month'] = monthly_df[date_col].dt.strftime('%b %Y')
            comparison_matrix = monthly_df.groupby([loc_col, 'Month', metric_col if metric_col else loc_col])[val_col].sum().unstack(level=0).fillna(0)
            group_total = [loc_col]
            if metric_col: group_total.append(metric_col)
            totals_str = df.groupby(group_total)[val_col].sum().reset_index().to_string(index=False)
            data_context = f"DATA SUMMARY:\nMATRIX:\n{comparison_matrix.to_string()}\n\nTOTALS:\n{totals_str}"
        else:
            data_context = df.head(50).to_string()

        system_msg = "Senior Strategic Analyst. Compare performance across regions and provide business implications."
        user_msg = f"Tab: {tab_name}\nQuestion: {custom_prompt if custom_prompt else f'Analyze performance for {tab_name}'}"

        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            # Fix: Using model name without 'models/' prefix to resolve 404
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{system_msg}\n\n{user_msg}\n\nContext:\n{data_context}")
            return response.text
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": f"{user_msg}\n\nContext:\n{data_context}"}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"AI Logic Error: {str(e)}"

def check_password():
    ADMIN_PASSWORD = "strategic_2026" 
    if "password_correct" not in st.session_state:
        st.subheader("Digital Strategy Login")
        pwd = st.text_input("Enter Password", type="password")
        if st.button("Submit"):
            if pwd == ADMIN_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Access Denied")
        return False
    return True

if not check_password():
    st.stop()

# Session State Persistence
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "ai_report" not in st.session_state: st.session_state.ai_report = ""
if "last_chat_input" not in st.session_state: st.session_state.last_chat_input = ""

# Data Loading
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data error: {e}"); st.stop()

sel_tab = st.sidebar.selectbox("Select Tab", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    date_col = 'dt'

    if value_col:
        tab_df[value_col] = pd.to_numeric(tab_df[value_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)

    is_ranking = "POSITION" in sel_tab.upper() or "TRACKING" in sel_tab.upper()

    # Sidebar Navigation and Filters
    if loc_col:
        raw_locs = tab_df[loc_col].dropna().unique()
        all_locs = sorted([str(x) for x in raw_locs], key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect("Filter Regions", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # Sidebar Export Tools
    st.sidebar.divider()
    st.sidebar.subheader("Export Options")
    if st.session_state.ai_report and PDF_SUPPORT:
        pdf_bytes = generate_pdf(st.session_state.ai_report, sel_tab)
        st.sidebar.download_button("Download PDF Report", data=pdf_bytes, file_name=f"Strategic_Report_{sel_tab}.pdf")
    
    try:
        import xlsxwriter
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            tab_df.to_excel(writer, index=False, sheet_name='Strategic_Data')
        st.sidebar.download_button("Export Data to Excel", data=output.getvalue(), file_name=f"Data_Export_{sel_tab}.xlsx")
    except ImportError:
        pass

    # Sidebar Interaction
    st.sidebar.divider()
    st.sidebar.subheader("Data Chat")
    user_q = st.sidebar.text_input("Ask a question", key="chat_input")
    
    # State check to prevent Groq from re-firing during Gemini report generation
    if user_q and user_q != st.session_state.last_chat_input:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
        st.session_state.chat_history.append({"q": user_q, "a": ans})
        st.session_state.last_chat_input = user_q

    for chat in reversed(st.session_state.chat_history):
        st.sidebar.text(f"User: {chat['q']}")
        st.sidebar.info(chat['a'])

    # Main Dashboard Area
    st.title(f"Strategic View: {sel_tab}")
    
    if "GSC" in sel_tab.upper() and metric_name_col:
        st.subheader("Top 20 Keywords")
        agg_k = 'min' if is_ranking else 'sum'
        top_k = tab_df.groupby(metric_name_col)[value_col].agg(agg_k).reset_index().sort_values(by=value_col, ascending=(agg_k=='min')).head(20)
        fig_k = px.bar(top_k, x=value_col, y=metric_name_col, orientation='h')
        if is_ranking: fig_k.update_layout(xaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_k, use_container_width=True, key="bar_chart_main")

    # Strategic Report (Gemini)
    st.divider()
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Processing analysis..."):
            st.session_state.ai_report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.rerun()
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    # Monthly Trends
    st.divider()
    st.subheader("Performance Trends")
    if metric_name_col and value_col and date_col in tab_df.columns:
        agg_sort = 'min' if is_ranking else 'sum'
        top_20_list = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()

        for l_idx, loc in enumerate(tab_df[loc_col].unique() if loc_col else [None]):
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.write(f"Region: {loc if loc else 'Global'}")
            region_keywords = [kw for kw in top_20_list if kw in loc_data[metric_name_col].unique()]

            for k_idx, kw in enumerate(region_keywords):
                kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
                with st.expander(f"Trend data: {kw}"):
                    fig = px.line(kw_data, x='dt', y=value_col, markers=True, title=f"Trend Analysis: {kw}")
                    if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed"))
                    # Unique keys to prevent StreamlitDuplicateElementId error
                    st.plotly_chart(fig, use_container_width=True, key=f"trend_chart_{l_idx}_{k_idx}")
                    
