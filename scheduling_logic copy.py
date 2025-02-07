import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from location_mapping import get_location_info

def parse_date_time(date_str, time_str):
    """Parse date and time safely, removing unnecessary timestamps and handling errors."""
    try:
        # Convert the date string to YYYY-MM-DD format only (removing extra timestamps)
        if isinstance(date_str, pd.Timestamp):
            date_part = date_str.date()  # ✅ Removes "00:00:00"
        else:
            date_part = pd.to_datetime(str(date_str).split(" ")[0], errors="coerce").date()

        


        # If date_part is NaT, skip this row
        if pd.isna(date_part):
            st.write(f"🚨 Skipping invalid date: {date_str}")
            return None

        # Handle different time formats
        if isinstance(time_str, pd.Timestamp):
            time_part = time_str.time()

        elif isinstance(time_str, str):
            time_str = time_str.strip()

            # Handle case where time includes a range (e.g., "12:00 - 13:00")
            if "-" in time_str:
                time_str = time_str.split("-")[0].strip()  # ✅ Extract first time (e.g., "12:00")

            # Normalize time format (some might be "HH:MM:SS", some might be "HH:MM")
            try:
                if len(time_str) == 5:  # "10:00"
                    time_part = pd.to_datetime(time_str, format="%H:%M", errors="coerce").time()
                elif len(time_str) == 8:  # "10:00:00"
                    time_part = pd.to_datetime(time_str, format="%H:%M:%S", errors="coerce").time()
                else:
                    st.write(f"⚠️ Unrecognized time format: {time_str}")
                    return None

                if pd.isna(time_part):
                    st.write(f"⚠️ Skipping invalid time: {time_str}")
                    return None

            except Exception as e:
                st.write(f"⚠️ Time parsing error: {time_str} - {e}")
                return None

        else:
            st.write(f"⚠️ Skipping invalid time format: {time_str}")
            return None

        # Ensure time_part is valid before combining
        if time_part is None:
            st.write(f"🚨 Skipping row due to invalid time: {date_str} {time_str}")
            return None

        # Debugging output
        # st.write(f"✅ Parsed Date: {date_part}, Parsed Time: {time_part}")

        return datetime.combine(date_part, time_part)

    except Exception as e:
        st.write(f"❌ Error parsing date/time: {e} ({date_str} {time_str})")
        return None



def schedule_catches(df, trucks):
    """Schedule the truck trips while ensuring all constraints are met."""
    trips = []
    unassigned = []

    # Sort catches by Offload Date, Location, and Offload Time
    df = df.sort_values(by=["Offload Date", "Location", "Offload Time"])

    # Available trucks pool (by area)
    available_trucks = {truck["Area"]: [] for truck in trucks}
    for truck in trucks:
        available_trucks[truck["Area"]].append(truck)

    # Iterate over sorted catches
    for _, row in df.iterrows():
        ready_time = parse_date_time(row["Offload Date"], row["Offload Time"])
        if ready_time is None:
            unassigned.append(row.to_dict())
            continue

        location = row["Location"]
        drop_off_location = row["drop_off_location"]
        area = row["Area"]

        # Check for an available truck in the correct area
        if area not in available_trucks or not available_trucks[area]:
            unassigned.append(row.to_dict())
            continue

        assigned_truck = available_trucks[area].pop(0)  # Take the first available truck

        trip = {
            "truck_id": assigned_truck["FLEET"],  # Assign truck ID
            "trip_start": ready_time,  # When the trip starts picking up catches
            "location": location,  # The port where truck picks up catches
            "dropoffDestination": drop_off_location,  # Where truck drops off
            "departTime": None,  # To be determined later
            "arriveDropTime": None,  # When truck arrives at drop-off
            "finalOffloadTime": None,  # When last catch is offloaded
            "out_of_water": 0,  # Placeholder, will be calculated later
            "area": area,
            "catches": []  # List of all assigned catches for this trip
        }

        # Add catch to trip
        trip["catches"].append({
            "Boat": row["Boat"],
            "ReadyTime": ready_time,
            "LoadFinish": ready_time + timedelta(minutes=15),  # Load time is 15 min
            "Baskets": row["Baskets"],
            "OutOfWaterMinutes": 0  # Placeholder, will be updated later
        })

        # Calculate departure and drop-off times
        trip["departTime"] = trip["catches"][0]["LoadFinish"]  # Truck departs after last load
        travel_time = row["travel_minutes"]
        trip["arriveDropTime"] = trip["departTime"] + timedelta(minutes=travel_time)

        # Calculate final offload time (15 min per catch)
        trip["finalOffloadTime"] = trip["arriveDropTime"] + timedelta(minutes=len(trip["catches"]) * 15)

        # Calculate max out-of-water time
        trip["out_of_water"] = (trip["finalOffloadTime"] - trip["trip_start"]).total_seconds() / 60  # Convert to minutes
        for catch in trip["catches"]:
            catch["OutOfWaterMinutes"] = trip["out_of_water"]  # Assign to each catch

        trips.append(trip)

    return trips, unassigned
