tab_df = df_dict.get(sel_tab, pd.DataFrame()).copy()

if not tab_df.empty:
    # --- FAILSAFE COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO'])), None)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'VALUE', 'POSITION'])), None)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['METRIC', 'QUERY', 'KEYWORD'])), None)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH'])), None)
    # --- IMPROVED COLUMN DETECTION ---
    loc_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['REGION', 'COUNTRY', 'GEO', 'LOCATION'])), None)
    # Target value (Clicks for GSC, Sessions/Users for GA4)
    value_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['CLICKS', 'SESSIONS', 'USERS', 'VALUE', 'POSITION', 'VIEWS'])), None)
    # Metric Name (Keyword for GSC)
    metric_name_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['QUERY', 'KEYWORD', 'TERM', 'METRIC'])), None)
    # Page Name (For GA4)
    page_col = next((c for c in tab_df.columns if any(x in c.upper() for x in ['PAGE', 'URL', 'PATH', 'LANDING'])), None)
date_col = 'dt'

if value_col:
@@ -44,7 +47,7 @@
sel_locs = st.sidebar.multiselect(f"Filter Region", all_locs, default=all_locs)
tab_df = tab_df[tab_df[loc_col].isin(sel_locs)]

    # --- SIDEBAR: CHAT WITH DATA ---
    # --- CHAT WITH DATA ---
st.sidebar.divider()
st.sidebar.subheader("Chat with Data")
user_q = st.sidebar.text_input("Ask a question about this data:", key="user_input")
@@ -58,33 +61,31 @@
st.sidebar.write(f"AI: {chat['a']}")
st.sidebar.divider()

    # --- SOURCE-SPECIFIC LEADERBOARDS ---
    # Top 20 Keywords only for GSC
    if "GSC" in sel_tab.upper() and metric_name_col and value_col:
    # --- DYNAMIC LEADERBOARDS ---
    # Top 20 Keywords logic (GSC)
    if "GSC" in sel_tab.upper() and metric_name_col:
st.subheader("Top 20 GSC Keywords")
agg_k = 'min' if is_ranking else 'sum'
top_k = tab_df.groupby(metric_name_col)[value_col].agg(agg_k).reset_index()
top_k = top_k.sort_values(by=value_col, ascending=(agg_k=='min')).head(20)
        fig_k = px.bar(top_k, x=value_col, y=metric_name_col, orientation='h', template="plotly_white")
        fig_k = px.bar(top_k, x=value_col, y=metric_name_col, orientation='h', template="plotly_white", color_discrete_sequence=['#4285F4'])
if is_ranking: fig_k.update_layout(xaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_k, use_container_width=True, key="leaderboard_gsc")
        st.plotly_chart(fig_k, use_container_width=True)

    # Top 20 Pages only for GA4 Top Pages
    if "PAGE" in sel_tab.upper() and page_col and value_col:
    # Top 20 Pages logic (GA4)
    if ("GA4" in sel_tab.upper() or "PAGE" in sel_tab.upper()) and page_col:
st.subheader("Top 20 GA4 Pages")
        agg_p = 'min' if is_ranking else 'sum'
        top_p = tab_df.groupby(page_col)[value_col].agg(agg_p).reset_index()
        top_p = top_p.sort_values(by=value_col, ascending=(agg_p=='min')).head(20)
        fig_p = px.bar(top_p, x=value_col, y=page_col, orientation='h', template="plotly_white")
        if is_ranking: fig_p.update_layout(xaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_p, use_container_width=True, key="leaderboard_ga4")
        top_p = tab_df.groupby(page_col)[value_col].sum().reset_index()
        top_p = top_p.sort_values(by=value_col, ascending=False).head(20)
        fig_p = px.bar(top_p, x=value_col, y=page_col, orientation='h', template="plotly_white", color_discrete_sequence=['#34A853'])
        st.plotly_chart(fig_p, use_container_width=True)

st.divider()

