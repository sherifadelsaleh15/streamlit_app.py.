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
    }
    
    .obj-section-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 40px;
        margin-bottom: 20px;
        border-left: 6px solid #3b82f6;
        padding-left: 15px;
    }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04);
    }
    
    .metric-name-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2563eb;
        margin-bottom: 5px;
    }

    .objective-subtitle {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        margin-bottom: 20px;
        display: block;
    }
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
        # Clean headers only (no renaming yet)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Ensure 'Value' is numeric
        val_col = next((c for c in df.columns if c.lower() in ['value', 'views', 'clicks']), None)
        if val_col:
            df[val_col] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
            
        return df, val_col
    except:
        return pd.DataFrame(), None

# --- 3. NAVIGATION ---
tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.selectbox("Data Source", tabs)
df, value_column = fetch_data(selected_tab)

# --- 4. DASHBOARD RENDERER ---
if not df.empty:
    st.title(f"Strategic Review: {selected_tab.replace('_', ' ')}")

    # Identification of Key Columns
    # We look for Objective and Metric/OKR names dynamically
    obj_col = next((c for c in df.columns if 'objective' in c.lower()), None)
    # The Metric Name is usually 'Metric Name', 'OKR_ID', 'Page Path', etc.
    name_col = next((c for c in df.columns if any(x in c.lower() for x in ['metric', 'okr', 'path', 'query', 'network'])), None)

    if name_col and value_column:
        # Group by Objective if it exists
        groups = df[obj_col].unique() if obj_col else ["General Metrics"]
        
        for group in groups:
            st.markdown(f'<div class="obj-section-header">{group}</div>', unsafe_allow_html=True)
            
            # Filter data for this group
            group_df = df[df[obj_col] == group] if obj_col else df
            
            # Unique Metrics in this group
            metrics = group_df[name_col].unique()
            
            for m_name in metrics:
                m_data = group_df[group_df[name_col] == m_name]
                
                # Sort by Month
                month_col = next((c for c in df.columns if 'month' in c.lower()), None)
                if month_col:
                    m_data = m_data.sort_values(month_col)

                # RENDER CARD
                with st.container():
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    
                    # THE FIX: Display the actual name from your spreadsheet column
                    st.markdown(f'<div class="metric-name-header">{m_name}</div>', unsafe_allow_html=True)
                    if obj_col:
                        st.markdown(f'<span class="objective-subtitle">Objective: {group}</span>', unsafe_allow_html=True)
                    
                    col_chart, col_data = st.columns([3, 1])
                    
                    with col_chart:
                        st.area_chart(m_data, x=month_col, y=value_column, color="#2563eb")
                    
                    with col_data:
                        total_val = m_data[value_column].sum()
                        st.metric("Total Progress", f"{total_val:,.0f}")
                        st.dataframe(m_data[[month_col, value_column]], hide_index=True)
                        
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Could not automatically detect Metric or Value columns. Showing raw data.")
        st.dataframe(df)

    # --- 5. SEARCH ---
    st.divider()
    q = st.chat_input("Search for specific keywords...")
    if q:
        res = df[df.apply(lambda r: r.astype(str).str.lower().str.contains(q.lower()).any(), axis=1)]
        st.dataframe(res)
else:
    st.error("Sheet connection failed.")
