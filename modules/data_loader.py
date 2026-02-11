url = base_url + tab.replace(" ", "%20")
df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')

            # Standardize Columns
            df.columns = [c.replace(' ', '_') for c in df.columns]
            # 1. Standardize Columns (removes spaces and special characters)
            # This turns 'Month/Date' into 'Month_Date' and 'Value/Position' into 'Value_Position'
            df.columns = [c.replace(' ', '_').replace('/', '_') for c in df.columns]

            # Standardize Date Column
            for col in ['Month', 'Date_Month', 'dt']:
            # 2. Standardize Date Column
            # Added 'Month_Date' to the list to match our new sheet
            for col in ['Month', 'Date_Month', 'dt', 'Month_Date']:
if col in df.columns:
df['dt'] = pd.to_datetime(df[col], errors='coerce')
break

            # 3. Handle Numeric Data for Rankings
            # If it's the position tracking tab, ensure the value is a number
            if 'Value_Position' in df.columns:
                df['Value_Position'] = pd.to_numeric(df['Value_Position'], errors='coerce')
            
all_data[tab] = df
except Exception as e:
st.error(f"Error loading tab {tab}: {e}")
