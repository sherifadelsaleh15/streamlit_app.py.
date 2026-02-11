import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import google.generativeai as genai
from modules.ml_models import get_prediction

def render_gsc_tab(tab_df, sel_tab, api_key):
    # 1. Detection
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    item_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    date_col = 'dt'

    # 2. Sidebar Filter (Applied within the tab)
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    st.title(f"Strategic SEO View: {sel_tab}")

    # 3. Leaderboard
    L, M, R = st.columns([1, 4, 1])
    with M:
        top_df = tab_df.groupby(item_col)[click_col].sum().nlargest(20).reset_index()
        fig = px.bar(top_df, x=click_col, y=item_col, orientation='h', template="plotly_white", color_discrete_sequence=['#4285F4'])
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 4. Monthly Trends Loop
    loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]
    for loc in loc_list:
        st.markdown(f"## Region: {loc}")
        loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
        top_kws = loc_data.groupby(item_col)[click_col].sum().nlargest(10).index.tolist()
        
        for kw in top_kws:
            kw_data = loc_data[loc_data[item_col] == kw].sort_values(date_col)
            avg_pos = round(kw_data[pos_col].mean(), 1)
            
            with st.expander(f"Keyword: {kw} | Clicks: {kw_data[click_col].sum()} | Avg Pos: {avg_pos}", expanded=(loc == 'Germany')):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # DUAL AXIS CHART
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=kw_data[date_col], y=kw_data[click_col], name="Clicks", line=dict(color='#4285F4', width=3)))
                    fig.add_trace(go.Scatter(x=kw_data[date_col], y=kw_data[pos_col], name="Avg Position", yaxis="y2", line=dict(color='#DB4437', dash='dot')))
                    
                    fig.update_layout(
                        template="plotly_white",
                        yaxis=dict(title="Clicks"),
                        yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"),
                        legend=dict(orientation="h", y=1.1)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.write("Monthly Detail")
                    st.dataframe(kw_data[[date_col, click_col, pos_col]], hide_index=True)
