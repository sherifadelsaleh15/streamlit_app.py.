import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_metric_chart(df, metric_name, forecast_df=None):
    m_df = df[df['Metric'] == metric_name].copy()
    chart_data = m_df.groupby(['dt', 'Month_Display'])['Val'].sum().reset_index()
    chart_data = chart_data.sort_values('dt')
    
    if chart_data.empty:
        return st.info(f"No data for {metric_name}")

    fig = go.Figure()

    # Actual Data (Black line)
    fig.add_trace(go.Scatter(
        x=chart_data['Month_Display'], y=chart_data['Val'],
        mode='lines+markers', name='Actual',
        line=dict(color='#1a1a1a', width=3),
        fill='tozeroy',
        fillcolor='rgba(26, 26, 26, 0.05)',
        marker=dict(size=6, color='#1a1a1a')
    ))

    # Forecast Data (Dashed Blue or Grey)
    if forecast_df is not None and not forecast_df.empty:
        last_actual = chart_data.tail(1)
        combined_f = pd.concat([last_actual, forecast_df], ignore_index=True)
        fig.add_trace(go.Scatter(
            x=combined_f['Month_Display'], y=combined_f['Val'],
            name='Forecast',
            line=dict(color='#94a3b8', width=2, dash='dash')
        ))

    fig.update_layout(
        title=dict(
            text=metric_name.upper(),
            font=dict(family="Raleway, sans-serif", size=16, color='#1a1a1a')
        ),
        template="plotly_white", # SWITCHED TO WHITE
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Raleway, sans-serif", color="#64748b"),
        hovermode="x unified",
        height=350,
        showlegend=False,
        margin=dict(l=10, r=10, t=60, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
