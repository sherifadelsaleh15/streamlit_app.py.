import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    .metric-card {
        background: white; border: 1px solid #e2e8f0; padding: 24px;
        border-radius: 12px; margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-label { font-size: 1.25rem; font-weight: 700; color: #1e293b; }
    .source-tag { font-size: 0.7rem; color: #64748b; text-transform: uppercase; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (THE FIX) ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_and_normalize_all():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_data = []

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
            # 1. Load and immediately drop empty rows/columns
            df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')
            
            # 2. THE NUCLEAR FIX: Reset the index and dedup columns immediately
            df = df.reset_index(drop=True)
            df.columns = [str(c).strip() for c in df.columns]
            
            # If columns are still duplicated, force them to be unique (e.g., 'Views', 'Views.1')
            if not df.columns.is_unique:
                new_cols = []
                counts = {}
                for col in df.columns:
                    counts[col] = counts.get(col, 0) + 1
                    new_cols.append(f"{col}_{counts[col]}" if counts[col] > 1 else col)
                df.columns = new_cols

            df = df.rename(columns=mapping)
            
            # 3. Numeric Extraction
            val_vars = ['Value', 'Views', 'Active Users', 'Clicks', 'Avg Position', 'Followers']
            found_vars = [c for c in df.columns if c in val_vars]

            for v_col in found_vars:
                temp = df.copy()
                temp['Metric_Source'] = v_col
                temp['Final_Value'] = pd.to_numeric(temp[v_col], errors='coerce').fillna(0)
                temp['Origin_Sheet'] = tab
                
                if 'Date_Month' in temp.columns:
                    temp['Date_Month'] = pd.to_datetime(temp['Date_Month'], errors='coerce').dt.strftime('%b %Y')
                
                # Use ONLY the standardized columns to avoid index/column alignment issues during concat
                cols_to_keep = ['Objective', 'Region', 'OKR_Label', 'Metric_Source', 'Date_Month', 'Final_Value', 'Origin_Sheet']
                temp = temp[[c for c in cols_to_keep if c in temp.columns]]
                
                # FINAL SAFETY: Reset index again for this chunk
                all_data.append(temp.reset_index(drop=True))
        except Exception:
            continue

    if not all_data: return pd.DataFrame()
    
    # 4. CONCAT WITH IGNORE_INDEX
    # This ignores the row labels of the individual dataframes and builds a new 0...N index
    return pd.concat(all_data, ignore_index=True, sort=False)

# --- 3. UI & FILTERS ---
master_df = load_and_normalize_all()

if not master_df.empty:
    st.title("2026 Strategy Performance Dashboard")

    with st.sidebar:
        st.header("Global Filtration")
        
        # Chronological Month Sort
        month_order = ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026', 
                       'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026']
        avail_months = [m for m in month_order if m in master_df['Date_Month'].unique()]
        sel_months = st.multiselect("Filtration of Month", avail_months, default=avail_months)
        
        regions = sorted(master_df['Region'].unique().astype(str).tolist()) if 'Region' in master_df.columns else []
        sel_regions = st.multiselect("Filtration of Region", regions, default=regions)

    # UI TABS
    tabs_list = ["All Data"] + sorted(master_df['Origin_Sheet'].unique().tolist())
    st_tabs = st.tabs(tabs_list)

    for i, tab_name in enumerate(tabs_list):
        with st_tabs[i]:
            f_df = master_df.copy()
            if tab_name != "All Data":
                f_df = f_df[f_df['Origin_Sheet'] == tab_name]
            
            f_df = f_df[f_df['Date_Month'].isin(sel_months)]
            if 'Region' in f_df.columns:
                f_df = f_df[f_df['Region'].isin(sel_regions)]

            if f_df.empty:
                st.info("No data found for current filters.")
                continue

            # Display logic
            objs = f_df['Objective'].unique() if 'Objective' in f_df.columns else ["Uncategorized"]
            for obj in objs:
                st.markdown(f"### {obj}")
                obj_subset = f_df[f_df['Objective'] == obj] if 'Objective' in f_df.columns else f_df
                
                metrics = obj_subset.groupby(['OKR_Label', 'Metric_Source'])
                for (label, m_type), m_df in metrics:
                    with st.container():
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="source-tag">{m_type}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-label">{label}</div>', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            m_df['dt'] = pd.to_datetime(m_df['Date_Month'], format='%b %Y')
                            m_df = m_df.sort_values('dt')
                            st.area_chart(m_df, x='Date_Month', y='Final_Value', color="#1e293b")
                        with col2:
                            st.metric("Total", f"{m_df['Final_Value'].sum():,.0f}")
                            st.dataframe(m_df[['Date_Month', 'Final_Value']], hide_index=True)
                        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.error("Connection failed. Check Google Sheets headers for duplicate names or empty columns.")
