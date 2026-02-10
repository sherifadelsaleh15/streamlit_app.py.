import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from modules.ml_models import generate_forecast

def render_metric_chart(df, metric_display_name, val_col, key_suffix=""):
    if df.empty or val_col not in df.columns:
        return

    # 1. Historical Data
    chart_data = df.groupby('dt')[val_col].sum().reset_index().sort_values('dt')
    
    fig = go.Figure()
    
    # Actual Data Trace
    fig.add_trace(go.Scatter(
        x=chart_data['dt'], y=chart_data[val_col],
        mode='lines+markers', name='Actual',
        line=dict(color='#1a1a1a', width=3),
        fill='tozeroy', fillcolor='rgba(0,0,0,0.05)'
    ))

    # 2. Add Predictive Forecast Trace
    f_df = generate_forecast(df, val_col)
    if not f_df.empty:
        # Join the last actual point with the first forecast point for a smooth line
        last_actual = chart_data.iloc[-1:]
        f_plot = pd.concat([last_actual, f_df])
        
        fig.add_trace(go.Scatter(
            x=f_plot['dt'], y=f_plot[val_col],
            mode='lines', name='AI Forecast',
            line=dict(color='#64748b', width=2, dash='dot')
        ))

    fig.update_layout(
        title=dict(text=f"Trend & Forecast: {metric_display_name}", font=dict(family="Raleway", size=16)),
        template="plotly_white", height=320,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{val_col}_{key_suffix}")

def render_top_breakdown(df, tab_name):
    label_col = 'Page_Path' if 'Page_Path' in df.columns else ('Keyword' if 'Keyword' in df.columns else None)
    val_col = 'Views' if 'Views' in df.columns else ('Clicks' if 'Clicks' in df.columns else 'Value')

    if not label_col: return

    st.subheader(f"Top 10: {label_col.replace('_', ' ')}")
    top_data = df.groupby(label_col)[val_col].sum().sort_values(ascending=False).head(10).reset_index()
    
    fig = go.Figure(go.Bar(x=top_data[val_col], y=top_data[label_col], orientation='h', marker=dict(color='#1a1a1a')))
    fig.update_layout(template="plotly_white", height=400, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True, key=f"bar_{tab_name}")
