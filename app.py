# app.py
import streamlit as st
import pandas as pd
import datetime

from truck_mapping import load_truck_data
from prepare_data import prepare_data_for_scheduling
from scheduling_logic import schedule_catches

st.title("Grouped by (Date->Location->Time), multi-catch, area matching, dropoff displayed")

json_file = st.text_input("Path to combined_logistics.json", "combined_logistics.json")
uploaded_file = st.file_uploader("Upload Catch CSV/Excel", type=["csv","xlsx"])

if json_file and uploaded_file:
    try:
        trucks, config = load_truck_data(json_file)
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        st.stop()

    # read data
    if uploaded_file.name.lower().endswith(".csv"):
        df_catch = pd.read_csv(uploaded_file)
    else:
        df_catch = pd.read_excel(uploaded_file)

    # unify Offload Time if arrow issues
    if "Offload Time" in df_catch.columns:
        df_catch["Offload Time"] = df_catch["Offload Time"].astype(str)

    # filter
    df_filtered = prepare_data_for_scheduling(df_catch)
    if df_filtered.empty:
        st.warning("No valid catch data after filtering.")
    else:
        st.subheader("Filtered Catch Data")
        st.dataframe(df_filtered)

        # schedule
        trips, unassigned = schedule_catches(df_filtered, trucks, config)

        st.subheader("Scheduled Trips")
        if trips:
            for i, trip in enumerate(trips, start=1):
                st.markdown(f"### Trip #{i} - Truck: {trip['truck_id']} - Date: {trip['trip_date']} - Location: {trip['location']}")
                st.write(f"Drop-off Destination: {trip['dropoffDestination']}")
                st.write(f"Depart Time: {trip['departTime']}")
                st.write(f"Arrive Drop Time: {trip['arriveDropTime']}")
                st.write(f"Final Offload Time: {trip['finalOffloadTime']}")

                cdf = pd.DataFrame(trip["catches"])
                if not cdf.empty:
                    for col in ["ReadyTime","LoadFinish","EarliestLoadFinish"]:
                        if col in cdf.columns:
                            cdf[col] = cdf[col].apply(
                                lambda x: x.strftime("%Y-%m-%d %H:%M") if isinstance(x, datetime.datetime) else str(x)
                            )
                st.dataframe(cdf)
        else:
            st.info("No trips formed. Possibly all unassigned or no data.")

        if unassigned:
            st.subheader("Unassigned Catches")
            st.dataframe(pd.DataFrame(unassigned))
        else:
            st.success("All assigned under 4-hour limit!")
else:
    st.info("Please provide the JSON path & upload daily catch data.")
