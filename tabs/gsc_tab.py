import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from modules.ml_models import get_prediction

def render_gsc_content(df, tab_name):
    st.title(f"GSC Analysis: {tab_name}")
    
    # Column Detection
    loc_col = next((c for c in df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    kw_col = next((c for c in df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    click_col = next((c for c in df.columns if 'CLICKS' in c.upper()), None)
    pos_col = next((c for c in df.columns if 'POSITION' in c.upper()), None)
    date_col = 'dt'

    # Filter Regions
    if loc_col:
        all_locs = sorted(df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        df = df[df[loc_col].isin(sel_locs)]

    # Loop Regions
    loc_list = sorted([str(x) for x in df[loc_col].unique()], key=lambda x: x != 'Germany')
    for loc in loc_list:
        st.markdown(f"## Region: {loc}")
        loc_data = df[df[loc_col] == loc]
        
        # Get Top Keywords for this region
        top_kws = loc_data.groupby(kw_col)[click_col].sum().sort_values(ascending=False).head(10).index.tolist()

        for kw in top_kws:
            kw_data = loc_data[loc_data[kw_col] == kw].sort_values(date_col)
            label = f"Keyword: {kw} | Clicks: {kw_data[click_col].sum()} | Avg Pos: {round(kw_data[pos_col].mean(), 1)}"
            
            with st.expander(label, expanded=(loc == 'Germany')):
                c1, c2 = st.columns([3, 1])
                with c1:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=kw_data[date_col], y=kw_data[click_col], name="Clicks", line=dict(color='#4285F4', width=3)))
                    fig.add_trace(go.Scatter(x=kw_data[date_col], y=kw_data[pos_col], name="Avg Position", yaxis="y2", line=dict(color='#DB4437', dash='dot')))
                    fig.update_layout(
                        template="plotly_white",
                        yaxis=dict(title="Clicks"),
                        yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"),
                        legend=dict(orientation="h", y=1.1)
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"gsc_{loc}_{kw}")
                with c2:
                    st.write("Monthly Detail")
                    st.dataframe(kw_data[[date_col, click_col, pos_col]], hide_index=True)
