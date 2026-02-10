
st.divider()

    # --- CHART SECTION ---
    # --- CHART SECTION (FIXED FOR GSC/GA4) ---
st.subheader("Charts")
    st.write("Use the camera icon on the top right of each chart to download as image.")

    # Check for Long Format (OKR style) vs Wide Format (Analytics style)
metric_name_col = next((c for c in tab_df.columns if 'METRIC' in c.upper()), None)
    
    # Determine the Y-axis column. If 'Value' exists, use it. 
    # Otherwise, we use the numeric columns (Clicks, Impressions, etc.)
    has_value_col = 'Value' in tab_df.columns

    if metric_name_col:
    if metric_name_col and has_value_col:
        # CASE: OKR/Social sheets (Metric Name + Value columns)
unique_metrics = sorted(tab_df[metric_name_col].unique())
        if loc_col:
            for loc in sorted(tab_df[loc_col].unique()):
                st.write(f"Location: {loc}")
                loc_data = tab_df[tab_df[loc_col] == loc]
                cols = st.columns(2)
                for i, met in enumerate(unique_metrics):
                    chart_df = loc_data[loc_data[metric_name_col] == met]
                    if not chart_df.empty:
                        with cols[i % 2]:
                            fig = px.line(chart_df, x='dt', y='Value', title=f"{met} - {loc}")
                            st.plotly_chart(fig, use_container_width=True)
        for loc in (sorted(tab_df[loc_col].unique()) if loc_col else [None]):
            if loc: st.write(f"Location: {loc}")
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            cols = st.columns(2)
            for i, met in enumerate(unique_metrics):
                chart_df = loc_data[loc_data[metric_name_col] == met]
                if not chart_df.empty:
                    with cols[i % 2]:
                        fig = px.line(chart_df, x='dt', y='Value', title=f"{met} - {loc if loc else ''}", markers=True)
                        st.plotly_chart(fig, use_container_width=True)
else:
        # Handle GSC/GA4 format
        num_cols = [c for c in tab_df.select_dtypes('number').columns if not any(x in c.upper() for x in ['ID', 'YEAR'])]
        if loc_col:
            for loc in sorted(tab_df[loc_col].unique()):
                st.write(f"Location: {loc}")
                loc_data = tab_df[tab_df[loc_col] == loc]
                cols = st.columns(2)
                for i, col in enumerate(num_cols):
        # CASE: GSC/GA4 sheets (Metrics are actual column names)
        # Find numeric columns that are likely metrics
        num_cols = [c for c in tab_df.select_dtypes('number').columns 
                    if not any(x in c.upper() for x in ['ID', 'YEAR', 'MONTH', 'POSITION'])]
        
        for loc in (sorted(tab_df[loc_col].unique()) if loc_col else [None]):
            if loc: st.write(f"Location: {loc}")
            loc_data = tab_df[tab_df[loc_col] == loc] if loc else tab_df
            cols = st.columns(2)
            for i, col_name in enumerate(num_cols):
                if not loc_data[col_name].dropna().empty:
with cols[i % 2]:
                        fig = px.line(loc_data, x='dt', y=col, title=f"{col} - {loc}")
                        # FIXED: We use 'col_name' for the Y-axis instead of 'Value'
                        fig = px.line(loc_data, x='dt', y=col_name, title=f"{col_name} - {loc if loc else ''}", markers=True)
st.plotly_chart(fig, use_container_width=True)

# --- SIDEBAR CHAT ---
