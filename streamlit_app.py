import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. PREMIUM STYLING & FONT ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
    }
    
    /* Objective Section Header */
    .objective-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 40px;
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid #e2e8f0;
    }

    /* Container for each OKR */
    .okr-wrapper {
        margin-bottom: 50px;
        padding: 20px;
        border: 1px solid #f1f5f9;
        border-radius: 8px;
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
        df.columns = [str(c).strip() for c in df.columns]
        
        # Determine Value Column
        val_col = next((c for c in df.columns if c.lower() in ['value', 'views', 'clicks', 'active users']), None)
        if val_col:
            df[val_col] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
            
        return df, val_col
    except:
        return pd.DataFrame(), None

# --- 3. SELECTION & FILTERING ---
tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
selected_tab = st.sidebar.selectbox("Data Source", tabs)
df, value_column = fetch_data(selected_tab)

if not df.empty:
    st.title(f"Strategic View: {selected_tab}")

    # Identify dynamic columns
    obj_col = next((c for c in df.columns if 'objective' in c.lower()), None)
    metric_col = next((c for c in df.columns if any(x in c.lower() for x in ['metric', 'okr', 'path', 'query', 'network'])), None)
    month_col = next((c for c in df.columns if 'month' in c.lower()), None)

    # Sidebar Filter for Month
    if month_col:
        unique_months = sorted(df[month_col].unique().tolist())
        sel_months = st.sidebar.multiselect("Filter Months", unique_months, default=unique_months)
        df = df[df[month_col].isin(sel_months)]

    # --- 4. HIERARCHICAL CHARTING ---
    if metric_col and value_column:
        # Group by Objective
        objectives = df[obj_col].unique() if obj_col else ["General Metrics"]
        
        for obj in objectives:
            st.markdown(f'<div class="objective-header">{obj}</div>', unsafe_allow_html=True)
            
            obj_df = df[df[obj_col] == obj] if obj_col else df
            metrics = obj_df[metric_col].unique()
            
            for m_name in metrics:
                m_data = obj_df[obj_df[metric_col] == m_name]
                if month_col:
                    m_data = m_data.sort_values(month_col)

                with st.container():
                    st.markdown('<div class="okr-wrapper">', unsafe_allow_html=True)
                    
                    chart_col, stat_col = st.columns([3, 1])
                    
                    with chart_col:
                        # Metric Name explicitly at the top of the chart
                        st.subheader(m_name)
                        st.area_chart(
                            m_data, 
                            x=month_col, 
                            y=value_column, 
                            color="#0f172a", # High-contrast professional dark blue
                            use_container_width=True
                        )
                    
                    with stat_col:
                        total = m_data[value_column].sum()
                        st.metric("Total Value", f"{total:,.0f}")
                        st.dataframe(m_data[[month_col, value_column]], hide_index=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.dataframe(df)

    # --- 5. AI SEARCH ---
    st.markdown("---")
    query = st.chat_input("Ask a question about this data...")
    if query:
        res = df[df.apply(lambda r: r.astype(str).str.lower().str.contains(query.lower()).any(), axis=1)]
        st.dataframe(res)
