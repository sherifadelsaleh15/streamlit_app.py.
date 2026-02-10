import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def format_currency(value):
    """Helper to format large numbers as currency-style strings"""
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.0f}"

def get_prediction(df, periods=4):
    """
    Calculates a lightweight forecast using Linear Regression (Scikit-Learn).
    Much faster and uses less memory than Prophet.
    """
    try:
        if len(df) < 2:
            return None
        
        # 1. Prepare Data
        # We need to sort by date for the line to make sense
        df = df.sort_values('dt').copy()
        
        # Convert Date to an "Ordinal" number (e.g. 738000) so Math can understand it
        df['date_ordinal'] = pd.to_datetime(df['dt']).map(pd.Timestamp.toordinal)
        
        X = df[['date_ordinal']]
        y = df['Value']
        
        # 2. Fit the Linear Model (Draw the best fit line)
        model = LinearRegression()
        model.fit(X, y)
        
        # 3. Create Future Dates
        last_date = pd.to_datetime(df['dt'].max())
        future_dates = [last_date + pd.DateOffset(months=i+1) for i in range(periods)]
        future_ordinals = pd.DataFrame({'date_ordinal': [d.toordinal() for d in future_dates]})
        
        # 4. Predict Future Values
        future_pred = model.predict(future_ordinals)
        
        # 5. Calculate "Confidence" (Standard Deviation of the history)
        # If history bounces around a lot, the shaded area will be wide.
        historical_pred = model.predict(X)
        residuals = y - historical_pred
        std_dev = residuals.std()
        
        # 6. Build the Result DataFrame
        forecast = pd.DataFrame({
            'ds': future_dates,
            'yhat': future_pred,
            'yhat_lower': future_pred - std_dev,  # Lower bound
            'yhat_upper': future_pred + std_dev   # Upper bound
        })
        
        return forecast

    except Exception as e:
        print(f"Prediction Error: {e}")
        return None
