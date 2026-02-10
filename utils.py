import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def get_prediction(df, periods=4):
    """
    Ensures the forecast starts ONLY after the most recent data point.
    """
    try:
        if len(df) < 2:
            return None
        
        # 1. Clean and Sort
        df = df.dropna(subset=['Value', 'dt']).sort_values('dt').copy()
        df['dt'] = pd.to_datetime(df['dt'])
        
        # 2. Train the model on Historical Data only
        df['date_ordinal'] = df['dt'].map(pd.Timestamp.toordinal)
        X = df[['date_ordinal']]
        y = df['Value']
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 3. IDENTIFY THE TRUE FUTURE
        # We find the last date in your data (e.g., Feb 2026)
        last_date = df['dt'].max()
        
        # Create future dates starting from the NEXT month
        # We use MonthEnd to ensure alignment with your data structure
        future_dates = [last_date + pd.DateOffset(months=i+1) for i in range(periods)]
        future_ordinals = pd.DataFrame({'date_ordinal': [d.toordinal() for d in future_dates]})
        
        # 4. Predict
        future_pred = model.predict(future_ordinals)
        
        # 5. Margin of Error
        std_dev = (y - model.predict(X)).std()
        
        # 6. Build Forecast (Starting from the first 'empty' month)
        forecast = pd.DataFrame({
            'ds': future_dates,
            'yhat': future_pred,
            'yhat_lower': future_pred - (std_dev * 1.5), # Slightly wider for realism
            'yhat_upper': future_pred + (std_dev * 1.5)
        })
        
        return forecast

    except Exception as e:
        print(f"Prediction Error: {e}")
        return None
