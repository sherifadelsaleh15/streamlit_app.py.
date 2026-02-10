import pandas as pd
import numpy as np

def generate_forecast(df, periods=6):
    """Calculates a simple linear projection for the next few months"""
    if len(df) < 3:
        return pd.DataFrame()

    # Sort and group by date to get a single time series
    ts = df.groupby('dt')['Val'].sum().reset_index().sort_values('dt')
    
    # Create numeric X values (0, 1, 2...) for the regression
    ts['x'] = np.arange(len(ts))
    y = ts['Val'].values
    x = ts['x'].values
    
    # Simple linear regression (slope and intercept)
    slope, intercept = np.polyfit(x, y, 1)
    
    # Generate future dates
    last_date = ts['dt'].max()
    future_dates = pd.date_range(last_date, periods=periods + 1, freq='ME')[1:]
    
    # Calculate future Y values
    future_x = np.arange(len(ts), len(ts) + periods)
    future_y = slope * future_x + intercept
    
    # Ensure no negative forecasts
    future_y = np.maximum(future_y, 0)
    
    forecast_df = pd.DataFrame({
        'dt': future_dates,
        'Val': future_y,
        'Month_Display': future_dates.strftime('%b %Y'),
        'Status': 'Forecast'
    })
    
    return forecast_df
