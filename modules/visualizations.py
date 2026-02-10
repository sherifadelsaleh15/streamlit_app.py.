import plotly.express as px
import streamlit as st

def render_metric_chart(df, metric_name, color="#3b82f6"):
    """Renders a clean, aggregated area chart for a specific metric"""
    # AGGREGATION: This is the secret sauce to fix broken charts
    # We sum values by date to ensure one clean line
    chart_data = df[df['Metric'] == metric_name].groupby(['dt', 'Month_Display'])['Val'].sum().reset_index()
    chart_data = chart_data.sort_values('dt')

    fig = px.area(
        chart_data, 
        x='Month_Display', 
        y='Val',
        title=f"Trend: {metric_name}",
        color_discrete_sequence=[color]
    )
    
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="",
        yaxis_title="Value",
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
