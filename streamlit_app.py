import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="2026 OKR Dashboard", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9; border-radius: 4px 4px 0px 0px; padding: 10px 20px;
    }
    .metric-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 20px; margin-bottom: 20px; border-left: 5px solid #3b82f6;
    }
    .okr-id { color: #64748b; font-weight: 600; font-size: 0.8rem; }
    .metric-label { color: #1e293b; font-weight: 700; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_all_tabs():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_chunks = []
    
    mapping = {
        "Objective_ID": "Objective", "Objective ID": "Objective",
        "Region/Country": "Region", "Region": "Region",
        "Date_Month": "Date_Raw", "Month": "Date_Raw",
        "Metric_Name": "Metric", "Metric Name": "Metric",
        "OKR_ID": "OKR"
    }

    for tab in tabs:
        encoded = urllib.parse.quote(tab)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        try:
            df = pd.read_csv(url).dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.rename(columns=mapping)

            # Determine numeric value column
            val_col = next((c for c in ['Value', 'Views', 'Clicks', 'KeywordClicks', 'Active Users'] if c in df.columns), None)
            
            if val_col:
                temp = pd.DataFrame()
                temp['Objective'] = df['Objective'].astype(str).fillna("No Obj")
                temp['Region'] = df['Region'].astype(str).fillna("Global")
                temp['OKR'] = df['OKR'].astype(str).fillna("N/A")
                temp['Metric'] = df['Metric'].astype(str).fillna(tab)
                temp['Val'] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
                temp['Tab_Source'] = tab
                
                # Standardize time
                temp['dt'] = pd.to_datetime(df['Date_Raw'], errors='coerce', dayfirst=True)
                temp.loc[temp['dt'].isna(), 'dt'] = pd.to_datetime(df['Date_Raw'], errors='coerce')
                temp['Month_Year'] = temp['dt'].dt.strftime('%b %Y')
                
                all_chunks.append(temp.reset_index(drop=True))
        except: continue

    return pd.concat(all_chunks, ignore_index=True) if all_chunks else pd.DataFrame()

# --- 3. FILTER LOGIC ---
df = load_all_tabs()

if not df.empty:
    # --- SIDEBAR: HIERARCHICAL FILTERS ---
    st.sidebar.header("Global Filters")
    
    # 1. Filter by Objective
    obj_opts = sorted(df['Objective'].unique())
    sel_objs = st.sidebar.multiselect("Select Objectives", obj_opts, default=obj_opts)
    df_filtered = df[df['Objective'].isin(sel_objs)]

    # 2. Filter by OKR (Cascaded)
    okr_opts = sorted(df_filtered['OKR'].unique())
    sel_okrs = st.sidebar.multiselect("Select OKRs", okr_opts, default=okr_opts)
    df_filtered = df_filtered[df_filtered['OKR'].isin(sel_okrs)]

    # 3. Filter by Region (Cascaded)
    reg_opts = sorted(df_filtered['Region'].unique())
    sel_regs = st.sidebar.multiselect("Select Regions", reg_opts, default=reg_opts)
    df_filtered = df_filtered[df_filtered['Region'].isin(sel_regs)]

    # 4. Filter by Month
    month_opts = df_filtered.sort_values('dt')['Month_Year'].unique().tolist()
    sel_months = st.sidebar.multiselect("Select Timeline", month_opts, default=month_opts)
    df_filtered = df_filtered[df_filtered['Month_Year'].isin(sel_months)]

    # --- MAIN VIEW: TABS ---
    tab_list = ["Strategic Overview"] + sorted(df['Tab_Source'].unique().tolist())
    st_tabs = st.tabs(tab_list)

    for i, tab_name in enumerate(tab_list):
        with st_tabs[i]:
            # Slice data for this specific tab view
            if tab_name == "Strategic Overview":
                view_df = df_filtered
            else:
                view_df = df_filtered[df_filtered['Tab_Source'] == tab_name]

            if view_df.empty:
                st.info("No data matches current filters for this section.")
                continue

            # --- HIERARCHICAL RENDERING ---
            for obj in sorted(view_df['Objective'].unique()):
                st.markdown(f"### 🎯 {obj}")
                obj_data = view_df[view_df['Objective'] == obj]
                
                for okr in sorted(obj_data['OKR'].unique()):
                    okr_data = obj_data[obj_data['OKR'] == okr]
                    
                    # Grouping Metrics under OKR
                    with st.expander(f"OKR {okr} Metrics", expanded=True):
                        metrics = okr_data['Metric'].unique()
                        cols = st.columns(min(len(metrics), 2))
                        
                        for idx, m_name in enumerate(metrics):
                            m_data = okr_data[okr_data['Metric'] == m_name].sort_values('dt')
                            with cols[idx % 2]:
                                st.markdown(f"""
                                    <div class="metric-card">
                                        <div class="okr-id">DATA SOURCE: {m_data['Tab_Source'].iloc[0]}</div>
                                        <div class="metric-label">{m_name}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                st.area_chart(m_data, x='Month_Year', y='Val', color="#3b82f6")
                                
                                c1, c2 = st.columns(2)
                                c1.metric("Sum", f"{m_data['Val'].sum():,.1f}")
                                c2.metric("Monthly Avg", f"{m_data['Val'].mean():,.1f}")
else:
    st.error("No data found. Ensure your Google Sheet tabs are published to web as CSV.")
