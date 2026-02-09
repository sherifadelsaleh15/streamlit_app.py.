import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 1. Page Config
st.set_page_config(page_title="2026 OKR Dashboard", layout="wide")
st.title("🚀 2026 Strategy AI Dashboard")

# 2. Connect to Google Sheets (using the link we published)
url = "YOUR_PUBLISHED_CSV_URL_HERE"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url, ttl="1h") # Caches for 1 hour to stay fast

# 3. Sidebar Filters
st.sidebar.header("Filter Analytics")
region = st.sidebar.multiselect("Select Region", options=df["Region"].unique(), default=df["Region"].unique())
source = st.sidebar.multiselect("Select Source", options=df["Source"].unique(), default=df["Source"].unique())

# Filter the data
mask = df["Region"].isin(region) & df["Source"].isin(source)
filtered_df = df[mask]

# 4. Display KPIs
st.subheader("Monthly Performance")
st.line_chart(data=filtered_df, x="Date_Month", y="Value")

# 5. THE AI CHAT BOX (The "Bricks" Alternative)
st.divider()
st.subheader("💬 Chat with your Data")
user_question = st.chat_input("Ask me about Objective 1 performance...")

if user_question:
    with st.chat_message("user"):
        st.write(user_question)
    
    with st.chat_message("assistant"):
        # Here you could integrate a free LLM API, but for now, 
        # we can show the filtered data the AI would analyze.
        st.write(f"Analyzing {len(filtered_df)} rows of data for your request...")
        st.dataframe(filtered_df.head())
