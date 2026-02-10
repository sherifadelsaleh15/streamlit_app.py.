import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_metric_chart(df, metric_name, forecast_df=None):
    """Renders trend lines with Raleway styling"""
    m_df = df[df['Metric Name'] == metric_name].copy() if 'Metric Name' in df.columns else df.copy()
    
    # Standardize date column for plotting
    date_col = 'Date_Month' if 'Date_Month' in df.columns else 'Month'
    val_col = 'Value' if 'Value' in df.columns else 'Views'
    
    chart_data = m_df.groupby(date_col)[val_col].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_data[date_col], y=chart_data[val_col],
        mode='lines+markers', name='Actual',
        line=dict(color='#1a1a1a', width=3),
        fill='tozeroy', fillcolor='rgba(26, 26, 26, 0.05)'
    ))

    fig.update_layout(
        template="plotly_white",
        font=dict(family="Raleway, sans-serif"),
        height=350,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

def render_top_pages_table(df):
    """Specific logic for GSC Keywords and GA4 Page Paths"""
    source = str(df['Source'].iloc[0]).upper() if 'Source' in df.columns else ""
    
    st.subheader("🔥 Top Performance Breakdown")
    
    # Determine which column to use as the 'Label'
    if 'Keyword' in df.columns:
        label_col = 'Keyword'
        val_col = 'Clicks'
    elif 'Page Path' in df.columns:
        label_col = 'Page Path'
        val_col = 'Views'
    else:
        label_col = 'Objective ID'
        val_col = 'Value' if 'Value' in df.columns else df.columns[-1]

    # Aggregate top 10
    top_data = df.groupby(label_col)[val_col].sum().sort_values(ascending=False).head(10).reset_index()
    
    fig = go.Figure(go.Bar(
        x=top_data[val_col],
        y=top_data[label_col],
        orientation='h',
        marker=dict(color='#1a1a1a')
    ))
    
    fig.update_layout(
        template="plotly_white",
        height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(autorange="reversed", font=dict(family="Raleway"))
    )
    st.plotly_chart(fig, use_container_width=True)
