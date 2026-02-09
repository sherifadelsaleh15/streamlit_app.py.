import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Clean Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background-color: #0f172a !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=300)
def fetch_tab(name):
    encoded_name = urllib.parse.quote(name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    try:
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        return data
    except:
        return pd.DataFrame()

# --- 3. NAVIGATION ---
st.title("🚀 2026 Strategy Command Center")
st.caption("Integrated Marketing & OKR Intelligence")

# EXACT MATCH to your Google Sheet tabs
tab_list = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
ui_tabs = st.tabs(tab_list)

# --- 4. DASHBOARD LOGIC ---
for i, tab_name in enumerate(tab_list):
    with ui_tabs[i]:
        df = fetch_tab(tab_name)
        
        if not df.empty:
            # Metrics Row
            nums = df.select_dtypes(include=['number']).columns
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                val = df[nums[0]].sum() if not nums.empty else len(df)
                st.metric(f"Total {nums[0] if not nums.empty else 'Rows'}", f"{val:,.0f}")
            with m2:
                st.metric("Entries", len(df))
            with m3:
                # Finding a dimension for "Scope"
                scope = df.iloc[:, 0].nunique()
                st.metric("Unique Segments", scope)
            with m4:
                st.metric("System", "Online", delta="Healthy")

            # Filters & Content
            col_chart, col_table = st.columns([1.5, 1])
            
            with col_chart:
                st.markdown(f"### {tab_name} Analysis")
                if not nums.empty:
                    # Look for Month/Date column
                    x_axis = 'Month' if 'Month' in df.columns else df.columns[0]
                    st.area_chart(df, x=x_axis, y=nums[0], color="#0f172a")
                else:
                    st.info("No numeric columns found for trend mapping.")

            with col_table:
                st.markdown("### Data Preview")
                st.dataframe(df.head(15), use_container_width=True, hide_index=True)

            # --- SMART AI SEARCH ---
            st.divider()
            st.markdown(f"### 🤖 AI Search: {tab_name}")
            user_q = st.chat_input(f"Ask about {tab_name}...", key=f"chat_{tab_name}")

            if user_q:
                with st.chat_message("assistant"):
                    # Smarter filtering logic (Keywords)
                    words = user_q.lower().split()
                    results = df.copy()
                    for word in words:
                        results = results[results.apply(lambda row: row.astype(str).str.lower().str.contains(word).any(), axis=1)]
                    
                    if not results.empty:
                        st.write(f"I found **{len(results)}** matching records:")
                        st.dataframe(results, use_container_width=True)
                        if not nums.empty:
                            st.success(f"**Quick Insight:** The total **{nums[0]}** for this search is **{results[nums[0]].sum():,.0f}**")
                    else:
                        st.warning("No matches found. Try using single keywords.")
        else:
            st.error(f"Tab '{tab_name}' not found. Please check spelling in Google Sheets.")
