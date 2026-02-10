import streamlit as st
import pandas as pd
from config import APP_TITLE, TABS

# Modules
from modules.data_loader import load_and_preprocess_data
from modules.analytics import calculate_kpis
from modules.visualizations import render_metric_chart
from modules.ml_models import generate_forecast
# MUST INCLUDE ALL FOUR HERE:
from modules.ui_components import apply_custom_css, render_header, render_footer, render_sidebar_logo 
import utils 

st.set_page_config(page_title=APP_TITLE, layout="wide")

# 1. Apply Styles
apply_custom_css()

# 2. Load Data
df = load_and_preprocess_data()

if not df.empty:
    # 3. Sidebar
    render_sidebar_logo() # Now this will work!
    st.sidebar.title("Dashboard Controls")
    
    sel_tab = st.sidebar.selectbox("Select Data Source", TABS)
    # ... rest of your code
