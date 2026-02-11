import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import google.generativeai as genai
from modules.ml_models import get_prediction

def render_gsc_tab(tab_df, sel_tab, api_key):
    # Failsafe Detection (Prevents KeyError)
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    item_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD'])), None)

    if not all([click_col, pos_col, item_col]):
        st.error(f"Missing SEO columns in {sel_tab}. Available: {list(tab_df.columns)}")
        return

    st.title(f"Strategic SEO View: {sel_tab}")

    # GSC Dual-Axis Chart Logic
    loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]
    for loc in loc_list:
        st.markdown(f"## Region: {loc}")
        loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
        top_kws = loc_data.groupby(item_col)[click_col].sum().nlargest(10).index.tolist()
        
        for kw in top_kws:
            kw_data = loc_data[loc_data[item_col] == kw].sort_values('dt')
            with st.expander(f"Keyword: {kw} | Avg Pos: {round(kw_data[pos_col].mean(), 1)}", expanded=(loc == 'Germany')):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=kw_data['dt'], y=kw_data[click_col], name="Clicks", line=dict(color='#4285F4')))
                fig.add_trace(go.Scatter(x=kw_data['dt'], y=kw_data[pos_col], name="Position", yaxis="y2", line=dict(color='#DB4437', dash='dot')))
                fig.update_layout(yaxis2=dict(overlaying="y", side="right", autorange="reversed"), template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
