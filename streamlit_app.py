import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide", page_icon="🚀")

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
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .okr-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .okr-title {
        font-size: 1.25rem;
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
        # 1. Clean whitespace from headers
        df.columns = [str(c).strip() for c in df.columns]
        
        # 2. Rename columns using a robust mapping
        mapping = {
            'Month': 'Month', 'Date_Month': 'Month', 'Date Month': 'Month',
            'Region/Country': 'Region', 'Region': 'Region',
            # Map multiple potential ID columns to a single standard name
            'Metric Name': 'OKR_Name', 'OKR_ID': 'OKR_Name', 'Metric_Name': 'OKR_Name',
            'Objective ID': 'OKR_Name', 'Page Path': 'OKR_Name', 'Query': 'OKR_Name',
            'Social Network': 'OKR_Name', 'Channel': 'OKR_Name', 'Landing Page': 'OKR_Name'
        }
        df = df.rename(columns=mapping)
        
        # 3. CRITICAL FIX: Remove Duplicate Columns
        # If two columns got renamed to 'OKR_Name', keep only the first one
        df = df.loc[:, ~df.columns.duplicated()]
        
        # 4. Ensure Value is numeric
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        return pd.DataFrame()

# --- 3. DASHBOARD LOGIC ---
st.title("🚀 2026 Strategy Command Center")

tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.selectbox("Select Data Source", tabs)

df = fetch_data(selected_tab)

if not df.empty:
    # Sidebar Filters
    st.sidebar.markdown("---")
    st.sidebar.header("Filter View")
    
    # Generate Month Filter
    months = sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else []
    sel_months = st.sidebar.multiselect("Months", options=months, default=months, key=f"m_{selected_tab}")
    
    # Generate Region Filter
    regions = sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else []
    sel_regions = st.sidebar.multiselect("Regions", options=regions, default=regions, key=f"r_{selected_tab}")

    # Apply Filters
    f_df = df.copy()
    if sel_months and 'Month' in f_df.columns:
        f_df = f_df[f_df['Month'].isin(sel_months)]
    if sel_regions and 'Region' in f_df.columns:
        f_df = f_df[f_df['Region'].isin(sel_regions)]

    # --- 4. VISUALIZATION ---
    st.markdown(f"### 📊 {selected_tab.replace('_', ' ')} Analysis")
    
    # Identify the ID Column (e.g., OKR_Name)
    id_col = 'OKR_Name' if 'OKR_Name' in f_df.columns else None
    
    # Fallback: If no 'OKR_Name', try finding the first text column
    if id_col is None:
        object_cols = f_df.select_dtypes(include=['object']).columns
        # Exclude common non-ID columns
        candidates = [c for c in object_cols if c not in ['Month', 'Region', 'Date']]
        if candidates:
            id_col = candidates[0]

    # Render Charts
    if id_col and 'Value' in f_df.columns:
        # Get unique items to chart
        unique_items = f_df[id_col].unique()
        
        for item in unique_items:
            # Filter data for this specific item
            subset = f_df[f_df[id_col] == item].copy()
            
            # Sort by Month for correct chart flow
            if 'Month' in subset.columns:
                subset = subset.sort_values('Month')

            # Render the Card
            with st.container():
                st.markdown('<div class="okr-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="okr-label">{id_col}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="okr-title">{item}</div>', unsafe_allow_html=True)
                
                c_chart, c_data = st.columns([2.5, 1])
                
                with c_chart:
                    st.area_chart(subset, x='Month' if 'Month' in subset.columns else None, y='Value', color="#0f172a")
                
                with c_data:
                    total = subset['Value'].sum()
                    st.metric("Total", f"{total:,.0f}")
                    st.dataframe(subset[['Month', 'Value']], hide_index=True, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No chartable data found. Showing raw table.")
        st.dataframe(f_df, use_container_width=True)

    # --- 5. AI SEARCH ---
    st.divider()
    st.markdown("### 🤖 Assistant")
    q = st.chat_input("Search (e.g., 'Google' or 'Jan')...")
    if q:
        with st.chat_message("assistant"):
            # Multi-keyword search
            terms = q.lower().split()
            res = df.copy()
            for t in terms:
                res = res[res.apply(lambda r: r.astype(str).str.lower().str.contains(t).any(), axis=1)]
            
            if not res.empty:
                st.write(f"Found {len(res)} matches:")
                st.dataframe(res, use_container_width=True)
            else:
                st.write("No matches found.")

else:
    st.error("Connection Error: Could not load data from Google Sheets.")
