import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS, SHEET_ID
from modules.data_loader import load_and_preprocess_data
from modules.visualizations import render_metric_chart, render_top_pages_table
from modules.ui_components import (
    apply_custom_css, render_header, render_footer, 
    render_sidebar_logo, render_pdf_button
)

# Initialize
st.set_page_config(page_title=APP_TITLE, layout="wide")
apply_custom_css()

# Load Data from Google Sheets
@st.cache_data(ttl=600)
def get_data():
    # This logic assumes your data_loader uses the SHEET_ID from config
    return load_and_preprocess_data()

df_dict = get_data() # Returns a dictionary of DataFrames {TabName: DataFrame}

# 1. SIDEBAR
render_sidebar_logo()
st.sidebar.title("Data Navigation")
sel_tab = st.sidebar.selectbox("Select Dashboard Tab", TABS)

# Get the specific data for this tab
tab_df = df_dict.get(sel_tab, pd.DataFrame())

if not tab_df.empty:
    # Filters
    st.sidebar.markdown("---")
    show_table = st.sidebar.checkbox("📋 Show Raw Data Table", value=False)
    render_pdf_button()

    # 2. MAIN HEADER
    render_header(APP_TITLE, f"Performance analysis for {sel_tab}")

    # 3. TOP ANALYSIS (GSC/GA4 Detection)
    if any(k in sel_tab.upper() for k in ["GSC", "GA4", "TOP_PAGES"]):
        render_top_pages_table(tab_df)
        st.divider()

    # 4. TREND CHARTS
    st.subheader("Monthly Growth Trends")
    # Identify value columns (Numeric)
    numeric_cols = tab_df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        cols = st.columns(len(numeric_cols[:2])) # Show up to 2 main metrics
        for i, col_name in enumerate(numeric_cols[:2]):
            with cols[i]:
                st.write(f"**Trend: {col_name}**")
                render_metric_chart(tab_df, col_name)

    # 5. RAW DATA TABLE (The request for each sheet)
    if show_table:
        st.divider()
        st.subheader(f"Raw Records: {sel_tab}")
        
        search = st.text_input("🔍 Search within this table...", "")
        if search:
            display_df = tab_df[tab_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        else:
            display_df = tab_df
            
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    render_footer()
else:
    st.warning(f"Could not find data for tab: {sel_tab}. Please check Google Sheet tab names.")
