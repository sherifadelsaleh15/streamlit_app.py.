import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f9fbff; }
    
    .okr-card {
        background: white; border: 1px solid #e2e8f0; padding: 24px;
        border-radius: 16px; margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .metric-title { font-size: 1.3rem; font-weight: 700; color: #1e293b; margin-bottom: 2px; }
    .type-subtitle { font-size: 0.85rem; color: #3b82f6; text-transform: uppercase; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (STRICT SANITIZATION) ---
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
            # Load raw
            df = pd.read_csv(url)
            
            # --- CRITICAL FIX FOR INVALIDINDEXERROR ---
            # 1. Clean whitespace from headers
            df.columns = [str(c).strip() for c in df.columns]
            # 2. Force unique columns (renames 'Value' to 'Value.1' if it appears twice)
            df.columns = pd.io.common.dedup_names(df.columns, is_unique=False)
            # 3. Drop completely empty rows and reset index
            df = df.dropna(how='all').reset_index(drop=True)
            
            # Rename based on mapping
            df = df.rename(columns=mapping)
            
            # Identify numeric columns
            value_vars = ['Value', 'Views', 'Active Users', 'Clicks', 'Avg Position', 'Followers']
            found_vars = [c for c in df.columns if c in value_vars]

            for v_col in found_vars:
                temp = df.copy()
                temp['Metric_Type'] = v_col
                temp['Actual_Value'] = pd.to_numeric(temp[v_col], errors='coerce').fillna(0)
                temp['Source_Tab'] = tab
                
                # Standardize Month
                if 'Date_Month' in temp.columns:
                    temp['Date_Month'] = pd.to_datetime(temp['Date_Month'], errors='coerce').dt.strftime('%b %Y')
                
                # Filter to only unified schema to avoid concat index collisions
                final_cols = ['Objective', 'Region', 'OKR_Label', 'Metric_Type', 'Date_Month', 'Actual_Value', 'Source_Tab']
                available = [c for c in final_cols if c in temp.columns]
                
                # Drop any remaining duplicated indices in the temp object
                temp = temp[available].loc[:, ~temp[available].columns.duplicated()]
                all_data.append(temp)
        except:
            continue

    if not all_data: return pd.DataFrame()
    
    # Final Concatenation with forced alignment
    return pd.concat(all_data, axis=0, ignore_index=True, sort=False)

# --- 3. DASHBOARD LOGIC ---
master_df = load_and_normalize_all()

if not master_df.empty:
    st.title("2026 Strategy & OKR Dashboard")

    # Chronological sorting reference
    month_order = ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026', 
                   'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026']
    present_months = [m for m in month_order if m in master_df['Date_Month'].unique()]

    # FILTRATION SIDEBAR
    with st.sidebar:
        st.header("Filtration Panel")
        sel_months = st.multiselect("Filtration of Month", present_months, default=present_months)
        
        reg_opts = sorted(master_df['Region'].unique().astype(str).tolist()) if 'Region' in master_df.columns else []
        sel_regions = st.multiselect("Filtration of Region", reg_opts, default=reg_opts)

    # TAB SELECTOR
    tab_names = ["All Performance"] + sorted(master_df['Source_Tab'].unique().tolist())
    dashboard_tabs = st.tabs(tab_names)

    for i, t_name in enumerate(tab_names):
        with dashboard_tabs[i]:
            # Apply Filters
            f_df = master_df.copy()
            if t_name != "All Performance":
                f_df = f_df[f_df['Source_Tab'] == t_name]
            
            f_df = f_df[f_df['Date_Month'].isin(sel_months)]
            if 'Region' in f_df.columns:
                f_df = f_df[f_df['Region'].isin(sel_regions)]

            if f_df.empty:
                st.info("No matching data for these filters.")
                continue

            # --- 4. RENDER BY OBJECTIVE ---
            objectives = f_df['Objective'].unique() if 'Objective' in f_df.columns else ["General"]
            
            for obj in objectives:
                st.markdown(f"### {obj}")
                obj_data = f_df[f_df['Objective'] == obj] if 'Objective' in f_df.columns else f_df
                
                # Group by OKR Label + Metric Type (e.g., "Homepage" + "Views")
                groups = obj_data.groupby(['OKR_Label', 'Metric_Type'])
                
                for (okr_name, m_type), m_df in groups:
                    with st.container():
                        st.markdown('<div class="okr-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="type-subtitle">{m_type}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-title">{okr_name}</div>', unsafe_allow_html=True)
                        
                        c_chart, c_data = st.columns([3, 1])
                        
                        with c_chart:
                            # Time-sorting for chart
                            m_df['sort_key'] = pd.to_datetime(m_df['Date_Month'], format='%b %Y')
                            m_df = m_df.sort_values('sort_key')
                            st.area_chart(m_df, x='Date_Month', y='Actual_Value', color="#1e293b")
                        
                        with c_data:
                            st.metric("Total", f"{m_df['Actual_Value'].sum():,.0f}")
                            st.dataframe(m_df[['Date_Month', 'Actual_Value']], hide_index=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. AI CHAT ---
    st.divider()
    query = st.chat_input("Search metrics or ask a question...")
    if query:
        res = master_df[master_df.apply(lambda r: r.astype(str).str.lower().str.contains(query.lower()).any(), axis=1)]
        st.write(f"Results for '{query}':")
        st.dataframe(res)
else:
    st.error("Data synchronization failed. Verify column headers in all sheet tabs.")
