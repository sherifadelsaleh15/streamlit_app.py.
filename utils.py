import pandas as pd

def format_currency(value):
    """Helper to format large numbers as currency-style strings"""
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.0f}"

def get_date_range_label(df):
    """Returns a string showing the range of data available"""
    if df.empty:
        return "No data"
    start = df['dt'].min().strftime('%b %Y')
    end = df['dt'].max().strftime('%b %Y')
    return f"Reporting Period: {start} - {end}"
