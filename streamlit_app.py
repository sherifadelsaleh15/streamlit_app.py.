import streamlit as st
import pandas as pd

# --- 1. SET THEME & PAGE CONFIG ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

# Custom CSS for a "Premium" look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; background-color: #fcfcfd; }
    .stMetric { background-color: white; border: 1px solid #f0f0f1; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .stDataFrame { border-radius: 12px; overflow: hidden; }
    .main-header { font-size: 32px; font-weight: 700; color: #111827; margin-bottom: 5px; }
    .sub-header { color: #6b7280; font-size: 16px; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MULTI-TAB DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=300)
def fetch_data(tab_name):
    # This URL format is the key to accessing different tabs
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab_name}"
    try:
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        return data
    except:
        return pd.DataFrame()

# --- 3. NAVIGATION & TABS ---
st.markdown('<p class="main-header">🚀 Strategy AI Command Center</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">2026 Performance Monitoring & Deep Analysis</p>', unsafe_allow_html=True)

# Define your tab names EXACTLY as they appear in Google Sheets
available_tabs = ["MASTER_FEED", "Social_Media", "Top_Pages", "Keywords"] 
selected_tab = st.tabs(available_tabs)

# --- 4. LOOP THROUGH TABS ---
for i, tab_name in enumerate(available_tabs):
    with selected_tab[i]:
        df = fetch_data(tab_name)
        
        if not df.empty:
            # --- FILTRATION BAR ---
            st.markdown("### 🔍 Smart Filters")
            cols = st.columns(min(len(df.columns), 4))
            filtered_df = df.copy()
            
            # Create dynamic filters based on column names
            for idx, col in enumerate(df.columns[:4]): # Limit to first 4 for layout
                if df[col].dtype == 'object':
                    with cols[idx]:
                        pick = st.multiselect(f"Select {col}", options=df[col].unique(), default=df[col].unique())
                        filtered_df = filtered_df[filtered_df[col].isin(pick)]

            # --- KEY PERFORMANCE INDICATORS ---
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            
            # Auto-detect a numeric column for the metric
            numeric_cols = filtered_df.select_dtypes(include=['number']).columns
            target_col = numeric_cols[0] if not numeric_cols.empty else None

            with m1:
                total = filtered_df[target_col].sum() if target_col else len(filtered_df)
                st.metric(label=f"Total {target_col if target_col else 'Rows'}", value=f"{total:,.0f}")
            with m2:
                st.metric(label="Unique Segments", value=len(filtered_df.iloc[:, 0].unique()))
            with m3:
                st.metric(label="Data Recency", value="Live")
            with m4:
                st.metric(label="Status", value="Healthy", delta="OK")

            # --- VISUALIZATION ---
            st.markdown("### 📊 Analytics Overview")
            v1, v2 = st.columns([2, 1])
            
            with v1:
                if target_col and 'Month' in filtered_df.columns:
                    st.area_chart(filtered_df, x='Month', y=target_col)
                else:
                    st.bar_chart(filtered_df.iloc[:, :2])
            
            with v2:
                st.write("Top 5 Performance")
                st.dataframe(filtered_df.head(5), use_container_width=True)

            # --- THE AI ANALYST ---
            st.markdown("---")
            st.markdown("### 🤖 Chat with this Dataset")
            user_q = st.chat_input(f"Ask about {tab_name}...", key=f"chat_{tab_name}")
            
            if user_q:
                with st.chat_message("assistant"):
                    # Smarter Search Logic
                    q = user_q.lower()
                    results = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(q).any(), axis=1)]
                    if not results.empty:
                        st.write(f"Based on the **{tab_name}** data, I found:")
                        st.dataframe(results)
                    else:
                        st.write("I couldn't find a direct match. Try searching for a specific keyword or value.")

        else:
            st.info(f"Tab '{tab_name}' not found or empty. Ensure tab names match your Google Sheet exactly.")
