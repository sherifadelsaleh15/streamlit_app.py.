fig.update_layout(
        title=dict(
            text=f"{metric_name}", 
            font=dict(family="Raleway, sans-serif", size=18, color='#ffffff')
        ),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Raleway, sans-serif", color="#a3a3a3"), # Sets font for axes/legend
        hovermode="x unified",
        height=350,
        margin=dict(l=10, r=10, t=50, b=10)
    )
