import streamlit as st
import pandas as pd

st.set_page_config(page_title="2026 Strategy AI", layout="wide", initial_sidebar_state="expanded")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_value=True)

# 1. DATA ENGINE
url = "https://docs.google.com/spreadsheets/d/1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY/export?format=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns] # Clean hidden spaces
    mapping = {'Month': 'Date_Month', 'Region/Country': 'Region', 'Metric Name': 'Metric'}
    return df.rename(columns=mapping)

df = load_data()

# 2. HEADER & KPI CARDS
st.title("📈 2026 Strategy Command Center")
st.caption("Real-time OKR Tracking & AI Analysis")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Value", f"{pd.to_numeric(df['Value'], errors='coerce').sum():,.0f}")
with col2:
    st.metric("Regions Active", len(df['Region'].unique()))
with col3:
    st.metric("Current Month", df['Date_Month'].iloc[-1] if not df.empty else "N/A")
with col4:
    st.metric("Status", "Online", delta="Healthy")

st.divider()

# 3. SIDEBAR FILTERS
with st.sidebar:
    st.header("🎛️ Control Panel")
    selected_region = st.multiselect("Target Region", options=df['Region'].unique(), default=df['Region'].unique())
    selected_metric = st.selectbox("Select KPI", options=df['Metric'].unique())

# Filter Data
filtered_df = df[(df['Region'].isin(selected_region)) & (df['Metric'] == selected_metric)]

# 4. VISUALS SECTION
view_col, chart_col = st.columns([1, 1])

with view_col:
    st.subheader("📋 Raw Intelligence")
    st.dataframe(filtered_df, use_container_width=True, height=400)

with chart_col:
    st.subheader("📊 Growth Trend")
    if not filtered_df.empty:
        st.line_chart(filtered_df, x="Date_Month", y="Value", color="#FF4B4B")

# 5. THE AI CHAT ENGINE (Functional)
st.divider()
st.subheader("🤖 AI Data Consultant")
prompt = st.chat_input("Ask me to 'Show Germany' or 'Show February'...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        # Simple Logic: AI searches the dataframe for your keywords
        search_term = prompt.title()
        ai_results = df[df.apply(lambda row: row.astype(str).str.contains(search_term).any(), axis=1)]
        
        if not ai_results.empty:
            st.write(f"I found {len(ai_results)} records related to '{prompt}':")
            st.dataframe(ai_results)
        else:
            st.write(f"I analyzed the 2026 dataset but couldn't find a direct match for '{prompt}'. Try asking for a specific Region or Month.")
