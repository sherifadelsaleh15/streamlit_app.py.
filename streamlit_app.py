import streamlit as st
import pandas as pd
import urllib.parse

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="2026 Strategy Dashboard", layout="wide")

st.markdown("""
    <style>
    .metric-container {
        background: white; border: 1px solid #e2e8f0; padding: 15px;
        border-radius: 10px; margin-bottom: 20px;
    }
    .metric-meta { font-size: 0.75rem; color: #64748b; margin-bottom: 5px; }
    .metric-title { font-size: 1rem; font-weight: 700; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. UNIVERSAL DATA LOADER ---
SHEET_ID = "1QFIhc5g1FeMj-wQSL7kucsAyhgurxH9mqP3cmC1mcFY"

@st.cache_data(ttl=60)
def load_all_data():
    tabs = ["MASTER_FEED", "GA4_Data", "GA4_Top_Pages", "GSC", "SOCIAL_MEDIA"]
    all_chunks = []
    
    # Universal mapping based on your shared layout
    mapping = {
        "Objective ID": "Objective", "Objective_ID": "Objective",
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

            # Check for numeric values in order of priority
            val_col = next((c for c in ['Value', 'Views', 'Clicks', 'KeywordClicks', 'Active Users'] if c in df.columns), None)
            
            if val_col:
                temp = pd.DataFrame()
                temp['Objective'] = df['Objective'].astype(str).replace('nan', 'Unassigned')
                temp['Region'] = df['Region'].astype(str).replace('nan', 'Global')
                temp['OKR'] = df['OKR'].astype(str).replace('nan', 'N/A')
                temp['Metric'] = df['Metric'].astype(str).fillna(tab)
                temp['Val'] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
                temp['Source'] = tab
                
                # Standardize time for proper chart sorting
                temp['dt'] = pd.to_datetime(df['Date_Raw'], errors='coerce')
                temp = temp.dropna(subset=['dt'])
                temp['Month_Display'] = temp['dt'].dt.strftime('%b %Y')
                
                all_chunks.append(temp)
        except: continue

    return pd.concat(all_chunks, ignore_index=True) if all_chunks else pd.DataFrame()

df_master = load_all_data()

# --- 3. MAIN INTERFACE ---
if not df_master.empty:
    st.title("🎯 2026 Strategy Performance Hub")
    
    # Create the Tabs at the top
    tab_names = sorted(df_master['Source'].unique().tolist())
    st_tabs = st.tabs(tab_names)

    for i, tab_label in enumerate(tab_names):
        with st_tabs[i]:
            # Filter data for THIS tab only
            tab_df = df_master[df_master['Source'] == tab_label]
            
            # --- TAB-SPECIFIC FILTRATION ---
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                sel_objs = st.multiselect(f"Filter Objectives ({tab_label})", 
                                        sorted(tab_df['Objective'].unique()), 
                                        key=f"obj_{tab_label}")
            
            # Filter OKRs based on selected Objectives
            okr_opts = tab_df[tab_df['Objective'].isin(sel_objs)]['OKR'].unique() if sel_objs else tab_df['OKR'].unique()
            with col_f2:
                sel_okrs = st.multiselect(f"Filter OKRs ({tab_label})", 
                                        sorted(okr_opts), 
                                        key=f"okr_{tab_label}")
            
            # Filter Metrics based on OKRs
            metric_opts = tab_df[tab_df['OKR'].isin(sel_okrs)]['Metric'].unique() if sel_okrs else tab_df['Metric'].unique()
            with col_f3:
                sel_metrics = st.multiselect(f"Filter Metrics ({tab_label})", 
                                           sorted(metric_opts), 
                                           key=f"met_{tab_label}")

            # Apply final filtration for display
            final_df = tab_df.copy()
            if sel_objs: final_df = final_df[final_df['Objective'].isin(sel_objs)]
            if sel_okrs: final_df = final_df[final_df['OKR'].isin(sel_okrs)]
            if sel_metrics: final_df = final_df[final_df['Metric'].isin(sel_metrics)]

            if final_df.empty:
                st.info("Select filters above to view charts.")
                continue

            # --- RENDER CHARTS ---
            # Grouping the UI to show the data you requested per chart
            for metric in final_df['Metric'].unique():
                m_slice = final_df[final_df['Metric'] == metric]
                
                # Pivot logic for the chart to handle multiple regions/sources
                chart_data = m_slice.groupby('dt')['Val'].sum().reset_index().sort_values('dt')
                chart_data['Month_Display'] = chart_data['dt'].dt.strftime('%b %Y')

                with st.container():
                    st.markdown(f"""
                        <div class="metric-container">
                            <div class="metric-meta">
                                <b>Objective:</b> {m_slice['Objective'].iloc[0]} | 
                                <b>OKR:</b> {m_slice['OKR'].iloc[0]} | 
                                <b>Region:</b> {', '.join(m_slice['Region'].unique())}
                            </div>
                            <div class="metric-title">{metric} ({tab_label})</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        # Re-plotting the chart with standardized X and Y
                        st.area_chart(chart_data, x='Month_Display', y='Val', use_container_width=True)
                    with c2:
                        st.metric("Total", f"{chart_data['Val'].sum():,.0f}")
                        st.dataframe(m_slice[['Month_Display', 'Region', 'Val']], hide_index=True, use_container_width=True)
else:
    st.error("Data synchronization failed. Ensure your Google Sheet is published to web as CSV.")
