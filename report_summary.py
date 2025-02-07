import streamlit as st

def display_summary(south_trips, north_trips):
    """
    Displays a summary of scheduled trips, separated by South and North regions.
    """
    south_count = len(south_trips)
    north_count = len(north_trips)
    
    total_trips = south_count + north_count
    total_catches = sum(len(trip["catches"]) for trip in south_trips + north_trips)

    south_avg_out_of_water = (
        sum(trip["out_of_water"] for trip in south_trips) / south_count if south_count > 0 else 0
    )
    north_avg_out_of_water = (
        sum(trip["out_of_water"] for trip in north_trips) / north_count if north_count > 0 else 0
    )

    st.write(f"### 🚛 South Region Trips: {south_count}")
    st.write(f"**Average Time Out of Water:** {south_avg_out_of_water:.0f} min")
    
    st.write(f"### 🚚 North Region Trips: {north_count}")
    st.write(f"**Average Time Out of Water:** {north_avg_out_of_water:.0f} min")

    st.write(f"### 📊 Total Trips: {total_trips}")
    st.write(f"**Total Catches Scheduled:** {total_catches}")
