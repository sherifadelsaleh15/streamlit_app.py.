import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    
    .okr-card {
        border: 1px solid #f1f5f9;
        padding: 24px;
        border-radius: 12px;
        background-color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .okr-label {
        font-size: 0.9rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .okr-value-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 20px;
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
        
        # Robust Mapping logic
        mapping = {
            'Month': 'Month', 'Date_Month': 'Month', 'Date Month': 'Month',
            'Region/Country': 'Region', 'Region': 'Region',
            'Metric Name': 'OKR_Name', 'OKR_ID': 'OKR_Name', 'Metric_Name': 'OKR_Name',
            'Objective ID': 'OKR_Name', 'Page Path': 'OKR_Name', 'Query': 'OKR_Name',
            'Social Network': 'OKR_Name', 'Channel': 'OKR_Name'
        }
        df = df.rename(columns=mapping)
        
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

# --- 3. NAVIGATION ---
tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.selectbox("Data Source", tabs)

df = fetch_data(selected_tab)

if not df.empty:
    # Sidebar Filters
    st.sidebar.markdown("---")
    
    # Check for columns before creating filters to avoid errors
    month_opts = sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else []
    sel_months = st.sidebar.multiselect("Filter Months", month_opts, default=month_opts, key=f"m_{selected_tab}")
    
    reg_opts = sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else []
    sel_regions = st.sidebar.multiselect("Filter Regions", reg_opts, default=reg_opts, key=f"r_{selected_tab}")

    # Process Filtering
    f_df = df.copy()
    if sel_months and 'Month' in f_df.columns:
        f_df = f_df[f_df['Month'].isin(sel_months)]
    if sel_regions and 'Region' in f_df.columns:
        f_df = f_df[f_df['Region'].isin(sel_regions)]

    # --- 4. OKR VISUALIZATION ---
    st.markdown(f"### {selected_tab.replace('_', ' ')}")

    # FAIL-SAFE COLUMN DETECTION
    # If OKR_Name isn't found, use the first string-based column available
    id_col = 'OKR_Name' if 'OKR_Name' in f_df.columns else None
    if id_col is None:
        object_cols = f_df.select_dtypes(include=['object']).columns
        # Exclude 'Month' and 'Region' from being the Title
        possible_titles = [c for c in object_cols if c not in ['Month', 'Region']]
        id_col = possible_titles[0] if possible_titles else None

    # Only run charting if we have an ID column and a Value column
    if id_col and 'Value' in f_df.columns:
        unique_items = f_df[id_col].unique()
        
        for item in unique_items:
            subset = f_df[f_df[id_col] == item]
            
            # Month sorting (Basic alpha-sort for Jan, Feb, etc.)
            if 'Month' in subset.columns:
                subset = subset.sort_values('Month')

            with st.container():
                st.markdown('<div class="okr-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="okr-label">{id_col.replace("_", " ")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="okr-value-title">{item}</div>', unsafe_allow_html=True)
                
                chart_c, data_c = st.columns([3, 1])
                
                with chart_c:
                    # Clean black area chart
                    st.area_chart(subset, x='Month' if 'Month' in subset.columns else None, y='Value', color="#0f172a")
                
                with data_c:
                    st.metric("Total", f"{subset['Value'].sum():,.0f}")
                    st.dataframe(subset[['Month', 'Value']], hide_index=True, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.dataframe(f_df, use_container_width=True)

    # --- 5. AI DATA CHAT ---
    st.divider()
    st.markdown("### Assistant Intelligence")
    query = st.chat_input("Ask about specific OKRs or trends...")
    
    if query:
        with st.chat_message("assistant"):
            terms = query.lower().split()
            results = df.copy()
            for t in terms:
                results = results[results.apply(lambda r: r.astype(str).str.lower().str.contains(t).any(), axis=1)]
            
            if not results.empty:
                st.write(f"Search results for '{query}':")
                st.dataframe(results, use_container_width=True)
            else:
                st.write("No matching intelligence found for those keywords.")

else:
    st.info("System Ready. Connect Google Sheet tabs to initialize.")
