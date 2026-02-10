import pandas as pd

def calculate_kpis(df):
    """Calculates the high-level numbers for the top of the dashboard"""
    if df.empty:
        return {}
    
    kpis = {
        "total_value": df['Val'].sum(),
        "avg_value": df['Val'].mean(),
        "active_objectives": df['Objective'].nunique(),
        "active_regions": df['Region'].nunique()
    }
    return kpis

def get_performance_summary(df):
    """Groups data by Objective and OKR for the summary table"""
    summary = df.groupby(['Objective', 'OKR'])['Val'].agg(['sum', 'mean', 'count']).reset_index()
    summary.columns = ['Objective', 'OKR', 'Total', 'Average', 'Entries']
    return summary
