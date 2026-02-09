import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="2026 Strategy Command", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f8fafc; }
    .okr-box {
        background: white; border: 1px solid #e2e8f0; padding: 20px;
        border-radius: 12px; margin-bottom: 20px;
    }
    .metric-header { display: flex; justify-content: space-between; align-items: center; }
    .metric-name { font-size: 1.1rem; font-weight: 700; color: #1e293b; }
    .okr-tag { background: #eff6ff; color: #3b82f6; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_and_clean():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_chunks = []
    
    mapping = {
        "Objective_ID": "Objective", "Objective ID": "Objective",
        "Region/Country": "Region", "Region": "Region",
        "Date_Month": "Month_Raw", "Month": "Month_Raw",
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

            # Identify value column
            val_col = next((c for c in ['Value', 'Views', 'Clicks', 'KeywordClicks'] if c in df.columns), None)
            
            if val_col:
                temp = pd.DataFrame()
                temp['Objective'] = df['Objective'].astype(str).fillna("Unassigned")
                temp['Region'] = df['Region'].astype(str).fillna("Global")
                temp['OKR'] = df['OKR'].astype(str).fillna("N/A")
                temp['Metric'] = df['Metric'].astype(str).fillna(tab)
                temp['Val'] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
                temp['Source'] = tab
                
                # Standardize Dates for chronological sorting
                raw_dates = df['Month_Raw'].astype(str)
                temp['dt'] = pd.to_datetime(raw_dates, errors='coerce', dayfirst=True)
                # Fallback for "January 2026" style strings if dayfirst fails
                temp.loc[temp['dt'].isna(), 'dt'] = pd.to_datetime(raw_dates, errors='coerce')
                
                temp['Month_Display'] = temp['dt'].dt.strftime('%b %Y')
                all_chunks.append(temp.reset_index(drop=True))
        except: continue

    return pd.concat(all_chunks, ignore_index=True) if all_chunks else pd.DataFrame()

# --- 3. ADVANCED FILTRATION LOGIC ---
df = load_and_clean()

if not df.empty:
    st.title("2026 Objective Tracking")

    with st.sidebar:
        st.header("Global Controls")
        
        # 1. Objective Filter (Primary)
        obj_list = sorted(df['Objective'].unique())
        sel_objs = st.multiselect("🎯 Select Objectives", obj_list, default=obj_list)
        
        # Filter data based on Objective first to cascade other filters
        step1_df = df[df['Objective'].isin(sel_objs)]
        
        # 2. Dynamic OKR Filter (Secondary)
        okr_list = sorted(step1_df['OKR'].unique())
        sel_okrs = st.multiselect("🔑 Select OKRs", okr_list, default=okr_list)
        
        # 3. Dynamic Region Filter (Tertiary)
        step2_df = step1_df[step1_df['OKR'].isin(sel_okrs)]
        reg_list = sorted(step2_df['Region'].unique())
        sel_regs = st.multiselect("🌍 Select Regions", reg_list, default=reg_list)
        
        # 4. Chronological Month Filter
        month_list = step2_df.sort_values('dt')['Month_Display'].unique().tolist()
        sel_months = st.multiselect("📅 Select Months", month_list, default=month_list)

    # FINAL FILTERED DATASET
    main_df = step2_df[
        (step2_df['Region'].isin(sel_regs)) & 
        (step2_df['Month_Display'].isin(sel_months))
    ]

    # --- 4. RENDER HIERARCHY ---
    for obj in sel_objs:
        obj_slice = main_df[main_df['Objective'] == obj]
        if obj_slice.empty: continue
        
        st.markdown(f"## {obj}")
        
        # Group by OKR within the Objective
        for okr in sorted(obj_slice['OKR'].unique()):
            okr_slice = obj_slice[obj_slice['OKR'] == okr]
            
            with st.expander(f"OKR {okr} Details", expanded=True):
                # Create grid for metrics under this OKR
                metrics = okr_slice['Metric'].unique()
                cols = st.columns(len(metrics) if len(metrics) <= 3 else 2)
                
                for idx, m_name in enumerate(metrics):
                    m_data = okr_slice[okr_slice['Metric'] == m_name].sort_values('dt')
                    
                    with cols[idx % len(cols)]:
                        st.markdown(f"""
                            <div class="okr-box">
                                <div class="metric-header">
                                    <span class="metric-name">{m_name}</span>
                                    <span class="okr-tag">{m_data['Source'].iloc[0]}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.area_chart(m_data, x='Month_Display', y='Val', color="#2563eb")
                        
                        # Summary Stats
                        c1, c2 = st.columns(2)
                        c1.metric("Sum", f"{m_data['Val'].sum():,.0f}")
                        c2.metric("Avg", f"{m_data['Val'].mean():,.1f}")

else:
    st.error("Data processing failed. Check sheet publishing settings.")
