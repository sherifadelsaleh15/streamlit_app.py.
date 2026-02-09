import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="2026 Strategy Command Center", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .stApp { background-color: #f9fbff; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
url = "https://docs.google.com/spreadsheets/d/1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    data = pd.read_csv(url)
    data.columns = [c.strip() for c in data.columns]
    # Standardizing names for the engine
    mapping = {
        'Month': 'Month', 
        'Region/Country': 'Region', 
        'Metric Name': 'Metric',
        'Objective ID': 'Objective',
        'OKR_ID': 'OKR_ID'
    }
    return data.rename(columns=mapping)

df = load_data()

# --- SIDEBAR: DEEP FILTRATION ---
with st.sidebar:
    st.header("🔍 Global Filters")
    
    # Hierarchical Filters
    sel_months = st.multiselect("Select Months", options=df['Month'].unique(), default=df['Month'].unique())
    sel_regions = st.multiselect("Select Regions", options=df['Region'].unique(), default=df['Region'].unique())
    sel_objectives = st.multiselect("Select Objectives", options=df['Objective'].unique(), default=df['Objective'].unique())
    sel_metrics = st.multiselect("Select Metrics", options=df['Metric'].unique(), default=df['Metric'].unique())
    sel_okrs = st.multiselect("Select OKR IDs", options=df['OKR_ID'].unique(), default=df['OKR_ID'].unique())

# Apply All Filters
f_df = df[
    (df['Month'].isin(sel_months)) & 
    (df['Region'].isin(sel_regions)) & 
    (df['Objective'].isin(sel_objectives)) & 
    (df['Metric'].isin(sel_metrics)) & 
    (df['OKR_ID'].isin(sel_okrs))
]

# --- DASHBOARD LAYOUT ---
st.title("🚀 2026 Strategy Command Center")

# Row 1: KPI Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Filtered Sum", f"{pd.to_numeric(f_df['Value'], errors='coerce').sum():,.0f}")
with c2:
    st.metric("Avg Performance", f"{pd.to_numeric(f_df['Value'], errors='coerce').mean():,.1f}")
with c3:
    st.metric("Data Points", len(f_df))
with c4:
    st.metric("Active Objectives", len(f_df['Objective'].unique()))

st.divider()

# Row 2: Visuals
col_a, col_b = st.columns([1, 1])

with col_a:
    st.subheader("📊 Trend by Month")
    if not f_df.empty:
        # Grouping data for a cleaner line chart
        chart_data = f_df.groupby('Month')['Value'].sum().reset_index()
        st.line_chart(chart_data, x="Month", y="Value")

with col_b:
    st.subheader("📍 Contribution by Region")
    if not f_df.empty:
        region_data = f_df.groupby('Region')['Value'].sum().reset_index()
        st.bar_chart(region_data, x="Region", y="Value")

# Row 3: The Data Table
st.subheader("📋 Filtered Intelligence")
st.dataframe(f_df, use_container_width=True)

# --- SMART AI CHAT ENGINE ---
st.divider()
st.subheader("💬 Smart Chat Assistant")
user_input = st.chat_input("Ex: 'Active Users January' or 'Germany Objective 1'")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    
    with st.chat_message("assistant"):
        # SMART SEARCH: Split input into keywords
        keywords = user_input.lower().split()
        
        # Search for rows that contain ALL keywords
        search_results = df.copy()
        for word in keywords:
            search_results = search_results[search_results.apply(lambda row: row.astype(str).str.lower().str.contains(word).any(), axis=1)]
        
        if not search_results.empty:
            st.write(f"I found {len(search_results)} records for your request:")
            st.dataframe(search_results, use_container_width=True)
            
            # Simple AI Insight
            total_val = pd.to_numeric(search_results['Value'], errors='coerce').sum()
            st.success(f"**Insight:** For this selection, the total value is **{total_val:,.0f}** across {len(search_results['Region'].unique())} regions.")
        else:
            st.warning("No direct match. Try using simpler keywords (e.g., 'Users Jan' instead of full sentences).")
