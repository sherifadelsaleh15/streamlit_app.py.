import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_metric_chart(df, metric_display_name, val_col, key_suffix=""):
    """Renders a trend line with a clear title and unique key."""
    if df.empty or val_col not in df.columns:
        return

    # Aggregate data by date
    chart_data = df.groupby('dt')[val_col].sum().reset_index().sort_values('dt')
    
    fig = go.Figure(go.Scatter(
        x=chart_data['dt'], y=chart_data[val_col],
        mode='lines+markers',
        line=dict(color='#1a1a1a', width=3),
        fill='tozeroy', fillcolor='rgba(0,0,0,0.05)',
        name=metric_display_name
    ))

    fig.update_layout(
        title=dict(text=f"Trend: {metric_display_name}", font=dict(family="Raleway", size=16)),
        template="plotly_white",
        height=300,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{val_col}_{key_suffix}")

def render_top_breakdown(df, tab_name):
    """Specifically for GSC (Keywords) and GA4 (Page Paths)."""
    label_col = 'Page_Path' if 'Page_Path' in df.columns else ('Keyword' if 'Keyword' in df.columns else None)
    val_col = 'Views' if 'Views' in df.columns else ('Clicks' if 'Clicks' in df.columns else 'Value')

    if not label_col or label_col not in df.columns:
        return

    st.subheader(f"Top 10: {label_col.replace('_', ' ')}")
    top_data = df.groupby(label_col)[val_col].sum().sort_values(ascending=False).head(10).reset_index()
    
    fig = go.Figure(go.Bar(
        x=top_data[val_col], y=top_data[label_col],
        orientation='h', marker=dict(color='#1a1a1a')
    ))
    fig.update_layout(template="plotly_white", height=400, yaxis=dict(autorange="reversed"), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True, key=f"bar_{tab_name}")
