import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    .okr-container {
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 8px;
        background-color: #ffffff;
        margin-bottom: 32px;
    }
    .okr-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def fetch_data(tab_name):
    encoded_name = urllib.parse.quote(tab_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Expanded Mapping to prevent AttributeError
        mapping = {
            'Month': 'Month', 'Date_Month': 'Month', 'Date Month': 'Month',
            'Region/Country': 'Region', 'Region': 'Region',
            'Metric Name': 'OKR_Name', 'OKR_ID': 'OKR_Name', 'Metric_Name': 'OKR_Name',
            'Objective ID': 'OKR_Name', 'Page Path': 'OKR_Name', 'Query': 'OKR_Name'
        }
        df = df.rename(columns=mapping)
        
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

# --- 3. NAVIGATION & FILTERS ---
tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.selectbox("Data Source", tabs)

df = fetch_data(selected_tab)

if not df.empty:
    # Sidebar Filters
    st.sidebar.markdown("---")
    
    # Dynamic month sorting
    months = sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else []
    sel_months = st.sidebar.multiselect("Months", options=months, default=months, key=f"m_{selected_tab}")
    
    regions = sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else []
    sel_regions = st.sidebar.multiselect("Regions", options=regions, default=regions, key=f"r_{selected_tab}")

    # Filter Application
    f_df = df.copy()
    if sel_months:
        f_df = f_df[f_df['Month'].isin(sel_months)]
    if sel_regions:
        f_df = f_df[f_df['Region'].isin(sel_regions)]

    # --- 4. MAIN DASHBOARD ---
    st.markdown(f"### {selected_tab.replace('_', ' ')} Performance")
    
    # Safe Column Identification
    id_col = 'OKR_Name' if 'OKR_Name' in f_df.columns else None
    
    # If OKR_Name is missing, try to use the first text column as a fallback
    if id_col is None:
        text_cols = f_df.select_dtypes(include=['object']).columns
        if len(text_cols) > 0:
            id_col = text_cols[0]

    if id_col and 'Value' in f_df.columns:
        unique_okrs = f_df[id_col].unique()
        
        for okr in unique_okrs:
            okr_subset = f_df[f_df[id_col] == okr]
            
            # Sort subset by month if possible to ensure chart continuity
            if 'Month' in okr_subset.columns:
                # Basic alphabetical sort for months (Jan, Feb...)
                okr_subset = okr_subset.sort_values('Month')

            with st.container():
                st.markdown('<div class="okr-container">', unsafe_allow_html=True)
                st.markdown(f'<div class="okr-header">{okr}</div>', unsafe_allow_html=True)
                
                chart_col, data_col = st.columns([2.5, 1])
                
                with chart_col:
                    st.area_chart(okr_subset, x='Month' if 'Month' in okr_subset.columns else None, y='Value', color="#0f172a")
                
                with data_col:
                    st.metric("Total", f"{okr_subset['Value'].sum():,.0f}")
                    st.dataframe(okr_subset[['Month', 'Value']], hide_index=True, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.dataframe(f_df, use_container_width=True)

    # --- 5. AI CHAT ASSISTANT ---
    st.markdown("---")
    st.markdown("### AI Data Assistant")
    user_query = st.chat_input("Search metrics or regions...")
    
    if user_query:
        with st.chat_message("assistant"):
            keywords = user_query.lower().split()
            search_results = df.copy()
            for word in keywords:
                search_results = search_results[search_results.apply(lambda row: row.astype(str).str.lower().str.contains(word).any(), axis=1)]
            
            if not search_results.empty:
                st.write(f"Results for '{user_query}':")
                st.dataframe(search_results, use_container_width=True)
            else:
                st.write("No matching data found.")
else:
    st.info("Awaiting data connection. Verify tab names in Google Sheets.")
