import streamlit as st
from report_display import display_trips
from report_summary import display_summary

def show_results_with_tabs(south_trips, north_trips, unassigned):
    """
    Display the reports in Streamlit Tabs: South Trips, North Trips, Unassigned, and Summary.
    """
    tabs = st.tabs(["🚛 South Trips", "🚚 North Trips", "⚠️ Unassigned", "📊 Summary"])

    with tabs[0]:  # South Trips
        if south_trips:
            st.subheader("🚛 South Area Trips Report")
            display_trips(south_trips)
        else:
            st.warning("No trips assigned to the South region.")

    with tabs[1]:  # North Trips
        if north_trips:
            st.subheader("🚚 North Area Trips Report")
            display_trips(north_trips)
        else:
            st.warning("No trips assigned to the North region.")

    with tabs[2]:  # Unassigned Catches
        if unassigned:
            st.subheader("⚠️ Unassigned Catches")
            st.dataframe(unassigned)  # Show unassigned catches in a table
        else:
            st.success("All catches were successfully assigned!")

    with tabs[3]:  # Summary
        st.subheader("📊 Summary of Scheduled Trips")
        display_summary(south_trips, north_trips)
