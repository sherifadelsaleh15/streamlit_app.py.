import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide")

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_clean_data():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_chunks = []
    
    mapping = {
        "Objective_ID": "Objective", "Objective ID": "Objective",
        "Region/Country": "Region", "Region": "Region",
        "Date_Month": "Date_Raw", "Month": "Date_Raw",
        "Metric_Name": "Metric", "Metric Name": "Metric",
        "OKR_ID": "OKR"
    }

    for tab in tabs:
        encoded = urllib.parse.quote(tab)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"
        try:
            df = pd.read_csv(url).dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.rename(columns=mapping)

            # Find the best column for values
            val_col = next((c for c in ['Value', 'Views', 'Clicks', 'KeywordClicks', 'Active Users'] if c in df.columns), None)
            
            if val_col:
                temp = pd.DataFrame()
                temp['Objective'] = df['Objective'].astype(str).replace('nan', 'Unassigned')
                temp['OKR'] = df['OKR'].astype(str).replace('nan', 'N/A')
                temp['Region'] = df['Region'].astype(str).replace('nan', 'Global')
                temp['Metric'] = df['Metric'].astype(str).fillna(tab)
                temp['Val'] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
                temp['Source'] = tab
                
                # Robust Date Parsing
                temp['dt'] = pd.to_datetime(df['Date_Raw'], errors='coerce')
                # Sort out any NaT (Not a Time) values that break charts
                temp = temp.dropna(subset=['dt'])
                temp['Month_Display'] = temp['dt'].dt.strftime('%Y-%m') # Using YYYY-MM for perfect sorting
                
                all_chunks.append(temp)
        except Exception as e:
            continue

    return pd.concat(all_chunks, ignore_index=True) if all_chunks else pd.DataFrame()

df = load_clean_data()

# --- 3. IMPROVED FILTRATION LOGIC ---
if not df.empty:
    with st.sidebar:
        st.header("🎯 Filter Logic")
        
        # Cascading Logic: Obj -> OKR -> Region
        sel_objs = st.multiselect("Objectives", sorted(df['Objective'].unique()), default=df['Objective'].unique()[:2])
        
        mask_okr = df[df['Objective'].isin(sel_objs)]
        sel_okrs = st.multiselect("OKRs", sorted(mask_okr['OKR'].unique()), default=mask_okr['OKR'].unique())
        
        mask_reg = mask_okr[mask_okr['OKR'].isin(sel_okrs)]
        sel_regs = st.multiselect("Regions", sorted(mask_reg['Region'].unique()), default=mask_reg['Region'].unique())

    # Final Filter
    filtered_df = mask_reg[mask_reg['Region'].isin(sel_regs)]

    # --- 4. RENDER WITH CHART FIX ---
    for obj in sel_objs:
        st.header(f"Objective: {obj}")
        obj_data = filtered_df[filtered_df['Objective'] == obj]
        
        for okr in sorted(obj_data['OKR'].unique()):
            with st.expander(f"OKR {okr}", expanded=True):
                okr_data = obj_data[obj_data['OKR'] == okr]
                
                metrics = okr_data['Metric'].unique()
                cols = st.columns(len(metrics) if len(metrics) < 3 else 2)
                
                for i, m_name in enumerate(metrics):
                    m_data = okr_data[okr_data['Metric'] == m_name]
                    
                    # FIX: Pivot the data to ensure Streamlit reads it correctly
                    # This aggregates multiple rows for the same month (summing them up)
                    chart_df = m_data.groupby('Month_Display')['Val'].sum().reset_index()
                    chart_df = chart_df.sort_values('Month_Display') # Ensure Jan -> Dec order
                    
                    with cols[i % len(cols)]:
                        st.subheader(m_name)
                        # Explicitly naming x and y prevents blank chart errors
                        st.area_chart(chart_df, x='Month_Display', y='Val', use_container_width=True)
                        st.metric("Total", f"{chart_df['Val'].sum():,.0f}")

else:
    st.warning("No data found. Check if your Google Sheet is 'Published to Web' as a CSV.")
