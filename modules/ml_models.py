import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def get_prediction(df):
    """
    Core forecasting logic for the 'Monthly Performance Trends' section.
    Expects a DataFrame with 'ds' (date) and 'Value' columns.
    """
    try:
        if len(df) < 2:
            return None
        
        # Prepare data for Scikit-Learn
        df = df.copy()
        df['ds'] = pd.to_datetime(df['ds'])
        df['ordinal'] = df['ds'].map(pd.Timestamp.toordinal)
        
        X = df[['ordinal']].values
        y = df['Value'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Create 3-month future dates
        last_date = df['ds'].max()
        future_dates = pd.date_range(last_date, periods=4, freq='MS')[1:]
        future_ordinal = future_dates.map(pd.Timestamp.toordinal).values.reshape(-1, 1)
        
        preds = model.predict(future_ordinal)
        
        # Simple confidence interval (10% margin for visualization)
        forecast = pd.DataFrame({
            'ds': future_dates,
            'yhat': preds,
            'yhat_lower': preds * 0.9,
            'yhat_upper': preds * 1.1
        })
        
        return forecast
    except Exception:
        return None

def generate_forecast(df, value_col):
    """
    General forecast wrapper for the main dashboard view.
    """
    try:
        # Prepare data for forecast
        prep_df = df.groupby('dt')[value_col].sum().reset_index()
        prep_df.columns = ['ds', 'Value']
        return get_prediction(prep_df)
    except Exception:
        return pd.DataFrame()
