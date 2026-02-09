import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. PREMIUM STYLING & FONT ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
        background-color: #f8fafc;
        color: #1e293b;
    }
    
    /* Objective Header */
    .obj-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 30px;
        margin-bottom: 15px;
        border-left: 5px solid #3b82f6;
        padding-left: 15px;
        background: white;
        padding-top: 10px;
        padding-bottom: 10px;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* Metric Card */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .metric-title {
        font-size: 1rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ROBUST DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def fetch_data(tab_name):
    encoded_name = urllib.parse.quote(tab_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        df = pd.read_csv(url)
        # 1. Clean Headers: remove spaces
        df.columns = [str(c).strip() for c in df.columns]
        
        # 2. Smart Mapping: Align different sheets to a common schema
        mapping = {
            'Month': 'Month', 'Date_Month': 'Month', 'Date Month': 'Month',
            'Region/Country': 'Region', 'Region': 'Region',
            'Objective ID': 'Objective', 'Objective_ID': 'Objective',
            # Map specific items to 'Metric_Label' for the chart title
            'Metric Name': 'Metric_Label', 'OKR_ID': 'Metric_Label',
            'Page Path': 'Metric_Label', 'Query': 'Metric_Label',
            'Social Network': 'Metric_Label', 'Channel': 'Metric_Label'
        }
        df = df.rename(columns=mapping)
        
        # 3. Drop duplicate columns to prevent AttributeError
        df = df.loc[:, ~df.columns.duplicated()]
        
        # 4. Ensure Value is numeric
        if 'Value' in df.columns:
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
            
        return df
    except:
        return pd.DataFrame()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("NAVIGATOR")
tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.radio("Select Data Source", tabs)

df = fetch_data(selected_tab)

# --- 4. DASHBOARD RENDERER ---
if not df.empty:
    st.title(f"📊 {selected_tab.replace('_', ' ')}")
    
    # --- FILTERS ---
    with st.expander("🔎 Filter Options", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            # Month Filter
            months = sorted(df['Month'].unique().tolist()) if 'Month' in df.columns else []
            sel_months = st.multiselect("Select Months", months, default=months, key=f"m_{selected_tab}")
        with c2:
            # Region Filter
            regions = sorted(df['Region'].unique().tolist()) if 'Region' in df.columns else []
            sel_regions = st.multiselect("Select Regions", regions, default=regions, key=f"r_{selected_tab}")

    # Apply Filters
    f_df = df.copy()
    if sel_months and 'Month' in f_df.columns: f_df = f_df[f_df['Month'].isin(sel_months)]
    if sel_regions and 'Region' in f_df.columns: f_df = f_df[f_df['Region'].isin(sel_regions)]

    # --- HIERARCHY LOGIC: OBJECTIVE -> METRIC ---
    
    # 1. Identify Grouping Column (Objective)
    obj_col = 'Objective' if 'Objective' in f_df.columns else None
    
    # 2. Identify Item Column (The specific Metric/Page/Query)
    item_col = 'Metric_Label' if 'Metric_Label' in f_df.columns else None
    
    # FALLBACK: If no explicit Objective column, treat the Item as the top level
    if not obj_col and item_col:
        # Create a dummy objective for grouping
        f_df['Objective'] = "General Items"
        obj_col = 'Objective'

    if obj_col and item_col and 'Value' in f_df.columns:
        # Loop through unique Objectives
        unique_objs = f_df[obj_col].unique()
        
        for obj in unique_objs:
            # HEADER: Display the Objective Name
            st.markdown(f'<div class="obj-header">{obj}</div>', unsafe_allow_html=True)
            
            # Get all metrics belonging to this objective
            obj_data = f_df[f_df[obj_col] == obj]
            unique_metrics = obj_data[item_col].unique()
            
            # Create a Grid for the charts
            for metric in unique_metrics:
                metric_data = obj_data[obj_data[item_col] == metric]
                
                # Sort Chronologically if possible
                if 'Month' in metric_data.columns:
                    metric_data = metric_data.sort_values('Month')

                # CHART CARD
                with st.container():
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    c_left, c_right = st.columns([3, 1])
                    
                    with c_left:
                        st.markdown(f'<div class="metric-title">{metric}</div>', unsafe_allow_html=True)
                        # High-quality Area Chart
                        st.area_chart(metric_data, x='Month' if 'Month' in metric_data.columns else None, y='Value', color="#3b82f6")
                    
                    with c_right:
                        total = metric_data['Value'].sum()
                        st.markdown('<div class="metric-title">TOTAL</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-value">{total:,.0f}</div>', unsafe_allow_html=True)
                        st.dataframe(metric_data[['Month', 'Value']], hide_index=True, use_container_width=True, height=150)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Data structure not recognized for charting. Showing raw table.")
        st.dataframe(f_df, use_container_width=True)

    # --- 5. AI CHAT ---
    st.markdown("---")
    st.subheader("🤖 Strategy Assistant")
    q = st.chat_input("Ask about any objective or metric...")
    if q:
        with st.chat_message("assistant"):
            words = q.lower().split()
            res = df.copy()
            for w in words:
                res = res[res.apply(lambda r: r.astype(str).str.lower().str.contains(w).any(), axis=1)]
            if not res.empty:
                st.write(f"Found {len(res)} results:")
                st.dataframe(res)
            else:
                st.write("No matches found.")

else:
    st.error("Unable to load data. Please check your Google Sheet tabs.")
