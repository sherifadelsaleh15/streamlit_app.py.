import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

def generate_forecast(df, val_col, months_to_forecast=3):
    """
    Predicts future values using Linear Regression.
    """
    try:
        if df.empty or len(df.dropna(subset=[val_col])) < 2:
            return pd.DataFrame()

        # Prepare historical data
        df_hist = df.groupby('dt')[val_col].sum().reset_index().sort_values('dt')
        
        # Convert dates to ordinal numbers for regression
        X = np.array([d.toordinal() for d in df_hist['dt']]).reshape(-1, 1)
        y = df_hist[val_col].values
        
        # Train Model
        model = LinearRegression()
        model.fit(X, y)
        
        # Create Future Dates
        last_date = df_hist['dt'].max()
        future_dates = [last_date + pd.DateOffset(months=i+1) for i in range(months_to_forecast)]
        future_X = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        
        # Predict
        preds = model.predict(future_X)
        
        return pd.DataFrame({'dt': future_dates, val_col: preds})
    except:
        return pd.DataFrame()
