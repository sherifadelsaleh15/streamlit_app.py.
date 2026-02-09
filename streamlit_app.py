import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background: white; border: 1px solid #e2e8f0; padding: 20px;
        border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; }
    .source-label { font-size: 0.7rem; color: #3b82f6; text-transform: uppercase; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE UNIVERSAL ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_and_standardize_data():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_chunks = []

    # Mapping for all possible column variations across your tabs
    mapping = {
        "Objective_ID": "Objective", "Objective ID": "Objective",
        "Region/Country": "Region", "Region": "Region",
        "Date_Month": "Date", "Month": "Date", "Date Month": "Date",
        "Metric_Name": "Metric", "Metric Name": "Metric"
    }

    for tab in tabs:
        encoded = urllib.parse.quote(tab)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        try:
            df = pd.read_csv(url).dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.rename(columns=mapping)

            # Determine which column holds our numeric 'Result'
            # We check for 'Value', 'Views', 'Clicks', or 'KeywordClicks'
            value_col = None
            for col in ['Value', 'Views', 'Clicks', 'KeywordClicks']:
                if col in df.columns:
                    value_col = col
                    break
            
            if value_col:
                # Standardize the data slice
                temp = pd.DataFrame()
                temp['Objective'] = df['Objective'] if 'Objective' in df.columns else "General"
                temp['Region'] = df['Region'] if 'Region' in df.columns else "Global"
                temp['Metric'] = df['Metric'] if 'Metric' in df.columns else tab
                temp['Date_Raw'] = df['Date']
                temp['Val'] = pd.to_numeric(df[value_col], errors='coerce').fillna(0)
                temp['Source_Tab'] = tab
                
                # Cleanup Date Strings
                temp['Date_Clean'] = temp['Date_Raw'].astype(str).str.replace('1/1/2026', 'Jan 2026').str.replace('2/1/2026', 'Feb 2026')
                
                # Reset index to prevent InvalidIndexError during concat
                all_chunks.append(temp.reset_index(drop=True))
        except:
            continue

    return pd.concat(all_chunks, ignore_index=True) if all_chunks else pd.DataFrame()

# --- 3. UI LOGIC ---
master_df = load_and_standardize_data()

if not master_df.empty:
    st.title("2026 Strategy Performance")

    # Sidebar
    with st.sidebar:
        st.header("Filters")
        regions = sorted(master_df['Region'].unique().tolist())
        sel_regions = st.multiselect("Region", regions, default=regions)
        
        dates = master_df['Date_Clean'].unique().tolist()
        sel_dates = st.multiselect("Months", dates, default=dates)

    # Filtered Data
    f_df = master_df[(master_df['Region'].isin(sel_regions)) & (master_df['Date_Clean'].isin(sel_dates))]

    # Tabs
    ui_tabs = st.tabs(["Overview"] + sorted(master_df['Source_Tab'].unique().tolist()))

    for i, t_name in enumerate(["Overview"] + sorted(master_df['Source_Tab'].unique().tolist())):
        with ui_tabs[i]:
            display_df = f_df if t_name == "Overview" else f_df[f_df['Source_Tab'] == t_name]
            
            if display_df.empty:
                st.info("No data for selection.")
                continue

            # Display by Objective
            for obj in display_df['Objective'].unique():
                st.subheader(f"Target: {obj}")
                obj_data = display_df[display_df['Objective'] == obj]
                
                # Metrics within this Objective
                for metric in obj_data['Metric'].unique():
                    m_plot = obj_data[obj_data['Metric'] == metric].copy()
                    
                    with st.container():
                        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="source-label">{m_plot["Source_Tab"].iloc[0]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-title">{metric}</div>', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            # Simple trend chart
                            st.line_chart(m_plot, x='Date_Clean', y='Val', color="#3b82f6")
                        with col2:
                            st.metric("Total", f"{m_plot['Val'].sum():,.0f}")
                            st.dataframe(m_plot[['Date_Clean', 'Val']], hide_index=True)
                        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("Connection failed. Check Google Sheet publishing.")
