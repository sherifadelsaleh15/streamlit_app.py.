import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS

# Import our custom modules
from modules.data_loader import load_and_preprocess_data
from modules.analytics import calculate_kpis
from modules.visualizations import render_metric_chart
from modules.ml_models import generate_forecast

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric { 
        background-color: white; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #e2e8f0; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INITIALIZATION ---
@st.cache_data(ttl=60)
def get_data():
    return load_and_preprocess_data()

df = get_data()

# --- 3. MAIN APP LOGIC ---
if not df.empty:
    # --- SIDEBAR FILTERS ---
    st.sidebar.title("🎮 Dashboard Controls")
    
    # Tab/Source Selection
    selected_tab = st.sidebar.selectbox("📂 Select Data Source", TABS)
    
    # Filter data by the selected Tab/Source first
    tab_df = df[df['Source'] == selected_tab].copy()
    
    st.sidebar.markdown("---")
    
    # Objective Filter (Cascading)
    obj_list = sorted(tab_df['Objective'].unique())
    sel_objs = st.sidebar.multiselect("🎯 Filter Objectives", obj_list)
    if sel_objs:
        tab_df = tab_df[tab_df['Objective'].isin(sel_objs)]
        
    # OKR Filter (Cascading)
    okr_list = sorted(tab_df['OKR'].unique())
    sel_okrs = st.sidebar.multiselect("📊 Filter OKRs", okr_list)
    if sel_okrs:
        tab_df = tab_df[tab_df['OKR'].isin(sel_okrs)]

    # --- MAIN CONTENT AREA ---
    st.title(f"{APP_TITLE}")
    st.caption(f"Viewing Source: **{selected_tab}**")

    # KPI Summary Row
    stats = calculate_kpis(tab_df)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.metric("Total Volume", f"{stats.get('total_value', 0):,.0f}")
    with kpi_col2:
        st.metric("Avg Monthly", f"{stats.get('avg_value', 0):,.1f}")
    with kpi_col3:
        st.metric("Objectives", stats.get('active_objectives', 0))
    with kpi_col4:
        st.metric("Active Regions", stats.get('active_regions', 0))

    st.markdown("---")

    # --- CHART GRID ---
    st.subheader(f"📈 Performance Trends: {selected_tab}")
    
    # Get unique metrics in the filtered data
    metrics = sorted(tab_df['Metric'].unique())
    
    if metrics:
        # Create a 2-column layout for charts
        chart_cols = st.columns(2)
        
        for idx, metric_name in enumerate(metrics):
            # Prepare data for this specific chart
            metric_data = tab_df[tab_df['Metric'] == metric_name]
            
            # Generate the 6-month forecast
            f_df = generate_forecast(metric_data)
            
            # Alternate placing charts in col 1 and col 2
            with chart_cols[idx % 2]:
                render_metric_chart(tab_df, metric_name, forecast_df=f_df)
    else:
        st.info("No metrics found for the selected filters.")

    # --- DATA HEALTH CHECK (OPTIONAL) ---
    with st.expander("🔍 View Raw Filtered Data"):
        st.dataframe(tab_df.sort_values('dt', ascending=False), use_container_width=True)

else:
    st.error("❌ No data loaded. Please check your `config.py` and ensure your Google Sheet is Published to Web.")
    st.info("💡 Hint: Ensure your SHEET_ID is correct and the Tab names match exactly.")

# --- FOOTER ---
if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()
