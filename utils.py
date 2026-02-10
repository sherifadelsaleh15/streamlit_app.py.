import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def get_prediction(df, periods=4):
    try:
        if len(df) < 2:
            return None
        
        # 1. Prepare Historical Data
        df = df.dropna(subset=['Value', 'dt']).sort_values('dt').copy()
        df['dt'] = pd.to_datetime(df['dt'])
        
        # 2. Train Model
        df['date_ordinal'] = df['dt'].map(pd.Timestamp.toordinal)
        X = df[['date_ordinal']]
        y = df['Value']
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 3. Define the "Stitch" Point (The last known actual)
        last_row = df.iloc[-1]
        last_date = last_row['dt']
        last_val = last_row['Value']
        
        # 4. Generate Future Dates (Starting 1 month after last_date)
        future_dates = [last_date + pd.DateOffset(months=i+1) for i in range(periods)]
        future_ordinals = pd.DataFrame({'date_ordinal': [d.toordinal() for d in future_dates]})
        
        # 5. Predict Future Values
        future_pred = model.predict(future_ordinals)
        std_dev = (y - model.predict(X)).std()
        
        # 6. Create Forecast DF
        forecast = pd.DataFrame({
            'ds': future_dates,
            'yhat': future_pred,
            'yhat_lower': future_pred - (std_dev * 1.2),
            'yhat_upper': future_pred + (std_dev * 1.2)
        })

        # 7. THE STITCH: Add the last known point to the START of forecast
        # This makes the orange line connect to the blue line perfectly
        stitch_row = pd.DataFrame({
            'ds': [last_date],
            'yhat': [last_val],
            'yhat_lower': [last_val],
            'yhat_upper': [last_val]
        })
        
        forecast = pd.concat([stitch_row, forecast]).reset_index(drop=True)
        
        return forecast

    except Exception as e:
        print(f"Forecasting Error: {e}")
        return None
