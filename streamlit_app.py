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

# Safe PDF Import
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

# PDF HELPER
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

# SIMPLIFIED GEMINI SETUP - Using only gemini-pro which is most widely available
def setup_gemini():
    """Simple Gemini setup with error handling"""
    try:
        genai.configure(api_key=GEMINI_KEY)
        # Try the most basic model first
        model = genai.GenerativeModel('gemini-pro')
        # Test the model with a simple prompt
        response = model.generate_content("test", generation_config={'max_output_tokens': 5})
        return model, None
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg:
            return None, "Invalid API key. Please check your Gemini API key."
        elif "not found" in error_msg or "not supported" in error_msg:
            return None, "Gemini model not available. Your API key may need to be enabled at https://makersuite.google.com/app/apikey"
        else:
            return None, f"Gemini setup failed: {error_msg}"

# Initialize Gemini at startup
gemini_model, gemini_error = setup_gemini()

# CORE AI ENGINE
def get_ai_strategic_insight(df, tab_name, engine="groq", custom_prompt=None):
    try:
        loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
        val_col = next((c for c in df.columns if any(x in c.upper() for x in ['CLICKS', 'USERS', 'SESSIONS', 'VALUE'])), None)
        metric_col = next((c for c in df.columns if any(x in c.upper() for x in ['METRIC', 'TYPE', 'KEYWORD', 'QUERY'])), None)
        date_col = 'dt'

        # Build Advanced Data Context
        if loc_col and val_col:
            monthly_df = df.copy()
            monthly_df['Month'] = monthly_df[date_col].dt.strftime('%b %Y')
            
            # Regional Comparison Matrix
            comparison_matrix = monthly_df.groupby([loc_col, 'Month', metric_col if metric_col else loc_col])[val_col].sum().unstack(level=0).fillna(0)
            
            # Totals per region
            group_total = [loc_col]
            if metric_col: group_total.append(metric_col)
            totals_str = df.groupby(group_total)[val_col].sum().reset_index().to_string(index=False)
            
            # Monthly breakdown
            monthly_breakdown = monthly_df.groupby(['Month', loc_col])[val_col].sum().reset_index().to_string(index=False)
            
            data_context = f"""
SYSTEM STRATEGIC DATA:

[REGIONAL COMPARISON MATRIX (Monthly)]:
{comparison_matrix.to_string()}

[MONTHLY BREAKDOWN BY REGION]:
{monthly_breakdown}

[LIFETIME TOTALS PER REGION]:
{totals_str}

[RAW SAMPLE - Last 10 rows]:
{df.tail(10).to_string()}
"""
        else:
            data_context = df.head(50).to_string()

        # Enhanced Comparison Instructions
        system_msg = """You are a Senior Strategic Analyst. 
- When asked to compare countries, use the COMPARISON MATRIX to find differences in growth, volume, and monthly trends.
- Identify which market is leading and which is lagging.
- If data for a month is 0 in the matrix, interpret it as 'No Activity' for that specific period.
- Be critical: don't just state the numbers, explain what the gap between markets means for the business.
- Provide actionable strategic recommendations based on the data patterns observed."""

        user_msg = f"Dashboard Tab: {tab_name}\n\nUser Question: {custom_prompt if custom_prompt else f'Compare the regional performance in {tab_name} and provide strategic recommendations.'}"

        if engine == "gemini":
            global gemini_model, gemini_error
            
            if gemini_model is None:
                return f"AI Logic Error: Gemini unavailable - {gemini_error if gemini_error else 'Unknown error'}"
            
            try:
                # Simple generation without complex parameters
                response = gemini_model.generate_content(
                    f"{system_msg}\n\n{user_msg}\n\nData Context:\n{data_context}"
                )
                return response.text
            except Exception as e:
                return f"AI Logic Error: Gemini generation failed: {str(e)}"
        else:
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"{user_msg}\n\nData Context:\n{data_context}"}
                ]
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

# Session State
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "ai_report" not in st.session_state: st.session_state.ai_report = ""
if "last_chat_input" not in st.session_state: st.session_state.last_chat_input = ""

