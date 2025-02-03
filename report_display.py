# report_display.py

import streamlit as st
import pandas as pd
import datetime

def highlight_out_of_water(val):
    if val >= 240:
        return "background-color: red; color: white;"
    elif val >= 210:
        return "background-color: yellow;"
    return ""

def format_time(dt):
    """Convert datetime to 'YYYY-MM-DD HH:MM' or return str(dt)."""
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)

def display_trips(trips):
    """
    For each trip:
      - "Arrive Port" => earliest ReadyTime among the catches
      - "Depart Port" => trip['departTime']
      - Table => 'Boat Arrival Time' (ReadyTime) column before 'Load Finish'
    """
    for i, trip in enumerate(trips, start=1):
        st.markdown(f"### Trip #{i} - Truck **{trip['truck_id']}**")

        # ARRIVE PORT => earliest 'ReadyTime' among catches
        if trip["catches"]:
            arrive_port_time = min(c["ReadyTime"] for c in trip["catches"] if "ReadyTime" in c)
        else:
            arrive_port_time = None
        arrive_port_str = format_time(arrive_port_time) if arrive_port_time else "N/A"

        # DEPART PORT => trip['departTime']
        depart_port_time = trip.get("departTime", None)
        depart_port_str = format_time(depart_port_time) if depart_port_time else "N/A"

        st.write(f"**Arrive Port**: {arrive_port_str}")
        st.write(f"**Depart Port**: {depart_port_str}")
        st.write(f"**Location**: {trip.get('location','Unknown')}")
        st.write(f"**Drop-off**: {trip.get('dropoffDestination','Unknown')}")

        arrive_drop = trip.get("arriveDropTime", None)
        final_off = trip.get("finalOffloadTime", None)
        st.write(f"Arrive Drop Time: {format_time(arrive_drop)}")
        st.write(f"Final Offload Time: {format_time(final_off)}")

        df_catches = pd.DataFrame(trip["catches"])

        # Reorder columns => "ReadyTime" => "Boat Arrival Time", place it before LoadFinish
        col_map = {
            "Boat": "Vessel",
            "ReadyTime": "Boat Arrival Time",
            "LoadFinish": "Load Finish",
            "OutOfWaterMinutes": "Out-of-Water (min)"
        }

        # Desired order
        desired_cols = ["Boat","ReadyTime","LoadFinish","Baskets","OutOfWaterMinutes"]
        existing_cols = df_catches.columns.tolist()
        keep_cols = [c for c in desired_cols if c in existing_cols]
        df_catches = df_catches[keep_cols]
        df_catches.rename(columns=col_map, inplace=True)

        # Format times
        time_cols = ["Boat Arrival Time","Load Finish"]
        for tc in time_cols:
            if tc in df_catches.columns:
                df_catches[tc] = df_catches[tc].apply(format_time)

        # optional highlight out-of-water
        if "Out-of-Water (min)" in df_catches.columns:
            styled_df = df_catches.style.applymap(highlight_out_of_water, subset=["Out-of-Water (min)"])
        else:
            styled_df = df_catches.style

        st.dataframe(styled_df)

        # Summaries
        if "Baskets" in df_catches.columns:
            total_baskets = df_catches["Baskets"].sum()
            st.write(f"**Total Baskets**: {total_baskets}")

        st.write("---")
