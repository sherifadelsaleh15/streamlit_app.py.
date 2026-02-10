import pandas as pd
from prophet import Prophet

def format_currency(value):
    """Helper to format large numbers as currency-style strings"""
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.0f}"

def get_date_range_label(df):
    """Returns a string showing the range of data available"""
    if df.empty or 'dt' not in df.columns:
        return "No data"
    start = df['dt'].min().strftime('%b %Y')
    end = df['dt'].max().strftime('%b %Y')
    return f"Reporting Period: {start} - {end}"

def get_prediction(df, periods=4):
    """
    Calculates the 4-month forecast using Prophet.
    Returns the forecast dataframe including yhat_lower and yhat_upper.
    """
    try:
        # Prophet requires exactly two columns: 'ds' (date) and 'y' (value)
        if len(df) < 2:
            return None
            
        m_df = df[['dt', 'Value']].rename(columns={'dt': 'ds', 'Value': 'y'})
        m_df['ds'] = pd.to_datetime(m_df['ds'])
        
        # Initialize Prophet with basic settings for monthly OKRs
        model = Prophet(
            yearly_seasonality=False, 
            weekly_seasonality=False, 
            daily_seasonality=False
        )
        model.fit(m_df)
        
        # Create future timeframe (MS = Month Start)
        future = model.make_future_dataframe(periods=periods, freq='MS')
        forecast = model.predict(future)
        
        return forecast
    except Exception as e:
        print(f"Prediction error: {e}")
        return None
