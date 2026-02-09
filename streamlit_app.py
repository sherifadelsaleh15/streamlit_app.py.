import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. PREMIUM STYLING ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
        background-color: #f8fafc;
        color: #1e293b;
    }
    
    .obj-section-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 40px;
        margin-bottom: 20px;
        padding-left: 10px;
        border-left: 6px solid #3b82f6;
    }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    .card-metric-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: #2563eb;
        margin-bottom: 2px;
    }

    .card-obj-subtitle {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 15px;
    }

    .stat-label { font-size: 0.8rem; font-weight: 600; color: #94a3b8; }
    .stat-value { font-size: 2.2rem; font-weight: 700; color: #0f172a; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def fetch_data(tab_name):
    encoded_name = urllib.parse.quote(tab_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping to find Metric Name and Objective
        mapping = {
            'Month': 'Month', 'Date_Month': 'Month', 'Date Month': 'Month',
            'Region/Country': 'Region', 'Region': 'Region',
            'Objective ID': 'Objective', 'Objective_ID': 'Objective',
            'Metric Name': 'Metric_Name', 'Metric_Name': 'Metric_Name', 
            'OKR_ID': 'Metric_Name', 'Page Path': 'Metric_Name', 
            'Query': 'Metric_Name', 'Social Network': 'Metric_Name'
        }
        df = df.rename(columns=mapping)
        df = df.loc[:, ~df.columns.duplicated()]
        
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
            
        return df
    except:
        return pd.DataFrame()

# --- 3. NAVIGATION ---
tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.selectbox("Data Layer", tabs)
df = fetch_data(selected_tab)

# --- 4. DASHBOARD ---
if not df.empty:
    st.title(f"Performance Analysis: {selected_tab}")
    
    # Global Filters
    with st.expander("Filter Data", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            m_list = sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else []
            sel_m = st.multiselect("Months", m_list, default=m_list)
        with c2:
            r_list = sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else []
            sel_r = st.multiselect("Regions", r_list, default=r_list)

    f_df = df.copy()
    if sel_m and 'Month' in f_df.columns: f_df = f_df[f_df['Month'].isin(sel_m)]
    if sel_r and 'Region' in f_df.columns: f_df = f_df[f_df['Region'].isin(sel_r)]

    # --- HIERARCHY RENDERER ---
    obj_col = 'Objective' if 'Objective' in f_df.columns else None
    met_col = 'Metric_Name' if 'Metric_Name' in f_df.columns else None
    
    if not obj_col:
        f_df['Objective'] = "Standard Objectives"
        obj_col = 'Objective'

    if met_col and 'Value' in f_df.columns:
        for obj in f_df[obj_col].unique():
            st.markdown(f'<div class="obj-section-header">{obj}</div>', unsafe_allow_html=True)
            
            obj_data = f_df[f_df[obj_col] == obj]
            for metric in obj_data[met_col].unique():
                m_subset = obj_data[obj_data[met_col] == metric]
                if 'Month' in m_subset.columns: m_subset = m_subset.sort_values('Month')

                # THE CARD
                with st.container():
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    
                    # Explicit Metric Name and Objective Label
                    st.markdown(f'<div class="card-metric-name">{metric}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="card-obj-subtitle">Objective: {obj}</div>', unsafe_allow_html=True)
                    
                    c_left, c_right = st.columns([3, 1])
                    with c_left:
                        st.area_chart(m_subset, x='Month' if 'Month' in m_subset.columns else None, y='Value', color="#2563eb")
                    with c_right:
                        total = m_subset['Value'].sum()
                        st.markdown('<div class="stat-label">AGGREGATE VALUE</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="stat-value">{total:,.0f}</div>', unsafe_allow_html=True)
                        st.dataframe(m_subset[['Month', 'Value']], hide_index=True, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.dataframe(f_df)
else:
    st.error("No data found.")
