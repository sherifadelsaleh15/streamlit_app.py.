import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import google.generativeai as genai
import pandas as pd
from modules.ml_models import get_prediction

def get_ai_insight(df, tab_name, api_key):
    try:
        data_summary = df.head(15).to_string()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"Senior Strategic Analyst. Analyze GSC data for {tab_name}:\n{data_summary}")
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

def render_gsc_tab(tab_df, sel_tab, api_key):
    # --- FAILSAFE COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    click_col = next((c for c in tab_df.columns if 'CLICKS' in c.upper()), None)
    pos_col = next((c for c in tab_df.columns if 'POSITION' in c.upper() or 'RANK' in c.upper()), None)
    item_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM'])), None)
    date_col = 'dt'

    if not all([click_col, pos_col, item_col]):
        st.error(f"Missing SEO columns in {sel_tab}. Available: {list(tab_df.columns)}")
        return

    # --- SIDEBAR FILTERS ---
    if loc_col:
        all_locs = sorted(tab_df[loc_col].dropna().unique().tolist())
        sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
        tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    st.title(f"Strategic SEO View: {sel_tab}")

    # --- CENTERED LEADERBOARDS ---
    L, M, R = st.columns([1, 4, 1])
    with M:
        st.subheader(f"Top 20 Keywords by Clicks")
        top_df = tab_df.groupby(item_col)[click_col].sum().nlargest(20).reset_index()
        fig_main = px.bar(top_df, x=click_col, y=item_col, orientation='h', 
                          template="plotly_white", color_discrete_sequence=['#4285F4'])
        st.plotly_chart(fig_main, use_container_width=True)

    st.divider()

    # --- STRATEGIC AI REPORT ---
    st.subheader("Strategic AI Report")
    if st.button("Generate Executive Analysis"):
        with st.spinner("Analyzing..."):
            st.session_state.ai_report = get_ai_insight(tab_df, sel_tab, api_key)
    if "ai_report" in st.session_state and st.session_state.ai_report:
        st.markdown(st.session_state.ai_report)

    st.divider()

    # --- MONTHLY PERFORMANCE TRENDS ---
    st.subheader("Monthly Performance Trends")
    show_forecast = st.checkbox("Show AI Projections", value=True)
    
    loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]

    for loc in loc_list:
        loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
        st.markdown(f"## Region: {loc if loc else 'Global'}")
        
        top_region_items = loc_data.groupby(item_col)[click_col].sum().nlargest(10).index.tolist()

        for item in top_region_items:
            item_data = loc_data[loc_data[item_col] == item].sort_values('dt')
            
            # Dynamic Label combining Clicks and Position
            avg_pos = round(item_data[pos_col].mean(), 1)
            total_clicks = item_data[click_col].sum()
            
            with st.expander(f"Keyword: {item} | Clicks: {total_clicks} | Avg Pos: {avg_pos}", expanded=(loc == 'Germany')):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # GSC DUAL AXIS CHART
                    fig = go.Figure()
                    # Trace 1: Clicks (Bar or Line)
                    fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[click_col], 
                                             name="Clicks", line=dict(color='#4285F4', width=3)))
                    # Trace 2: Position (Dotted Line on Y2)
                    fig.add_trace(go.Scatter(x=item_data['dt'], y=item_data[pos_col], 
                                             name="Position", yaxis="y2", line=dict(color='#DB4437', dash='dot')))
                    
                    # AI Projection Logic
                    if show_forecast and len(item_data) >= 3:
                        f_in = item_data.rename(columns={click_col: 'Value', 'dt': 'ds'})
                        forecast = get_prediction(f_in)
                        if forecast is not None:
                            fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], 
                                                     mode='lines', name='Projection', line=dict(color='orange', dash='dash')))

                    fig.update_layout(
                        title=f"Trend: {item}",
                        template="plotly_white",
                        yaxis=dict(title="Clicks"),
                        yaxis2=dict(title="Position", overlaying="y", side="right", autorange="reversed"),
                        legend=dict(orientation="h", y=1.1)
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"gsc_{loc}_{item}")
                
                with col2:
                    st.write("Monthly Stats")
                    table_view = item_data[['dt', click_col, pos_col]].copy()
                    table_view['dt'] = table_view['dt'].dt.strftime('%b %Y')
                    st.dataframe(table_view, hide_index=True)
