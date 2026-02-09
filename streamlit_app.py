import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }
    .metric-card { background-color: white; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .okr-box { border-left: 5px solid #0f172a; background: white; padding: 15px; margin-bottom: 20px; border-radius: 0 12px 12px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA NORMALIZATION ENGINE (The "Plan" implementation) ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

def normalize_date(date_val):
    """Normalize 1/1/2026, January 2026, or Jan 2026 -> Jan 2026"""
    try:
        if isinstance(date_val, str):
            # Try parsing common formats
            for fmt in ("%m/%d/%Y", "%B %Y", "%b %Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_val.strip(), fmt).strftime("%b %Y")
                except: continue
        return str(date_val)
    except:
        return "Unknown"

@st.cache_data(ttl=60)
def fetch_and_normalize_tab(tab_name):
    encoded_name = urllib.parse.quote(tab_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]

        # 1. Flexible Column Mapping (Your Plan Detail)
        mapping = {
            'Objective ID': 'Objective_ID', 'Objective_ID': 'Objective_ID',
            'Region/Country': 'Region', 'Region': 'Region',
            'Month': 'Date_Month', 'Date_Month': 'Date_Month', 'Date Month': 'Date_Month',
            'Metric Name': 'Metric_Name', 'Metric_Name': 'Metric_Name'
        }
        df = df.rename(columns=mapping)

        # 2. Handle Multi-Value Columns (Plan Step 1c)
        # If 'Views' or 'Clicks' exist, move them to a unified 'Value' column
        value_vars = ['Value', 'Views', 'Clicks', 'Active Users', 'Avg Position', 'New Followers']
        existing_values = [v for v in value_vars if v in df.columns]
        
        if len(existing_values) > 1:
            # Melt the dataframe: turn multiple value columns into separate rows
            id_vars = [c for c in df.columns if c not in value_vars]
            df = df.melt(id_vars=id_vars, value_vars=existing_values, var_name='Metric_Name_Suffix', value_name='Value')
            # Append suffix to Metric Name if it exists
            if 'Metric_Name' in df.columns:
                df['Metric_Name'] = df['Metric_Name'] + " (" + df['Metric_Name_Suffix'] + ")"
            else:
                df['Metric_Name'] = df['Metric_Name_Suffix']

        # 3. Date Normalization (Plan Step 1d)
        if 'Date_Month' in df.columns:
            df['Date_Month'] = df['Date_Month'].apply(normalize_date)

        # 4. Final Polish
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
            
        df['Sheet_Source'] = tab_name # Tag origin (Plan Step 2c)
        return df
    except Exception as e:
        return pd.DataFrame()

# --- 3. DASHBOARD UI ---
st.title("🚀 2026 Global Strategy Dashboard")

# Tab Selector (Plan Step 2)
available_tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab_name = st.selectbox("📂 Select Performance View", ["All Sheets Summary"] + available_tabs)

# --- 4. PROCESSING & FILTERING ---
if selected_tab_name == "All Sheets Summary":
    all_data = pd.concat([fetch_and_normalize_tab(t) for t in available_tabs], ignore_index=True)
else:
    all_data = fetch_and_normalize_tab(selected_tab_name)

if not all_data.empty:
    # Filter Bar (Plan Step 3)
    with st.sidebar:
        st.header("🎛️ Filter Intelligence")
        # Clean empty strings and sort for SelectItem safety
        def get_opts(col): return sorted([str(x) for x in all_data[col].unique() if str(x).strip()]) if col in all_data.columns else []

        f_region = st.multiselect("Region", get_opts('Region'), default=get_opts('Region'))
        f_metric = st.multiselect("Metric", get_opts('Metric_Name'), default=get_opts('Metric_Name'))

    # Apply filters
    mask = (all_data['Region'].astype(str).isin(f_region)) & (all_data['Metric_Name'].astype(str).isin(f_metric))
    filtered_df = all_data[mask]

    # --- 5. VISUALIZATION (Plan Step 4) ---
    st.markdown("### 📈 OKR Performance Trends")
    
    # Create a unique chart for every OKR/Metric found
    unique_metrics = filtered_df['Metric_Name'].unique() if 'Metric_Name' in filtered_df.columns else []
    
    for metric in unique_metrics:
        m_data = filtered_df[filtered_df['Metric_Name'] == metric]
        
        with st.container():
            st.markdown(f'<div class="okr-box"><strong>Metric:</strong> {metric}</div>', unsafe_allow_html=True)
            col_chart, col_stat = st.columns([3, 1])
            
            with col_chart:
                # Force chronological sort for the chart
                st.area_chart(m_data, x="Date_Month", y="Value", color="#0f172a")
            
            with col_stat:
                total = m_data['Value'].sum()
                st.metric("Total Performance", f"{total:,.0f}")
                st.dataframe(m_data[['Region', 'Value']].head(5), hide_index=True)

else:
    st.warning("No data found. Ensure Google Sheet is shared and tab names match.")
