import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfc; }
    
    .okr-card {
        background: white; border: 1px solid #eef2f6; padding: 25px;
        border-radius: 12px; margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .metric-name-label { font-size: 1.25rem; font-weight: 700; color: #0f172a; margin-bottom: 2px; }
    .obj-subtitle { font-size: 0.8rem; color: #3b82f6; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE DATA ENGINE (FIXED FOR INVALIDINDEXERROR) ---
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
            raw_df = pd.read_csv(url)
            
            # --- STEP 1: FIX DUPLICATE COLUMNS ---
            # Strip whitespace from headers
            raw_df.columns = [str(c).strip() for c in raw_df.columns]
            # Remove any columns that are duplicates of each other to fix InvalidIndexError
            df = raw_df.loc[:, ~raw_df.columns.duplicated()].copy()
            
            # --- STEP 2: NORMALIZE SCHEMA ---
            df = df.rename(columns=mapping)
            
            # Detect numeric value columns
            potential_vals = ['Value', 'Views', 'Active Users', 'Clicks', 'Avg Position', 'Followers']
            found_val_cols = [c for c in df.columns if c in potential_vals]

            for v_col in found_val_cols:
                # Melt each value type into its own row set
                temp = df.copy()
                temp['Metric_Source_Name'] = v_col
                temp['Final_Value'] = pd.to_numeric(temp[v_col], errors='coerce').fillna(0)
                temp['Source_Sheet'] = tab
                
                # Standardize Date Month
                if 'Date_Month' in temp.columns:
                    temp['Date_Month'] = pd.to_datetime(temp['Date_Month'], errors='coerce').dt.strftime('%b %Y')
                
                # Keep only core columns to ensure clean concat
                core_cols = ['Objective', 'Region', 'OKR_Label', 'Metric_Source_Name', 'Date_Month', 'Final_Value', 'Source_Sheet']
                keep = [c for c in core_cols if c in temp.columns]
                all_data.append(temp[keep])
        except:
            continue

    if not all_data: return pd.DataFrame()
    
    # Concatenate all sheets safely
    return pd.concat(all_data, ignore_index=True)

# --- 3. DASHBOARD & FILTRATION ---
master_df = load_and_normalize_all()

if not master_df.empty:
    st.title("Strategic OKR Dashboard")

    # Chronological sorting for months
    month_ref = ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026', 
                 'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026']
    actual_months = [m for m in month_ref if m in master_df['Date_Month'].unique()]

    # FILTRATION SIDEBAR
    with st.sidebar:
        st.header("Global Filtration")
        sel_months = st.multiselect("Filtration of Month", actual_months, default=actual_months)
        
        reg_list = sorted(master_df['Region'].unique().astype(str).tolist()) if 'Region' in master_df.columns else []
        sel_regions = st.multiselect("Filtration of Region", reg_list, default=reg_list)

    # TAB SELECTOR
    tab_options = ["All Sheets"] + sorted(master_df['Source_Sheet'].unique().tolist())
    ui_tabs = st.tabs(tab_options)

    for i, t_name in enumerate(tab_options):
        with ui_tabs[i]:
            # Apply Filters
            filtered = master_df.copy()
            if t_name != "All Sheets":
                filtered = filtered[filtered['Source_Sheet'] == t_name]
            
            filtered = filtered[filtered['Date_Month'].isin(sel_months)]
            if 'Region' in filtered.columns:
                filtered = filtered[filtered['Region'].isin(sel_regions)]

            if filtered.empty:
                st.info("No data available for these filter settings.")
                continue

            # --- 4. RENDER CHARTS BY OBJECTIVE ---
            objs = filtered['Objective'].unique() if 'Objective' in filtered.columns else ["General"]
            
            for obj_name in objs:
                st.markdown(f"### {obj_name}")
                obj_subset = filtered[filtered['Objective'] == obj_name] if 'Objective' in filtered.columns else filtered
                
                # Group by Metric (Label + Metric Type)
                metric_groups = obj_subset.groupby(['OKR_Label', 'Metric_Source_Name'])
                
                for (label_val, metric_type), m_df in metric_groups:
                    with st.container():
                        st.markdown('<div class="okr-card">', unsafe_allow_html=True)
                        st.markdown(f'<div class="obj-subtitle">{metric_type}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-name-label">{label_val}</div>', unsafe_allow_html=True)
                        
                        chart_col, stat_col = st.columns([3, 1])
                        
                        with chart_col:
                            # Sort by date for the area chart
                            m_df['sort_dt'] = pd.to_datetime(m_df['Date_Month'], format='%b %Y')
                            m_df = m_df.sort_values('sort_dt')
                            st.area_chart(m_df, x='Date_Month', y='Final_Value', color="#0f172a")
                        
                        with stat_col:
                            st.metric("Total Progress", f"{m_df['Final_Value'].sum():,.0f}")
                            st.dataframe(m_df[['Date_Month', 'Final_Value']], hide_index=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. AI CHAT ---
    st.divider()
    st.subheader("AI Assistant")
    user_input = st.chat_input("Ask a question about your OKRs...")
    if user_input:
        with st.chat_message("assistant"):
            results = master_df[master_df.apply(lambda r: r.astype(str).str.lower().str.contains(user_input.lower()).any(), axis=1)]
            st.write(f"Search results for: {user_input}")
            st.dataframe(results)
else:
    st.error("System could not link to data sources. Please verify sheet headers.")
