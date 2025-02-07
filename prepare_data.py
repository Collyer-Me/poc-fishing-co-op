import pandas as pd
from location_mapping import LOCATION_MAP  # Ensure correct import

def prepare_data_for_scheduling(df_catch: pd.DataFrame):
    """
    Filters and prepares the data:
      - Keep only rows where Type='Trip'
      - Drop rows with blank 'Location'
      - Convert 'Offload Date' to datetime & pick the most recent day
      - Assign `drop_off_location`, `Area`, and `travel_minutes` from LOCATION_MAP
    """

    if "Type" in df_catch.columns:
        df_catch = df_catch[df_catch["Type"] == "Trip"]

    if "Location" in df_catch.columns:
        df_catch = df_catch.dropna(subset=["Location"])
        df_catch = df_catch[df_catch["Location"].astype(str).str.strip() != ""]

    if "Offload Date" in df_catch.columns:
        df_catch["Offload Date"] = pd.to_datetime(df_catch["Offload Date"], errors='coerce')
        df_catch = df_catch.dropna(subset=["Offload Date"])
        if not df_catch.empty:
            # Pick the most recent date
            most_recent_day = df_catch["Offload Date"].max()
            df_filtered = df_catch[df_catch["Offload Date"] == most_recent_day].copy()
        else:
            df_filtered = pd.DataFrame()
    else:
        df_filtered = pd.DataFrame()

    # ✅ **Assign drop_off_location, Area, and travel_minutes from LOCATION_MAP**
    if not df_filtered.empty and "Location" in df_filtered.columns:
        df_filtered["drop_off_location"] = df_filtered["Location"].map(
            lambda loc: LOCATION_MAP.get(loc, {}).get("drop_off_location", "Unknown")
        )

        df_filtered["Area"] = df_filtered["Location"].map(
            lambda loc: LOCATION_MAP.get(loc, {}).get("area", "Unknown")
        )

        df_filtered["travel_minutes"] = df_filtered["Location"].map(
            lambda loc: LOCATION_MAP.get(loc, {}).get("travel_minutes", 0)  # Default to 0 if missing
        )

    return df_filtered
