import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide")

# Custom CSS for a professional, high-contrast look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    
    /* Executive Card Styling */
    .okr-container {
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 8px;
        background-color: #ffffff;
        margin-bottom: 32px;
    }
    .okr-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 16px;
        border-bottom: 2px solid #3b82f6;
        display: inline-block;
        padding-bottom: 4px;
    }
    /* Metric styling */
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #1e293b; }
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
        
        # Schema Normalization
        mapping = {
            'Month': 'Month', 'Date_Month': 'Month', 'Date Month': 'Month',
            'Region/Country': 'Region', 'Region': 'Region',
            'Metric Name': 'OKR_Name', 'OKR_ID': 'OKR_Name', 'Metric_Name': 'OKR_Name'
        }
        df = df.rename(columns=mapping)
        
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

# --- 3. SIDEBAR NAVIGATION ---
tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.selectbox("Data Source", tabs)

df = fetch_data(selected_tab)

# --- 4. FILTRATION LOGIC ---
if not df.empty:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter View")
    
    # Month Filter
    months = sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else []
    sel_months = st.sidebar.multiselect("Months", options=months, default=months, key=f"m_{selected_tab}")
    
    # Region Filter
    regions = sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else []
    sel_regions = st.sidebar.multiselect("Regions", options=regions, default=regions, key=f"r_{selected_tab}")

    # Application of filters
    f_df = df.copy()
    if sel_months:
        f_df = f_df[f_df['Month'].isin(sel_months)]
    if sel_regions:
        f_df = f_df[f_df['Region'].isin(sel_regions)]

    # --- 5. MAIN DASHBOARD ---
    st.markdown(f"### {selected_tab.replace('_', ' ')} Performance")
    
    # OKR Charting Logic
    id_col = 'OKR_Name' if 'OKR_Name' in f_df.columns else None
    
    if id_col and 'Value' in f_df.columns:
        unique_okrs = f_df[id_col].unique()
        
        for okr in unique_okrs:
            okr_subset = f_df[f_df[id_col] == okr]
            
            with st.container():
                st.markdown(f'<div class="okr-container">', unsafe_allow_html=True)
                st.markdown(f'<div class="okr-header">{okr}</div>', unsafe_allow_html=True)
                
                chart_col, data_col = st.columns([2.5, 1])
                
                with chart_col:
                    # High-fidelity area chart
                    st.area_chart(okr_subset, x='Month' if 'Month' in okr_subset.columns else None, y='Value', color="#0f172a")
                
                with data_col:
                    total_val = okr_subset['Value'].sum()
                    st.metric("Total Progress", f"{total_val:,.0f}")
                    st.dataframe(okr_subset[['Month', 'Value', 'Region']] if 'Region' in okr_subset.columns else okr_subset[['Month', 'Value']], hide_index=True, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.dataframe(f_df, use_container_width=True)

    # --- 6. AI CHAT ASSISTANT ---
    st.markdown("---")
    st.markdown("### AI Data Assistant")
    user_query = st.chat_input("Ask a question about this dataset...")
    
    if user_query:
        with st.chat_message("assistant"):
            # Search logic: filter for any rows matching keywords
            keywords = user_query.lower().split()
            search_results = df.copy()
            for word in keywords:
                search_results = search_results[search_results.apply(lambda row: row.astype(str).str.lower().str.contains(word).any(), axis=1)]
            
            if not search_results.empty:
                st.write(f"I found {len(search_results)} matching records for '{user_query}':")
                st.dataframe(search_results, use_container_width=True)
                if 'Value' in search_results.columns:
                    st.info(f"The combined value for these records is {search_results['Value'].sum():,.2f}")
            else:
                st.write("No matching data found. Please refine your keywords.")

else:
    st.error("Data could not be retrieved. Please verify tab names and sharing settings.")
