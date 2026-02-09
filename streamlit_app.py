import streamlit as st
import pandas as pd

st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide")
st.title("🚀 2026 Strategy AI Dashboard")

# 1. YOUR NEW SHEET ID LINK (Direct Export)
# Sheet ID extracted from your URL: 1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY
url = "https://docs.google.com/spreadsheets/d/1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY/export?format=csv"

@st.cache_data(ttl=300) # Refresh data every 5 minutes
def load_data(sheets_url):
    data = pd.read_csv(sheets_url)
    
    # --- AUTO-FIX COLUMN NAMES ---
    # This maps your sheet's column names to standard names the dashboard uses
    mapping = {
        'Month ': 'Date_Month', # Added a space because sometimes sheets have trailing spaces
        'Month': 'Date_Month',
        'Region/Country': 'Region',
        'Metric Name': 'Metric_Name',
        'Objective ID': 'Objective_ID',
        'Value': 'Value'
    }
    data = data.rename(columns=mapping)
    return data

try:
    df = load_data(url)
    
    # 2. Sidebar Filters
    st.sidebar.header("Filter Analytics")
    
    # Filter by Region
    if "Region" in df.columns:
        region_list = df["Region"].unique()
        selected_regions = st.sidebar.multiselect("Select Region", options=region_list, default=region_list)
        df = df[df["Region"].isin(selected_regions)]

    # Filter by Metric
    if "Metric_Name" in df.columns:
        metrics = df["Metric_Name"].unique()
        selected_metrics = st.sidebar.multiselect("Select Metrics", options=metrics, default=metrics)
        df = df[df["Metric_Name"].isin(selected_metrics)]

    # 3. Main Dashboard Display
    st.subheader("📊 Data Overview")
    st.dataframe(df, use_container_width=True)

    # 4. Charting Logic
    # Note: Ensure the "Month" column in your sheet contains dates or text like "January"
    if "Date_Month" in df.columns and "Value" in df.columns:
        st.subheader("📈 Performance Trend")
        
        # Clean the 'Value' column to make sure it's a number
        df["Value"] = pd.to_numeric(df["Value"], errors='coerce')
        
        # Create the chart
        st.line_chart(df, x="Date_Month", y="Value")
    else:
        st.warning("Ensure your sheet has 'Month' and 'Value' columns filled with data.")

except Exception as e:
    st.error(f"Dashboard Error: {e}")
    st.info("Make sure your Google Sheet is shared as 'Anyone with the link can view'.")

# 5. AI Interaction
st.divider()
st.subheader("💬 Chat with your Data")
user_question = st.chat_input("Ask about Objective 1 performance...")
if user_question:
    st.write(f"Assistant: Looking into '{user_question}' for you...")
