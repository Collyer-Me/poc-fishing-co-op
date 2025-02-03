# app.py
import streamlit as st
import pandas as pd

from truck_mapping import load_truck_data
from prepare_data import prepare_data_for_scheduling
from scheduling_logic import schedule_catches
from report_display import display_trips

st.title("POC Truck Logistics - Final Structured Report")

json_path = st.text_input("Path to combined_logistics.json", "combined_logistics.json")
uploaded_file = st.file_uploader("Upload Catch CSV/Excel", type=["csv","xlsx"])

if json_path and uploaded_file:
    try:
        trucks, config = load_truck_data(json_path)
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        st.stop()

    # Read
    if uploaded_file.name.lower().endswith(".csv"):
        df_catch = pd.read_csv(uploaded_file)
    else:
        df_catch = pd.read_excel(uploaded_file)

    # Possibly unify Offload Time if arrow issues
    if "Offload Time" in df_catch.columns:
        df_catch["Offload Time"] = df_catch["Offload Time"].astype(str)

    # Prepare
    df_filtered = prepare_data_for_scheduling(df_catch)

    st.subheader("Filtered Catch Data")
    st.dataframe(df_filtered)

    # Schedule
    trips, unassigned = schedule_catches(df_filtered, trucks, config)

    st.subheader("Scheduled Trips")
    if trips:
        display_trips(trips)
    else:
        st.info("No trips formed. Possibly all unassigned or no data.")

    if unassigned:
        st.subheader("Unassigned Catches")
        st.dataframe(pd.DataFrame(unassigned))
    else:
        st.success("All assigned within 4-hour limit!")
else:
    st.info("Provide JSON path & upload daily catch data.")
