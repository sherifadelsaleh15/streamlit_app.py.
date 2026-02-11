import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import io
import google.generativeai as genai
from groq import Groq
from modules.data_loader import load_and_preprocess_data

# PDF Library Setup
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
    clean_text = report_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# AI ENGINE WITH 404 FALLBACK
def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        # Data Context Prep
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'VALUE'])), None)
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        
        data_summary = df.head(15).to_string()
        system_msg = "Senior Strategic Analyst. Compare performance and provide business implications."
        user_msg = f"Tab: {tab_name}\nQuestion: {custom_prompt if custom_prompt else 'Analyze data'}"

        if engine == "gemini":
            genai.configure(api_key=GEMINI_KEY)
            # Comprehensive fallback list for Gemini 1.5
            model_names = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
            
            for m_name in model_names:
                try:
                    model = genai.GenerativeModel(m_name)
                    response = model.generate_content(f"{system_msg}\n{user_msg}\nData:\n{data_summary}")
                    return response.text
                except Exception:
                    continue
            return "Gemini models currently unreachable. Please use Groq chat."
            
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": f"{user_msg}\nData:\n{data_summary}"}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# 2. Authentication
def check_password():
    if "password_correct" not in st.session_state:
        st.subheader("Login")
        pwd = st.text_input("Password", type="password")
        if st.button("Enter"):
            if pwd == "strategic_2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Denied")
        return False
    return True

if not check_password():
    st.stop()

# 3. State Management
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "ai_report" not in st.session_state: st.session_state.ai_report = ""
if "last_q" not in st.session_state: st.session_state.last_q = ""

# 4. Data Loading
try:
    df_dict = load_and_preprocess_data()
except Exception as e:
    st.error(f"Data error: {e}")
    st.stop()

# 5. Sidebar Layout
sel_tab = st.sidebar.selectbox("Navigation", list(df_dict.keys()))
tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # Exports
    st.sidebar.divider()
    st.sidebar.subheader("Exports")
    if st.session_state.ai_report and PDF_SUPPORT:
        st.sidebar.download_button("Download PDF", data=generate_pdf(st.session_state.ai_report, sel_tab), file_name="Report.pdf")
    
    try:
        import xlsxwriter
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            tab_df.to_excel(writer, index=False)
        st.sidebar.download_button("Download Excel", data=buf.getvalue(), file_name="Data.xlsx")
    except ImportError:
        pass

    # Chat
    st.sidebar.divider()
    st.sidebar.subheader("Chat")
    q = st.sidebar.text_input("Ask about data", key="chat_input")
    if q and q != st.session_state.last_q:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=q)
        st.session_state.chat_history.append({"q": q, "a": ans})
        st.session_state.last_q = q

    for c in reversed(st.session_state.chat_history):
        st.sidebar.text(f"Q: {c['q']}")
        st.sidebar.info(c['a'])

    # 6. Main Dashboard
    st.title(f"Strategic View: {sel_tab}")
    
    # Simple Visualization
    val_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'VALUE'])), None)
    name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'METRIC'])), None)
    
    if val_col and name_col:
        top_data = tab_df.groupby(name_col)[val_col].sum().nlargest(15).reset_index()
        fig = px.bar(top_data, x=val_col, y=name_col, orientation='h')
        st.plotly_chart(fig, use_container_width=True)

    # Gemini Report
    st.divider()
    st.subheader("Strategic Analysis")
    if st.button("Generate AI Report"):
        with st.spinner("Analyzing..."):
            st.session_state.ai_report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
            st.rerun()
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)
