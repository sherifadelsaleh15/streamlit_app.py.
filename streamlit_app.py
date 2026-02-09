import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# --- 1. SETTINGS & UI THEME ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .metric-card {
        background: white; border: 1px solid #e2e8f0; padding: 20px;
        border-radius: 12px; margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .metric-header { font-size: 1.1rem; font-weight: 700; color: #1e293b; margin-bottom: 5px; }
    .obj-tag { font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE NORMALIZATION ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_and_normalize_all():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_data = []

    # Column Mapping Dictionary
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
            df.columns = [str(c).strip() for c in df.columns]
            df = df.rename(columns=mapping)
            
            # Identify Value Columns (Handle multi-value sheets like GA4: Views, Active Users)
            potential_values = ['Value', 'Views', 'Active Users', 'Clicks', 'Avg Position', 'Followers']
            val_cols = [c for c in df.columns if c in potential_values]

            for v_col in val_cols:
                temp_df = df.copy()
                temp_df['Metric_Name'] = v_col # Preserve the actual metric name (e.g. "Clicks")
                temp_df['Final_Value'] = pd.to_numeric(temp_df[v_col], errors='coerce').fillna(0)
                temp_df['Source_Sheet'] = tab
                
                # Normalize Date to "Jan 2026" format
                if 'Date_Month' in temp_df.columns:
                    temp_df['Date_Month'] = pd.to_datetime(temp_df['Date_Month'], errors='coerce').dt.strftime('%b %Y')
                
                # Keep only normalized columns
                cols_to_keep = ['Objective', 'Region', 'OKR_Label', 'Metric_Name', 'Date_Month', 'Final_Value', 'Source_Sheet']
                available_cols = [c for c in cols_to_keep if c in temp_df.columns]
                all_data.append(temp_df[available_cols])
        except:
            continue

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

# --- 3. DATA LOADING & FILTRATION ---
df_master = load_and_normalize_all()

if not df_master.empty:
    # Tab selector for the Dashboard
    st.title("Strategic Performance Dashboard")
    
    sheet_list = ["All Data"] + sorted(df_master['Source_Sheet'].unique().tolist())
    selected_sheet = st.tabs(sheet_list) # Using tabs as requested

    with st.sidebar:
        st.header("Global Filters")
        
        # Chronological Month Filter
        if 'Date_Month' in df_master.columns:
            month_order = ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026', 
                           'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026']
            existing_months = [m for m in month_order if m in df_master['Date_Month'].unique()]
            sel_months = st.multiselect("Select Months", existing_months, default=existing_months)
        
        # Region Filter
        regions = sorted(df_master['Region'].unique().astype(str).tolist()) if 'Region' in df_master.columns else []
        sel_regions = st.multiselect("Select Regions", regions, default=regions)

    # Filtering Logic per Tab
    for idx, sheet_name in enumerate(sheet_list):
        with selected_sheet[idx]:
            # Apply Filters
            f_df = df_master.copy()
            if sheet_name != "All Data":
                f_df = f_df[f_df['Source_Sheet'] == sheet_name]
            if 'Date_Month' in f_df.columns:
                f_df = f_df[f_df['Date_Month'].isin(sel_months)]
            if 'Region' in f_df.columns:
                f_df = f_df[f_df['Region'].isin(sel_regions)]

            # --- 4. VISUAL RENDERING ---
            if not f_df.empty:
                # Group by Objective
                objectives = f_df['Objective'].unique() if 'Objective' in f_df.columns else ["General"]
                
                for obj in objectives:
                    st.markdown(f"### {obj}")
                    obj_df = f_df[f_df['Objective'] == obj] if 'Objective' in f_df.columns else f_df
                    
                    # Group by the Metric Identity (Label + Metric Name)
                    # e.g. "Homepage" + "Views"
                    metrics = obj_df.groupby(['OKR_Label', 'Metric_Name'])
                    
                    for (label, m_name), m_df in metrics:
                        with st.container():
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            
                            # Layout: Title + Metric Type
                            st.markdown(f'<div class="obj-tag">{m_name}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-header">{label}</div>', unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                # Ensure data is sorted by date for the chart
                                m_df['date_sort'] = pd.to_datetime(m_df['Date_Month'], format='%b %Y')
                                m_df = m_df.sort_values('date_sort')
                                st.area_chart(m_df, x='Date_Month', y='Final_Value', color="#0f172a")
                            
                            with col2:
                                current_total = m_df['Final_Value'].sum()
                                st.metric("Aggregate", f"{current_total:,.0f}")
                                st.dataframe(m_df[['Date_Month', 'Final_Value']], hide_index=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No data matches the selected filters.")

    # --- 5. AI CHAT ASSISTANT ---
    st.divider()
    st.subheader("Assistant Intelligence")
    query = st.chat_input("Ask about specific OKRs or search for keywords...")
    if query:
        search_res = df_master[df_master.apply(lambda r: r.astype(str).str.lower().str.contains(query.lower()).any(), axis=1)]
        st.write(f"Search results for: {query}")
        st.dataframe(search_res, use_container_width=True)

else:
    st.error("The system could not parse the Excel data. Verify that your Google Sheet is shared and headers are correct.")
