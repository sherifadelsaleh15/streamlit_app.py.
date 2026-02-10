import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def render_metric_chart(df, metric_name, forecast_df=None):
    """Renders an area chart with an optional forecast line"""
    chart_data = df[df['Metric'] == metric_name].groupby(['dt', 'Month_Display'])['Val'].sum().reset_index()
    chart_data = chart_data.sort_values('dt')
    chart_data['Status'] = 'Actual'

    fig = go.Figure()

    # 1. Add Actual Data (Area)
    fig.add_trace(go.Scatter(
        x=chart_data['Month_Display'], y=chart_data['Val'],
        fill='tozeroy', name='Actual',
        line=dict(color='#3b82f6', width=3)
    ))

    # 2. Add Forecast Data (Dashed Line)
    if forecast_df is not None and not forecast_df.empty:
        # Connect the last actual point to the first forecast point
        last_actual = chart_data.iloc[-1:]
        combined_forecast = pd.concat([last_actual, forecast_df])
        
        fig.add_trace(go.Scatter(
            x=combined_forecast['Month_Display'], y=combined_forecast['Val'],
            name='Forecast',
            line=dict(color='#94a3b8', width=3, dash='dash')
        ))

    fig.update_layout(
        title=f"Trend & Projection: {metric_name}",
        hovermode="x unified",
        template="plotly_white",
        height=350,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
