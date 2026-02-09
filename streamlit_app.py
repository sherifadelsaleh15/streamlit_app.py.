import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .metric-card {
        background: white; border: 1px solid #e2e8f0; padding: 20px;
        border-radius: 12px; margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .metric-header { font-size: 1.2rem; font-weight: 700; color: #1e293b; margin-bottom: 2px; }
    .obj-tag { font-size: 0.75rem; color: #3b82f6; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE NORMALIZATION ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_and_normalize_all():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_data = []

    # Map variant names to standard keys
    mapping = {
        "Objective ID": "Objective", "Objective_ID": "Objective",
        "Region/Country": "Region", "Region": "Region",
        "OKR_ID": "OKR_Label", "OKR ID": "OKR_Label",
        "Metric Name": "OKR_Label", "Metric_Name": "OKR_Label",
        "Page Path": "OKR_Label", "Query": "OKR_Label",
        "Month": "Date_Month", "Date_Month": "Date_Month", "Date Month": "Date_Month"
    }

    for tab in tabs:
        encoded_name = urllib.parse.quote(tab)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
        try:
            df = pd.read_csv(url)
            
            # CRITICAL FIX: Strip whitespace and remove duplicate column names
            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated()].copy() 
            
            # Apply mapping
            df = df.rename(columns=mapping)
            
            # Identify columns that contain numbers (Value, Views, Clicks, etc.)
            potential_values = ['Value', 'Views', 'Active Users', 'Clicks', 'Avg Position', 'Followers', 'Engagement']
            val_cols = [c for c in df.columns if c in potential_values]

            for v_col in val_cols:
                temp_df = df.copy()
                temp_df['Metric_Name'] = v_col
                temp_df['Final_Value'] = pd.to_numeric(temp_df[v_col], errors='coerce').fillna(0)
                temp_df['Source_Sheet'] = tab
                
                # Standardize Month display
                if 'Date_Month' in temp_df.columns:
                    temp_df['Date_Month'] = pd.to_datetime(temp_df['Date_Month'], errors='coerce').dt.strftime('%b %Y')
                
                # Filter to only necessary columns to avoid concat conflicts
                cols = ['Objective', 'Region', 'OKR_Label', 'Metric_Name', 'Date_Month', 'Final_Value', 'Source_Sheet']
                available = [c for c in cols if c in temp_df.columns]
                all_data.append(temp_df[available])
        except Exception as e:
            continue

    if not all_data:
        return pd.DataFrame()
        
    # Final concat
    combined = pd.concat(all_data, ignore_index=True)
    return combined

# --- 3. DATA LOADING & TABS ---
df_master = load_and_normalize_all()

if not df_master.empty:
    st.title("Strategic Performance Dashboard")
    
    # Generate unique months for filtration (Sorted Chronologically)
    month_order = ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026', 
                   'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026']
    available_months = [m for m in month_order if m in df_master['Date_Month'].unique()]
    
    # Sidebar Filters
    st.sidebar.header("Global Filters")
    sel_months = st.sidebar.multiselect("Filtration of Month", available_months, default=available_months)
    
    regions = sorted(df_master['Region'].unique().astype(str).tolist()) if 'Region' in df_master.columns else []
    sel_regions = st.sidebar.multiselect("Filtration of Region", regions, default=regions)

    # Sheet Tabs
    sheet_options = ["All Sheets"] + sorted(df_master['Source_Sheet'].unique().tolist())
    st_tabs = st.tabs(sheet_options)

    for i, tab_name in enumerate(sheet_options):
        with st_tabs[i]:
            # Apply Filtration
            view_df = df_master.copy()
            if tab_name != "All Sheets":
                view_df = view_df[view_df['Source_Sheet'] == tab_name]
            
            view_df = view_df[view_df['Date_Month'].isin(sel_months)]
            if 'Region' in view_df.columns:
                view_df = view_df[view_df['Region'].isin(sel_regions)]

            if view_df.empty:
                st.info("No data available for these filters.")
                continue

            # Group by Objective
            objs = view_df['Objective'].unique() if 'Objective' in view_df.columns else ["General"]
            
            for obj in objs:
                st.markdown(f"### {obj}")
                obj_data = view_df[view_df['Objective'] == obj] if 'Objective' in view_df.columns else view_df
                
                # Display unique OKRs within the objective
                metrics = obj_data.groupby(['OKR_Label', 'Metric_Name'])
                
                for (label, m_type), m_df in metrics:
                    with st.container():
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="obj-tag">{m_type}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-header">{label}</div>', unsafe_allow_html=True)
                        
                        chart_col, stat_col = st.columns([3, 1])
                        
                        with chart_col:
                            # Ensure chart follows time order
                            m_df['temp_date'] = pd.to_datetime(m_df['Date_Month'], format='%b %Y')
                            m_df = m_df.sort_values('temp_date')
                            st.area_chart(m_df, x='Date_Month', y='Final_Value', color="#1e293b")
                        
                        with stat_col:
                            total = m_df['Final_Value'].sum()
                            st.metric("Total", f"{total:,.0f}")
                            st.dataframe(m_df[['Date_Month', 'Final_Value']], hide_index=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. AI CHAT ---
    st.divider()
    st.subheader("Intelligence Assistant")
    q = st.chat_input("Ask a question about the data...")
    if q:
        matches = df_master[df_master.apply(lambda r: r.astype(str).str.lower().str.contains(q.lower()).any(), axis=1)]
        st.dataframe(matches)
else:
    st.error("Data synchronization failed. Please check your Google Sheets connection.")
