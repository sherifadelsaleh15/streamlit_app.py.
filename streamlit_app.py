import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="2026 OKR Tracker", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }
    .stMetric { background-color: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 12px; }
    .okr-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #0f172a; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def fetch_tab(name):
    encoded_name = urllib.parse.quote(name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        # Ensure Value is numeric
        if 'Value' in data.columns:
            data['Value'] = pd.to_numeric(data['Value'], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

# --- 3. NAVIGATION ---
st.title("🎯 2026 Strategy & OKR Performance")
tab_list = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
ui_tabs = st.tabs(tab_list)

# --- 4. DASHBOARD LOGIC ---
for i, tab_name in enumerate(tab_list):
    with ui_tabs[i]:
        df = fetch_tab(tab_name)
        
        if not df.empty:
            # Global Metrics for this Tab
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Total Volume", f"{df['Value'].sum() if 'Value' in df.columns else len(df):,.0f}")
            with m2:
                st.metric("Entries Count", len(df))
            with m3:
                st.metric("Data Scope", tab_name.replace("_", " "))

            st.divider()

            # --- DYNAMIC CHARTING BY OKR ---
            # We look for OKR_ID or Metric Name to group the charts
            group_col = None
            if 'OKR_ID' in df.columns: group_col = 'OKR_ID'
            elif 'Metric' in df.columns: group_col = 'Metric'
            elif 'Metric Name' in df.columns: group_col = 'Metric Name'

            if group_col and 'Value' in df.columns:
                st.subheader(f"📈 Individual {group_col} Trends")
                
                # Create a grid of charts (2 per row)
                unique_okrs = df[group_col].unique()
                cols = st.columns(2)
                
                for idx, okr in enumerate(unique_okrs):
                    okr_data = df[df[group_col] == okr].sort_values(by='Month' if 'Month' in df.columns else df.columns[0])
                    
                    with cols[idx % 2]:
                        st.markdown(f"""<div class="okr-card"><strong>{okr}</strong></div>""", unsafe_allow_html=True)
                        # We use area_chart for a "premium" look
                        st.area_chart(okr_data, x='Month' if 'Month' in df.columns else None, y='Value', color="#0f172a")
            else:
                st.info("No 'Value' or 'OKR_ID' columns found to generate individual charts.")
                st.dataframe(df.head(10), use_container_width=True)

            # --- SEARCH SECTION ---
            st.markdown("---")
            user_q = st.chat_input(f"Search {tab_name}...", key=f"chat_{tab_name}")
            if user_q:
                results = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(user_q.lower()).any(), axis=1)]
                st.dataframe(results, use_container_width=True)
        else:
            st.error(f"Tab '{tab_name}' is empty or not found.")