# Load Data
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

    # Sidebar Filters
    if loc_col:
        raw_locs = tab_df[loc_col].dropna().unique()
        all_locs = sorted([str(x) for x in raw_locs], key=lambda x: x != 'Germany')
        sel_locs = st.sidebar.multiselect("Filter Regions", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # Sidebar Downloads
    st.sidebar.divider()
    st.sidebar.subheader("Export Options")
    if st.session_state.ai_report and PDF_SUPPORT:
        pdf_bytes = generate_pdf(st.session_state.ai_report, sel_tab)
        st.sidebar.download_button("Download PDF Report", data=pdf_bytes, file_name=f"Report_{sel_tab}.pdf")
    
    try:
        import xlsxwriter
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            tab_df.to_excel(writer, index=False, sheet_name='Data')
        st.sidebar.download_button("Export Data to Excel", data=output.getvalue(), file_name=f"Data_{sel_tab}.xlsx")
    except ImportError:
        pass

    # Sidebar Chat
    st.sidebar.divider()
    st.sidebar.subheader("Data Chat")
    user_q = st.sidebar.text_input("Ask a question", key="chat_input")
    
    # Only run Groq if the question has actually changed
    if user_q and user_q != st.session_state.last_chat_input:
        ans = get_ai_strategic_insight(tab_df, sel_tab, engine="groq", custom_prompt=user_q)
        st.session_state.chat_history.append({"q": user_q, "a": ans})
        st.session_state.last_chat_input = user_q

    for chat in reversed(st.session_state.chat_history):
        st.sidebar.text(f"User: {chat['q']}")
        st.sidebar.info(chat['a'])

    # Main Visuals
    st.title(f"Strategic View: {sel_tab}")
    
    if "GSC" in sel_tab.upper() and metric_name_col:
        st.subheader("Top 20 Keywords")
        agg_k = 'min' if is_ranking else 'sum'
        top_k = tab_df.groupby(metric_name_col)[value_col].agg(agg_k).reset_index().sort_values(by=value_col, ascending=(agg_k=='min')).head(20)
        fig_k = px.bar(top_k, x=value_col, y=metric_name_col, orientation='h')
        if is_ranking: fig_k.update_layout(xaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_k, use_container_width=True, key="main_bar_chart")

    # Gemini Report
    st.divider()
    st.subheader("Strategic AI Report")
    
    # Show Gemini status
    if gemini_model is None:
        st.error(f"⚠️ **Gemini AI Unavailable**")
        st.info(f"**Reason**: {gemini_error}")
        st.markdown("""
        **To fix this:**
        1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Sign in with your Google account
        3. Create a new API key or enable your existing one
        4. Make sure the Generative Language API is enabled in your Google Cloud Console
        5. Update the GEMINI_KEY in the code
        
        **Alternative**: Use the sidebar chat with Groq (already working) for analysis.
        """)
    else:
        if st.button("Generate Strategic Analysis with Gemini"):
            with st.spinner("Analyzing with Gemini..."):
                st.session_state.ai_report = get_ai_strategic_insight(tab_df, sel_tab, engine="gemini")
                st.rerun()
    
    if st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    # Trends Loop
    st.divider()
    st.subheader("Monthly Performance Trends")
    if metric_name_col and value_col and date_col in tab_df.columns:
        agg_sort = 'min' if is_ranking else 'sum'
        top_20_list = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()

        for loc_idx, loc in enumerate(tab_df[loc_col].unique() if loc_col else [None]):
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.write(f"Region: {loc if loc else 'Global'}")
            region_keywords = [kw for kw in top_20_list if kw in loc_data[metric_name_col].unique()]

            for kw_idx, kw in enumerate(region_keywords):
                kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
                with st.expander(f"Data for: {kw}"):
                    fig = px.line(kw_data, x='dt', y=value_col, markers=True, title=f"Trend: {kw}")
                    if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig, use_container_width=True, key=f"trend_{loc_idx}_{kw_idx}")
