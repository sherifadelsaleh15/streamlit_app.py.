import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_metric_chart(df, metric_name):
    # Find the value column automatically
    val_col = 'Value' if 'Value' in df.columns else metric_name
    date_col = 'dt' if 'dt' in df.columns else df.columns[0]

    chart_data = df.groupby(date_col)[val_col].sum().reset_index()
    
    fig = go.Figure(go.Scatter(
        x=chart_data[date_col], y=chart_data[val_col],
        line=dict(color='#1a1a1a', width=3),
        fill='tozeroy', fillcolor='rgba(0,0,0,0.05)'
    ))
    fig.update_layout(template="plotly_white", height=300, font=dict(family="Raleway"))
    st.plotly_chart(fig, use_container_width=True)

def render_top_pages_table(df):
    """Specific logic for GSC and GA4 Top Pages"""
    # Detect if we should use Page Path (GA4) or Keyword (GSC)
    if 'Page Path' in df.columns:
        label_col, val_col = 'Page Path', 'Views'
    elif 'Keyword' in df.columns:
        label_col, val_col = 'Keyword', 'Clicks'
    else:
        return st.info("No Page or Keyword data found in this tab.")

    top_data = df.groupby(label_col)[val_col].sum().sort_values(ascending=False).head(10).reset_index()
    
    fig = go.Figure(go.Bar(
        x=top_data[val_col], y=top_data[label_col],
        orientation='h', marker=dict(color='#1a1a1a')
    ))
    fig.update_layout(template="plotly_white", height=400, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)
