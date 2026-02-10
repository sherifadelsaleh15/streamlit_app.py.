import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd  # <--- This was likely missing!

def render_metric_chart(df, metric_name, forecast_df=None):
    """Renders an area chart with an optional forecast line"""
    
    # 1. Filter and aggregate the actual data
    chart_data = df[df['Metric'] == metric_name].groupby(['dt', 'Month_Display'])['Val'].sum().reset_index()
    chart_data = chart_data.sort_values('dt')
    
    if chart_data.empty:
        st.warning(f"No data available for {metric_name}")
        return

    fig = go.Figure()

    # 2. Add Actual Data (Solid Blue Area)
    fig.add_trace(go.Scatter(
        x=chart_data['Month_Display'], 
        y=chart_data['Val'],
        fill='tozeroy', 
        name='Actual',
        line=dict(color='#3b82f6', width=3)
    ))

    # 3. Add Forecast Data (Dashed Gray Line)
    if forecast_df is not None and not forecast_df.empty:
        # We take the last row of actual data so the forecast line connects to it
        last_actual = chart_data.tail(1)
        
        # Merge last actual point with forecast points
        combined_forecast = pd.concat([last_actual, forecast_df], ignore_index=True)
        
        fig.add_trace(go.Scatter(
            x=combined_forecast['Month_Display'], 
            y=combined_forecast['Val'],
            name='6-Month Forecast',
            line=dict(color='#94a3b8', width=3, dash='dash')
        ))

    # 4. Layout Styling
    fig.update_layout(
        title=dict(text=f"Trend & Forecast: {metric_name}", font=dict(size=18)),
        hovermode="x unified",
        template="plotly_white",
        height=380,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
