import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_metric_chart(df, metric_name, forecast_df=None):
    # (Keep your existing line chart code here for the trends)
    pass

def render_top_pages_table(df):
    """
    Specifically for GSC/GA4: Shows top URLs by Value with a small bar visualization.
    """
    st.write("### Top Performing Pages")
    # Group by Objective (which often holds the URL/Page name in GSC exports)
    top_pages = df.groupby('Objective')['Val'].sum().sort_values(ascending=False).head(10).reset_index()
    
    # Create a simple horizontal bar chart for the top pages
    fig = go.Figure(go.Bar(
        x=top_pages['Val'],
        y=top_pages['Objective'],
        orientation='h',
        marker=dict(color='#1a1a1a')
    ))
    fig.update_layout(
        template="plotly_white",
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(autorange="reversed") # Highest at the top
    )
    st.plotly_chart(fig, use_container_width=True)