# --- GEMINI REPORT ---
st.subheader("Strategic AI Report")
if st.button("Generate Executive Analysis"):
        with st.spinner("Processing..."):
        with st.spinner("Analyzing..."):
sample_forecast = None
if value_col and len(tab_df) >= 2:
predict_df = tab_df.rename(columns={value_col: 'Value'})
@@ -93,53 +94,44 @@

if st.session_state.ai_report:
st.markdown(st.session_state.ai_report)
        st.download_button(label="Download AI Report (TXT)", data=st.session_state.ai_report, file_name=f"Report_{sel_tab}.txt")
        st.download_button("Download AI Report (TXT)", st.session_state.ai_report, f"Report_{sel_tab}.txt")

st.divider()

    # --- KEYWORD TRENDS (LOCATION + KEYWORD) ---
    # --- KEYWORD TRENDS ---
st.subheader("Monthly Performance Trends")
show_forecast = st.checkbox("Show Scikit-Learn Forecasts", value=True)

if metric_name_col and value_col and date_col in tab_df.columns:
agg_sort = 'min' if is_ranking else 'sum'
        # Get global top 20 list to keep focus sharp
top_20_list = tab_df.groupby(metric_name_col)[value_col].agg(agg_sort).sort_values(ascending=(agg_sort=='min')).head(20).index.tolist()
loc_list = sorted([str(x) for x in tab_df[loc_col].dropna().unique()], key=lambda x: x != 'Germany') if loc_col else [None]

c_idx = 0
for loc in loc_list:
loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            st.markdown(f"### Region: {loc if loc else 'Global'}")
            
            st.markdown(f"Region: {loc if loc else 'Global'}")
region_keywords = [kw for kw in top_20_list if kw in loc_data[metric_name_col].unique()]

for kw in region_keywords:
kw_data = loc_data[loc_data[metric_name_col] == kw].sort_values('dt')
c_idx += 1
                
                with st.expander(f"Trend for: {kw} in {loc}", expanded=(loc == 'Germany')):
                with st.expander(f"Data for: {kw} in {loc}", expanded=(loc == 'Germany')):
col1, col2 = st.columns([3, 1])
with col1:
                        fig = px.line(kw_data, x='dt', y=value_col, markers=True, height=350, 
                                      title=f"Monthly Trend: {kw} ({loc})")
                        
                        fig = px.line(kw_data, x='dt', y=value_col, markers=True, height=350, title=f"Trend: {kw} ({loc})")
if show_forecast and len(kw_data) >= 2:
f_in = kw_data.rename(columns={value_col: 'Value'})
forecast = get_prediction(f_in)
if forecast is not None:
fig.add_trace(go.Scatter(x=pd.concat([forecast['ds'], forecast['ds'][::-1]]), y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]), fill='toself', fillcolor='rgba(255,165,0,0.1)', line=dict(color='rgba(255,255,255,0)'), showlegend=False))
fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Projection', line=dict(color='orange', dash='dash')))

                        if is_ranking:
                            fig.update_layout(yaxis=dict(autorange="reversed", title="Rank"))
                        if is_ranking: fig.update_layout(yaxis=dict(autorange="reversed", title="Rank"))
st.plotly_chart(fig, use_container_width=True, key=f"ch_{loc}_{c_idx}")
                    
with col2:
st.write("Monthly Data")
table_data = kw_data[['dt', value_col]].copy()
table_data['dt'] = table_data['dt'].dt.strftime('%b %Y')
st.dataframe(table_data, hide_index=True, key=f"tbl_{loc}_{c_idx}")
                        
csv = table_data.to_csv(index=False).encode('utf-8')
                        st.download_button(label="Download CSV", data=csv, file_name=f"{kw}_{loc}.csv", key=f"dl_{loc}_{c_idx}")
                        st.download_button("Download CSV", csv, f"{kw}_{loc}.csv", key=f"dl_{loc}_{c_idx}")
