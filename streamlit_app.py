import streamlit as st
from config import APP_TITLE, TABS

# Modules
from modules.data_loader import load_and_preprocess_data
from modules.analytics import calculate_kpis
from modules.visualizations import render_metric_chart
from modules.ml_models import generate_forecast
from modules.ui_components import apply_custom_css, render_header, render_footer # NEW
import utils # NEW

st.set_page_config(page_title=APP_TITLE, layout="wide")

# 1. Apply Styles
try:
    apply_custom_css()
except:
    pass # Fallback if file isn't found

# 2. Load Data
df = load_and_preprocess_data()

if not df.empty:
    # 3. Sidebar
    st.sidebar.title("Navigation")
    sel_tab = st.sidebar.selectbox("Data Source", TABS)
    
    # NEW: Use utility to show date range in sidebar
    st.sidebar.info(utils.get_date_range_label(df))
    
    filtered_df = df[df['Source'] == sel_tab].copy()
    
    # Filters... (keep your existing multiselect logic here)
    sel_objs = st.sidebar.multiselect("Objectives", sorted(filtered_df['Objective'].unique()))
    if sel_objs:
        filtered_df = filtered_df[filtered_df['Objective'].isin(sel_objs)]

    # 4. Main UI (Using UI Components)
    render_header(APP_TITLE, f"Strategic insights for {selected_tab}") # NEW
    
    stats = calculate_kpis(filtered_df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", f"{stats['total_value']:,.0f}")
    # ... (keep other metrics)

    # 5. Charts... (keep your existing chart loop here)
    st.divider()
    # ... (Chart Loop)

    # 6. Footer
    render_footer() # NEW

else:
    st.error("Data not found.")
