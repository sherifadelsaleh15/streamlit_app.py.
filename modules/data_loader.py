url = base_url + tab.replace(" ", "%20")

try:
    df = pd.read_csv(url).dropna(how='all').dropna(axis=1, how='all')

    # Standardize Columns
    df.columns = [
        c.replace(' ', '_').replace('/', '_')
        for c in df.columns
    ]

    # Standardize Date Column
    for col in ['Month', 'Date_Month', 'dt', 'Month_Date']:
        if col in df.columns:
            df['dt'] = pd.to_datetime(df[col], errors='coerce')
            break

    # Handle Numeric Data for Rankings
    if 'Value_Position' in df.columns:
        df['Value_Position'] = pd.to_numeric(
            df['Value_Position'],
            errors='coerce'
        )

    all_data[tab] = df

except Exception as e:
    st.error(f"Error loading tab {tab}: {e}")
