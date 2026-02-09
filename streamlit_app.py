import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
    .metric-card {
        background: white; border: 1px solid #e2e8f0; padding: 24px;
        border-radius: 12px; margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-title { font-size: 1.2rem; font-weight: 700; color: #1e293b; }
    .metric-type { font-size: 0.75rem; color: #3b82f6; text-transform: uppercase; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (THE ULTIMATE FIX) ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_and_normalize_all():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_data = []

    # Column Mapping
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
            # Load raw data
            df = pd.read_csv(url)
            
            # 1. DROP ALL COMPLETELY EMPTY ROWS/COLUMNS
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            # 2. FORCE UNIQUE COLUMNS (The Fix for InvalidIndexError)
            # This ensures even if you have multiple 'Metric Name' columns, they are renamed
            df.columns = [str(c).strip() for c in df.columns]
            df = df.T.drop_duplicates().T  # Transpose-deduplicate-transpose method
            df.columns = pd.io.common.dedup_names(df.columns, is_unique=False)
            
            # 3. RESET INDEX COMPLETELY
            df = df.reset_index(drop=True)
            df = df.rename(columns=mapping)
            
            # 4. Value Extraction
            val_vars = ['Value', 'Views', 'Active Users', 'Clicks', 'Avg Position', 'Followers']
            found_vars = [c for c in df.columns if c in val_vars]

            for v_col in found_vars:
                temp = df.copy()
                temp['Metric_Source'] = v_col
                temp['Final_Value'] = pd.to_numeric(temp[v_col], errors='coerce').fillna(0)
                temp['Origin_Sheet'] = tab
                
                if 'Date_Month' in temp.columns:
                    temp['Date_Month'] = pd.to_datetime(temp['Date_Month'], errors='coerce').dt.strftime('%b %Y')
                
                # Keep ONLY standardized columns to prevent concat collision
                cols = ['Objective', 'Region', 'OKR_Label', 'Metric_Source', 'Date_Month', 'Final_Value', 'Origin_Sheet']
                available = [c for c in cols if c in temp.columns]
                
                # Final safeguard: ensure this slice has unique index and columns
                final_slice = temp[available].copy()
                final_slice = final_slice.loc[:, ~final_slice.columns.duplicated()]
                all_data.append(final_slice.reset_index(drop=True))
                
        except Exception:
            continue

    if not all_data:
        return pd.DataFrame()
    
    # 5. CONCAT WITH STRICK ALIGNMENT
    # Axis=0 stacks them, ignore_index=True ensures the final dataframe has a unique 0-N index
    return pd.concat(all_data, axis=0, ignore_index=True, sort=False)

# --- 3. DASHBOARD LOGIC ---
master_df = load_and_normalize_all()

if not master_df.empty:
    st.title("Performance Management Dashboard")

    # Chronological Months
    month_order = ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026', 
                   'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026']
    avail_m = [m for m in month_order if m in master_df['Date_Month'].unique()]

    # SIDEBAR FILTRATION
    st.sidebar.header("Filtration Bar")
    sel_m = st.sidebar.multiselect("Filtration of Month", avail_m, default=avail_m)
    
    reg_list = sorted(master_df['Region'].unique().astype(str).tolist()) if 'Region' in master_df.columns else []
    sel_r = st.sidebar.multiselect("Filtration of Region", reg_list, default=reg_list)

    # UI TABS
    sheet_tabs = ["Summary"] + sorted(master_df['Origin_Sheet'].unique().tolist())
    st_tabs = st.tabs(sheet_tabs)

    for i, tab_name in enumerate(sheet_tabs):
        with st_tabs[i]:
            view_df = master_df.copy()
            if tab_name != "Summary":
                view_df = view_df[view_df['Origin_Sheet'] == tab_name]
            
            view_df = view_df[view_df['Date_Month'].isin(sel_m)]
            if 'Region' in view_df.columns:
                view_df = view_df[view_df['Region'].isin(sel_r)]

            if view_df.empty:
                st.info("No matching data found.")
                continue

            # RENDER BY OBJECTIVE
            objs = view_df['Objective'].unique() if 'Objective' in view_df.columns else ["Uncategorized"]
            for obj in objs:
                st.markdown(f"### {obj}")
                subset = view_df[view_df['Objective'] == obj]
                
                groups = subset.groupby(['OKR_Label', 'Metric_Source'])
                for (label, m_type), m_df in groups:
                    with st.container():
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-type">{m_type}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-title">{label}</div>', unsafe_allow_html=True)
                        
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            m_df['sort_dt'] = pd.to_datetime(m_df['Date_Month'], format='%b %Y')
                            m_df = m_df.sort_values('sort_dt')
                            st.area_chart(m_df, x='Date_Month', y='Final_Value', color="#1e293b")
                        with c2:
                            st.metric("Aggregate", f"{m_df['Final_Value'].sum():,.0f}")
                            st.dataframe(m_df[['Date_Month', 'Final_Value']], hide_index=True)
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. SEARCH ---
    st.divider()
    q = st.chat_input("Search for a specific metric or keyword...")
    if q:
        res = master_df[master_df.apply(lambda r: r.astype(str).str.lower().str.contains(q.lower()).any(), axis=1)]
        st.dataframe(res)
else:
    st.error("Error: Data Indexing Failed. Please check your Excel headers for duplicates.")
