import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="2026 Strategy Command Center", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM THEME & CSS ---
st.markdown("""
    <style>
    /* Professional Metric Cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f2f6;
    }
    /* Main App Background */
    .stApp {
        background-color: #f8f9fa;
    }
    /* Section Headers */
    .header-style {
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
# Using your provided Sheet ID: 1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY
url = "https://docs.google.com/spreadsheets/d/1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY/export?format=csv"

@st.cache_data(ttl=300) # Auto-refresh every 5 minutes
def load_data():
    try:
        data = pd.read_csv(url)
        # Standardize column names (remove hidden spaces and map to clean keys)
        data.columns = [c.strip() for c in data.columns]
        mapping = {
            'Month': 'Date_Month', 
            'Region/Country': 'Region', 
            'Metric Name': 'Metric',
            'Objective ID': 'Objective'
        }
        return data.rename(columns=mapping)
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- DASHBOARD HEADER ---
st.title("🚀 2026 Strategy Command Center")
st.markdown("---")

if not df.empty:
    # --- TOP ROW: KPI SUMMARY CARDS ---
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        total_val = pd.to_numeric(df['Value'], errors='coerce').sum()
        st.metric("Global Cumulative Value", f"{total_val:,.0f}")
    
    with kpi_col2:
        active_markets = len(df['Region'].unique())
        st.metric("Active Markets", active_markets)
        
    with kpi_col3:
        unique_metrics = len(df['Metric'].unique())
        st.metric("Tracked OKRs", unique_metrics)

    with kpi_col4:
        st.metric("Sync Status", "Live", delta="200 OK")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SIDEBAR FILTERS ---
    with st.sidebar:
        st.header("🎛️ Dashboard Controls")
        st.write("Filter the charts and tables below:")
        
        # Region Filter
        all_regions = sorted(df['Region'].unique())
        sel_region = st.multiselect("Select Target Region", all_regions, default=all_regions)
        
        # Metric Filter
        all_metrics = sorted(df['Metric'].unique())
        sel_metric = st.selectbox("Select Focus Metric", all_metrics)
        
        st.divider()
        st.info("💡 Tip: Use the Chat box at the bottom to find specific data points across all months.")

    # --- FILTER LOGIC ---
    mask = (df['Region'].isin(sel_region)) & (df['Metric'] == sel_metric)
    filtered_df = df[mask]

    # --- MAIN VISUALS SECTION ---
    col_table, col_chart = st.columns([1, 1.2], gap="large")

    with col_table:
        st.markdown('<p class="header-style">📋 Performance Records</p>', unsafe_allow_html=True)
        st.dataframe(
            filtered_df, 
            use_container_width=True, 
            height=400,
            column_config={
                "Value": st.column_config.NumberColumn(format="%d"),
                "Source": st.column_config.TextColumn(help="Data Origin Platform")
            }
        )

    with col_chart:
        st.markdown('<p class="header-style">📈 Trend Analysis</p>', unsafe_allow_html=True)
        if not filtered_df.empty:
            # Sort by Date_Month if possible, or just plot sequence
            st.line_chart(filtered_df, x="Date_Month", y="Value", color="#1E3A8A")
        else:
            st.warning("No data found for the selected filters.")

    # --- FUNCTIONAL CHAT ENGINE ---
    st.markdown("---")
    st.markdown('<p class="header-style">💬 Chat with your Data</p>', unsafe_allow_html=True)
    
    prompt = st.chat_input("Ask me something (e.g., 'Show Portugal' or 'What happened in January?')")

    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            # The "AI" logic: Keyword search across the whole database
            query = prompt.strip().lower()
            chat_results = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(query).any(), axis=1)]
            
            if not chat_results.empty:
                st.write(f"I analyzed the 2026 records. Here are the matches for **'{prompt}'**:")
                st.dataframe(chat_results, use_container_width=True)
            else:
                st.write(f"I couldn't find a direct match for **'{prompt}'** in the current dataset. Try searching for a specific Country, Metric, or Month.")

else:
    st.error("Waiting for data... Please check your Google Sheet sharing settings.")
