import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_metric_chart(df, metric_name, forecast_df=None):
    """
    Renders a premium dark-mode line chart using Raleway font.
    """
    # Filter and prep data
    m_df = df[df['Metric'] == metric_name].copy()
    chart_data = m_df.groupby(['dt', 'Month_Display'])['Val'].sum().reset_index()
    chart_data = chart_data.sort_values('dt')
    
    if chart_data.empty:
        return st.info(f"No data available for {metric_name}")

    fig = go.Figure()

    # Actual Data Trace
    fig.add_trace(go.Scatter(
        x=chart_data['Month_Display'], 
        y=chart_data['Val'],
        mode='lines+markers',
        name='Actual',
        line=dict(color='#ffffff', width=3),
        fill='tozeroy',
        fillcolor='rgba(255, 255, 255, 0.05)',
        marker=dict(size=6, color='#ffffff')
    ))

    # Forecast Trace
    if forecast_df is not None and not forecast_df.empty:
        # Connect the last actual point to the first forecast point for continuity
        last_actual = chart_data.tail(1)
        combined_f = pd.concat([last_actual, forecast_df], ignore_index=True)
        
        fig.add_trace(go.Scatter(
            x=combined_f['Month_Display'], 
            y=combined_f['Val'],
            name='Forecast',
            line=dict(color='#737373', width=2, dash='dash'),
            mode='lines'
        ))

    # Layout styling for Dark Mode & Raleway
    fig.update_layout(
        title=dict(
            text=metric_name.upper(),
            font=dict(family="Raleway, sans-serif", size=16, color='#ffffff'),
            pad=dict(b=20)
        ),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Raleway, sans-serif", color="#a3a3a3"),
        hovermode="x unified",
        height=350,
        showlegend=False,
        margin=dict(l=10, r=10, t=60, b=20),
        xaxis=dict(
            showgrid=False,
            linecolor='#333333',
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#1f1f1f',
            linecolor='#333333',
            tickfont=dict(size=10)
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
