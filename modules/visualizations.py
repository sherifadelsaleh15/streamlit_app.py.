import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_metric_chart(df, metric_name):
    # Flexible column selection
    val_col = next((c for c in ['Value', 'Views', 'Clicks', metric_name] if c in df.columns), df.select_dtypes('number').columns[0])
    date_col = 'dt' if 'dt' in df.columns else (df.select_dtypes('datetime').columns[0] if not df.select_dtypes('datetime').empty else df.columns[0])

    chart_data = df.groupby(date_col)[val_col].sum().reset_index().sort_values(date_col)
    
    fig = go.Figure(go.Scatter(
        x=chart_data[date_col], y=chart_data[val_col],
        line=dict(color='#1a1a1a', width=3),
        fill='tozeroy', fillcolor='rgba(0,0,0,0.05)'
    ))
    fig.update_layout(template="plotly_white", height=300, font=dict(family="Raleway"), margin=dict(l=10,r=10,t=10,b=10))
    
    # The key=metric_name prevents the Duplicate ID error
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{metric_name}")

def render_top_pages_table(df, tab_name):
    """Detects Page Path or Keyword and shows top 10"""
    label_col = 'Page Path' if 'Page Path' in df.columns else ('Keyword' if 'Keyword' in df.columns else None)
    val_col = 'Views' if 'Views' in df.columns else ('Clicks' if 'Clicks' in df.columns else 'Value')

    if not label_col:
        return
    
    st.subheader(f"Top Performance: {label_col}")
    top_data = df.groupby(label_col)[val_col].sum().sort_values(ascending=False).head(10).reset_index()
    
    fig = go.Figure(go.Bar(
        x=top_data[val_col], y=top_data[label_col],
        orientation='h', marker=dict(color='#1a1a1a')
    ))
    fig.update_layout(template="plotly_white", height=400, yaxis=dict(autorange="reversed"), margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True, key=f"top_bar_{tab_name}")
