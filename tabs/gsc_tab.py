import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import google.generativeai as genai
from modules.ml_models import get_prediction

GEMINI_KEY = "AIzaSyAEssaFWdLqI3ie8y3eiZBuw8NVdxRzYB0"

def render_gsc(tab_df, sel_tab):
    # Same settings logic
    is_gsc = True
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    item_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    date_col = 'dt'

    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    st.title(f"Strategic View: {sel_tab}")
    
    # Leaderboard, AI Report, and the Loop Logic you provided goes here
    # (Using your provided loop logic exactly)
    loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany')
    for loc in loc_list:
        loc_data = tab_df[tab_df[loc_col] == loc]
        st.markdown(f"## Region: {loc}")
        top_items = loc_data.groupby(item_col)[click_col].sum().sort_values(ascending=False).head(10).index.tolist()
        
        for item in top_items:
            item_data = loc_data[loc_data[item_col] == item].sort_values('dt')
            label = f"Keyword: {item} | Clicks: {item_data[click_col].sum()} | Avg Pos: {round(item_data[pos_col].mean(), 1)}"
            with st.expander(label, expanded=(loc == 'Germany')):
                col1, col2 = st.columns([3, 1])
                with col1:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[click_col], name="Clicks", line=dict(color='#4285F4', width=3)))
                    fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[pos_col], name="Avg Position", yaxis="y2", line=dict(color='#DB4437', dash='dot')))
                    fig.update_layout(yaxis2=dict(overlaying="y", side="right", autorange="reversed"), template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True, key=f"gsc_{loc}_{item}")
                with col2:
                    st.dataframe(item_data[['dt', click_col, pos_col]], hide_index=True)
