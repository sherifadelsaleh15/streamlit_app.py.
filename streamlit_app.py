import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="2026 Strategy Command Center", layout="wide")

# --- DATA ENGINE (Multi-Tab Support) ---
# Replace this ID with your Master Sheet ID
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_tab(sheet_name):
    # This URL format allows us to target specific tabs by name
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        return data
    except:
        return pd.DataFrame()

# --- HEADER & NAVIGATION ---
st.title("🚀 2026 Global Strategy Dashboard")

# 1. SELECT DATA SOURCE (This targets your Google Sheet Tabs)
# Make sure these names match your Tab names in Google Sheets exactly!
source = st.selectbox(
    "📂 Select Data Source", 
    ["OKR_Master", "Social_Media", "Top_Pages", "Keywords"]
)

df = load_tab(source)

if not df.empty:
    # --- DYNAMIC FILTERS ---
    # This automatically creates filters based on the columns in the selected tab
    st.sidebar.header(f"🔍 {source} Filters")
    
    filtered_df = df.copy()
    
    # Auto-generate multiselect filters for columns like 'Region', 'Category', 'Month'
    for col in df.columns:
        if col not in ['Value', 'Date', 'Impressions', 'Clicks']: # Don't filter by the numbers
            unique_vals = df[col].unique()
            selected = st.sidebar.multiselect(f"Filter {col}", options=unique_vals, default=unique_vals)
            filtered_df = filtered_df[filtered_df[col].isin(selected)]

    # --- KPI CARDS ---
    # We find the first numeric column to sum up
    nums = filtered_df.select_dtypes(include=['number']).columns
    c1, c2, c3 = st.columns(3)
    with c1:
        if len(nums) > 0:
            st.metric(f"Total {nums[0]}", f"{filtered_df[nums[0]].sum():,.0f}")
    with c2:
        st.metric("Entries", len(filtered_df))
    with c3:
        st.metric("Source Status", "Active", delta="Synced")

    # --- DASHBOARD VISUALS ---
    tab_view, tab_chart = st.tabs(["📊 Visualization", "📋 Data Table"])
    
    with tab_view:
        if len(nums) > 0:
            # If there's a 'Month' column, use it for the X-axis
            x_axis = 'Month' if 'Month' in filtered_df.columns else filtered_df.columns[0]
            st.subheader(f"{nums[0]} Trend")
            st.bar_chart(filtered_df, x=x_axis, y=nums[0])
        else:
            st.info("No numeric data available for charting in this tab.")

    with tab_chart:
        st.dataframe(filtered_df, use_container_width=True)

    # --- SMART SEARCH ---
    st.divider()
    st.subheader("💬 Search across this data")
    user_input = st.chat_input(f"Search {source}...")

    if user_input:
        keywords = user_input.lower().split()
        search_results = df.copy()
        for word in keywords:
            search_results = search_results[search_results.apply(lambda row: row.astype(str).str.lower().str.contains(word).any(), axis=1)]
        
        if not search_results.empty:
            st.write(f"Results for '{user_input}':")
            st.dataframe(search_results)
        else:
            st.warning("No matches found in this specific tab.")

else:
    st.error(f"Could not find data in the tab named '{source}'. Check your Google Sheet tab names.")
