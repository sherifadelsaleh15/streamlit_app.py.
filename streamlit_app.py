import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    
    .okr-card {
        background: white; border: 1px solid #e2e8f0; padding: 20px;
        border-radius: 12px; margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-title { font-size: 1.15rem; font-weight: 700; color: #1e293b; margin-bottom: 2px; }
    .obj-tag { font-size: 0.75rem; color: #3b82f6; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SIMPLIFIED DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_normalized_data():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_chunks = []

    # Map your specific headers to standard internal keys
    mapping = {
        "Objective_ID": "Objective", "Objective ID": "Objective",
        "Region/Country": "Region",
        "Date_Month": "Month", "Date Month": "Month",
        "Metric_Name": "Metric", "Metric Name": "Metric",
        "OKR_ID": "OKR"
    }

    for tab in tabs:
        encoded_name = urllib.parse.quote(tab)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=encoded_name"
        try:
            df = pd.read_csv(url)
            # Clean headers
            df.columns = [str(c).strip() for c in df.columns]
            df = df.rename(columns=mapping)
            
            # Ensure Value is numeric
            if 'Value' in df.columns:
                df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
            
            # Add metadata
            df['Sheet_Source'] = tab
            
            # Keep only the rows that have actual data
            df = df.dropna(subset=['Value']) if 'Value' in df.columns else df
            
            # Select only columns we need for the dashboard to prevent concat errors
            core_cols = ['Objective', 'Region', 'OKR', 'Metric', 'Source', 'Month', 'Value', 'Sheet_Source']
            available = [c for c in core_cols if c in df.columns]
            
            # Force a fresh index for this tab's data
            all_chunks.append(df[available].reset_index(drop=True))
        except:
            continue

    if not all_chunks:
        return pd.DataFrame()
    
    # Concatenate all tabs into one master frame
    return pd.concat(all_chunks, axis=0, ignore_index=True)

# --- 3. DASHBOARD LOGIC ---
master_df = load_normalized_data()

if not master_df.empty:
    st.title("2026 Performance Strategy")

    # Filter Sidebar
    with st.sidebar:
        st.header("Filtration Panel")
        
        # Month Filter
        if 'Month' in master_df.columns:
            # Try to sort months chronologically
            try:
                master_df['dt_temp'] = pd.to_datetime(master_df['Month'], dayfirst=True)
                sorted_months = master_df.sort_values('dt_temp')['Month'].unique().tolist()
            except:
                sorted_months = sorted(master_df['Month'].unique().tolist())
            
            sel_months = st.multiselect("Filtration of Month", sorted_months, default=sorted_months)
        
        # Region Filter
        regions = sorted(master_df['Region'].unique().tolist()) if 'Region' in master_df.columns else []
        sel_regions = st.multiselect("Filtration of Region", regions, default=regions)

    # UI Tabs by Source
    tab_options = ["Summary"] + sorted(master_df['Sheet_Source'].unique().tolist())
    ui_tabs = st.tabs(tab_options)

    for i, tab_name in enumerate(tab_options):
        with ui_tabs[i]:
            # Apply Filters
            f_df = master_df.copy()
            if tab_name != "Summary":
                f_df = f_df[f_df['Sheet_Source'] == tab_name]
            
            if 'Month' in f_df.columns:
                f_df = f_df[f_df['Month'].isin(sel_months)]
            if 'Region' in f_df.columns:
                f_df = f_df[f_df['Region'].isin(sel_regions)]

            if f_df.empty:
                st.info("No data found for the current selection.")
                continue

            # Grouping by Objective -> Metric
            if 'Objective' in f_df.columns:
                for obj in f_df['Objective'].unique():
                    st.markdown(f"### {obj}")
                    obj_subset = f_df[f_df['Objective'] == obj]
                    
                    # Each Metric gets its own chart card
                    unique_metrics = obj_subset['Metric'].unique() if 'Metric' in obj_subset.columns else ["Data"]
                    
                    for m in unique_metrics:
                        m_df = obj_subset[obj_subset['Metric'] == m]
                        
                        # Sort by date for proper charting
                        if 'Month' in m_df.columns:
                            m_df['dt_sort'] = pd.to_datetime(m_df['Month'], dayfirst=True)
                            m_df = m_df.sort_values('dt_sort')

                        with st.container():
                            st.markdown('<div class="okr-card">', unsafe_allow_html=True)
                            
                            # Layout
                            st.markdown(f'<div class="obj-tag">Metric: {m}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-title">{m} Performance</div>', unsafe_allow_html=True)
                            
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.area_chart(m_df, x='Month', y='Value', color="#0f172a")
                            with c2:
                                total = m_df['Value'].sum()
                                st.metric("Aggregate", f"{total:,.2f}" if total < 1 else f"{total:,.0f}")
                                st.dataframe(m_df[['Month', 'Value']], hide_index=True)
                            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.error("Data could not be synchronized. Please ensure your Google Sheet is public and headers match the expected format.")
