import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="2026 OKR Dashboard", layout="wide")
st.title("🚀 2026 Strategy AI Dashboard")

# 2. Your Converted Sheet Link (Machine Readable)
# Your ID: 1WcEEqPkzvGW
# Formatted for Streamlit connection:
url = "https://docs.google.com/spreadsheets/d/1WcEEqPkzvGW/edit#gid=0"

# 3. Connect using the library
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # We use the public URL directly in the read function
    df = conn.read(spreadsheet=url, ttl="5m") 

    # 4. Sidebar Filters
    st.sidebar.header("Filter Analytics")
    
    # Check if columns exist before filtering to prevent errors
    if not df.empty:
        # If your columns have different names in the sheet, update these strings:
        region_col = "Region" if "Region" in df.columns else df.columns[1]
        source_col = "Source" if "Source" in df.columns else df.columns[4]

        regions = st.sidebar.multiselect("Select Region", options=df[region_col].unique(), default=df[region_col].unique())
        sources = st.sidebar.multiselect("Select Source", options=df[source_col].unique(), default=df[source_col].unique())

        # Filter Logic
        mask = df[region_col].isin(regions) & df[source_col].isin(sources)
        filtered_df = df[mask]

        # 5. Display Data & Charts
        st.subheader("📊 Performance Overview")
        st.dataframe(filtered_df, use_container_width=True)
        
        if "Value" in filtered_df.columns:
            st.line_chart(data=filtered_df, x="Date_Month", y="Value")
        else:
            st.info("Add a column named 'Value' to see the line chart.")

except Exception as e:
    st.error(f"Connection Error: {e}")
    st.info("Check that your Google Sheet is set to 'Anyone with the link can view'.")

# 6. AI Chat Box
st.divider()
st.subheader("💬 Chat with your Data")
user_question = st.chat_input("Ask me about your February progress...")
if user_question:
    st.write(f"Assistant: I am analyzing your data for: '{user_question}'")
    st.write("Feature coming soon: Integrating LLM for deeper insights.")
