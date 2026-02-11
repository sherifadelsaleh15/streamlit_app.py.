import streamlit as st
import plotly.express as px
import google.generativeai as genai

def render_performance_tab(tab_df, sel_tab, api_key):
    # Detect Page and Views columns
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PLATFORM', 'SOURCE'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['VIEWS', 'SESSIONS', 'USERS', 'CLICKS'])), None)
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY'])), None)

    st.title(f"Performance Analysis: {sel_tab}")

    # Standard Leaderboard
    L, M, R = st.columns([1, 4, 1])
    with M:
        top_df = tab_df.groupby(page_col)[value_col].sum().nlargest(20).reset_index()
        fig = px.bar(top_df, x=value_col, y=page_col, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'])
        st.plotly_chart(fig, use_container_width=True)

    # Trends Loop
    loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany')
    for loc in loc_list:
        st.markdown(f"## Region: {loc}")
        loc_data = tab_df[tab_df[loc_col] == loc]
        top_pages = loc_data.groupby(page_col)[value_col].sum().nlargest(10).index.tolist()
        
        for pg in top_pages:
            pg_data = loc_data[loc_data[page_col] == pg]
            with st.expander(f"Entity: {pg} | Total: {pg_data[value_col].sum()}", expanded=(loc=='Germany')):
                fig = px.line(pg_data, x='dt', y=value_col, markers=True, title=f"Trend: {pg}")
                st.plotly_chart(fig, use_container_width=True)
