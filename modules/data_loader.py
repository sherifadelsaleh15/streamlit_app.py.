import pandas as pd


def load_and_preprocess_data(sheet_id, tabs):
    """
    Load multiple Google Sheet tabs as CSV and preprocess them.
    Returns a dictionary of DataFrames.
    """

    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="

    all_data = {}

    for tab in tabs:
        url = base_url + tab.replace(" ", "%20")

        try:
            df = pd.read_csv(url).dropna(how="all").dropna(axis=1, how="all")

            # 🔹 Standardize column names
            df.columns = [
                c.strip()
                .replace(" ", "_")
                .replace("/", "_")
                .replace("-", "_")
                for c in df.columns
            ]

            # 🔹 Standardize date column
            for col in ["Month", "Date_Month", "Month_Date", "dt"]:
                if col in df.columns:
                    df["dt"] = pd.to_datetime(df[col], errors="coerce")
                    break

            # 🔹 Convert ranking column to numeric if exists
            if "Value_Position" in df.columns:
                df["Value_Position"] = pd.to_numeric(
                    df["Value_Position"], errors="coerce"
                )

            all_data[tab] = df

        except Exception as e:
            print(f"Error loading tab {tab}: {e}")

    return all_data
