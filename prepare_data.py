# prepare_data.py
import pandas as pd

def prepare_data_for_scheduling(df_catch: pd.DataFrame):
    # Example filters
    if "Type" in df_catch.columns:
        df_catch = df_catch[df_catch["Type"] == "Trip"]
    
    if "Location" in df_catch.columns:
        df_catch = df_catch.dropna(subset=["Location"])
        df_catch = df_catch[df_catch["Location"].astype(str).str.strip() != ""]

    if "Offload Date" in df_catch.columns:
        df_catch["Offload Date"] = pd.to_datetime(df_catch["Offload Date"], errors='coerce')
        df_catch = df_catch.dropna(subset=["Offload Date"])
        if not df_catch.empty:
            most_recent_day = df_catch["Offload Date"].max()
            df_filtered = df_catch[df_catch["Offload Date"] == most_recent_day].copy()
        else:
            df_filtered = pd.DataFrame()
    else:
        df_filtered = pd.DataFrame()

    return df_filtered
