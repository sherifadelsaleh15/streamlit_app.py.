import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_metric_chart(df, metric_name):
    # Find value column (Value or Views or Clicks)
    val_col = 'Value' if 'Value' in df.columns else (
              'Views' if 'Views' in df.columns else (
              'Clicks' if 'Clicks' in df.columns else df.select_dtypes('number').columns[0]))
    
    date_col = 'dt' if 'dt' in df.columns else df.columns[0]
    chart_data = df.groupby(date_col)[val_col].sum().reset_index().sort_values(date_col)
    
    fig = go.Figure(go.Scatter(
        x=chart_data[date_col], y=chart_data[val_col],
        line=dict(color='#1a1a1a', width=3),
        fill='tozeroy', fillcolor='rgba(0,0,0,0.05)'
    ))
    fig.update_layout(template="plotly_white", height=300, font=dict(family="Raleway"))
    st.plotly_chart(fig, use_container_width=True)

def render_top_pages_table(df):
    """Detects Page Path or Keyword and shows top 10"""
    label_col = 'Page_Path' if 'Page_Path' in df.columns else (
                'Keyword' if 'Keyword' in df.columns else None)
    
    val_col = 'Views' if 'Views' in df.columns else (
              'Clicks' if 'Clicks' in df.columns else 'Value')

    if not label_col:
        st.info("Detailed breakdown not available for this tab.")
        return

    top_data = df.groupby(label_col)[val_col].sum().sort_values(ascending=False).head(10).reset_index()
    
    fig = go.Figure(go.Bar(
        x=top_data[val_col], y=top_data[label_col],
        orientation='h', marker=dict(color='#1a1a1a')
    ))
    fig.update_layout(template="plotly_white", height=400, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)
