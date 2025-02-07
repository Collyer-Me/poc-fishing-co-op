import streamlit as st
import pandas as pd

from truck_mapping import load_truck_data
from prepare_data import prepare_data_for_scheduling
from scheduling_logic import schedule_catches
from report_layout import show_results_with_tabs

st.title("POC Truck Logistics with Tabs & Summaries")

json_path = st.text_input("Path to combined_logistics.json", "combined_logistics.json")
uploaded_file = st.file_uploader("Upload Catch CSV/Excel", type=["csv", "xlsx"])

if json_path and uploaded_file:
    try:
        trucks, config = load_truck_data(json_path)
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        st.stop()

    # Read data
    if uploaded_file.name.lower().endswith(".csv"):
        df_catch = pd.read_csv(uploaded_file)
    else:
        df_catch = pd.read_excel(uploaded_file)

    if "Offload Time" in df_catch.columns:
        df_catch["Offload Time"] = df_catch["Offload Time"].astype(str)

    # Prepare data for scheduling
    df_filtered = prepare_data_for_scheduling(df_catch)

    st.subheader("Filtered Catch Data")
    st.dataframe(df_filtered)

    # Schedule trips
    trips, unassigned = schedule_catches(df_filtered, trucks, config)

    # Separate trips by area (South and North)
    south_trips = [trip for trip in trips if trip["area"] == "South"]
    north_trips = [trip for trip in trips if trip["area"] == "North"]

    # Display the results using tabs
    show_results_with_tabs(south_trips, north_trips, unassigned)
else:
    st.info("Please provide the JSON path & upload daily catch data.")
