import datetime
import pandas as pd
from location_mapping import get_location_info

def parse_date_time(date_val, time_val):
    """
    Combine 'Offload Date' + 'Offload Time' into a single datetime or return None on failure.
    """
    if not date_val or not time_val:
        return None

    # parse date
    if isinstance(date_val, datetime.date):
        date_part = date_val
    else:
        try:
            date_part = datetime.datetime.strptime(str(date_val), "%Y-%m-%d").date()
        except:
            return None

    # parse time
    if isinstance(time_val, datetime.time):
        time_part = time_val
    else:
        time_part = None
        for fmt in ["%H:%M", "%H:%M:%S"]:
            try:
                time_part = datetime.datetime.strptime(str(time_val), fmt).time()
                break
            except:
                pass
        if not time_part:
            return None

    return datetime.datetime.combine(date_part, time_part)

def schedule_catches(df: pd.DataFrame, trucks: list, config: dict):
    """
    Schedule trips ensuring each truck is only used once per day.
    """
    trips = []
    unassigned = []
    used_trucks = set()  # Track used trucks per day

    df["ReadyTime"] = df.apply(lambda r: parse_date_time(r.get("Offload Date"), r.get("Offload Time")), axis=1)
    df = df.dropna(subset=["ReadyTime"]).copy()

    if "Est. Baskets" in df.columns:
        df["Est. Baskets"] = df["Est. Baskets"].fillna(0).astype(int)
    else:
        df["Est. Baskets"] = 1

    df = df.sort_values(["Offload Date", "Location", "ReadyTime"])
    trucks = sorted(trucks, key=lambda t: t["Basket Total"], reverse=True)

    date_groups = df.groupby("Offload Date")

    for date_val, df_by_date in date_groups:
        used_trucks.clear()  # Reset used trucks for the new day
        loc_groups = df_by_date.groupby("Location")

        for loc, df_loc in loc_groups:
            df_loc_sorted = df_loc.sort_values("ReadyTime").to_dict("records")
            loc_info = get_location_info(loc)
            loc_area = loc_info["area"]
            drop_dest = loc_info["drop_off_location"]
            travel_minutes = loc_info["travel_minutes"]

            i = 0
            n = len(df_loc_sorted)
            load_time_min = config["load_time_minutes"]
            offload_per_catch = config["offload_time_per_catch_minutes"]
            max_time = config["max_time_out_of_water_minutes"]

            while i < n:
                trip_catches = []
                used_capacity = 0

                # Find the largest available truck that has not been used today
                available_trucks = [t for t in trucks if t["FLEET"] not in used_trucks]
                if not available_trucks:
                    # No available truck left for the day, mark remaining catches as unassigned
                    unassigned.extend(df_loc_sorted[i:])
                    break

                truck_used = available_trucks[0]  # Pick the largest available truck
                used_trucks.add(truck_used["FLEET"])  # Mark truck as used

                while i < n:
                    cN = df_loc_sorted[i]
                    neededN = cN["Est. Baskets"]

                    # Check if catch fits the current trip
                    if (used_capacity + neededN > truck_used["Basket Total"]) or (trip_catches and cN["Location"] != loc):
                        break  # Close the current trip

                    # Determine load times
                    if trip_catches:
                        last_load_finish = trip_catches[-1]["LoadFinish"]
                        actual_load_startN = max(last_load_finish, cN["ReadyTime"])
                    else:
                        actual_load_startN = cN["ReadyTime"]

                    load_finishN = actual_load_startN + datetime.timedelta(minutes=load_time_min)

                    # Check max out-of-water time BEFORE adding the catch
                    final_arrival_time = load_finishN + datetime.timedelta(minutes=travel_minutes)
                    predicted_final_offload_time = final_arrival_time + datetime.timedelta(minutes=(len(trip_catches) + 1) * offload_per_catch)
                    predicted_out_of_water_time = (predicted_final_offload_time - (trip_catches[0]["ReadyTime"] if trip_catches else cN["ReadyTime"])).total_seconds() / 60.0
                    
                    if predicted_out_of_water_time > max_time:
                        break  # Close the trip if adding the catch would exceed max out-of-water time

                    # Add catch to trip
                    trip_catches.append({
                        "Boat": cN.get("Boat", "Unknown"),
                        "ReadyTime": cN["ReadyTime"],
                        "LoadFinish": load_finishN,
                        "Baskets": cN["Est. Baskets"]
                    })
                    used_capacity += neededN
                    i += 1

                    # Final trip checks
                    final_arrival_time = load_finishN + datetime.timedelta(minutes=travel_minutes)
                    final_offload_time = final_arrival_time + datetime.timedelta(minutes=(len(trip_catches) * offload_per_catch))
                    out_of_water_time = (final_offload_time - (trip_catches[0]["ReadyTime"] if trip_catches else trip_catches[-1]["ReadyTime"])).total_seconds() / 60.0
                    
                    if out_of_water_time > max_time:
                        break  # Close the trip if max out-of-water time exceeded

                # Finalize the trip
                required_baskets = sum(catch["Baskets"] for catch in trip_catches)

                for catch in trip_catches:
                    catch["OutOfWaterMinutes"] = (final_offload_time - catch["ReadyTime"]).total_seconds() / 60.0

                trips.append({
                    "trip_date": str(date_val),
                    "truck_id": truck_used["FLEET"],
                    "location": loc,
                    "dropoffDestination": drop_dest,
                    "area": loc_area,
                    "departTime": trip_catches[-1]["LoadFinish"],
                    "arriveDropTime": final_arrival_time,
                    "finalOffloadTime": final_offload_time,
                    "OutOfWaterMinutes": out_of_water_time,
                    "catches": trip_catches
                })

    return trips, unassigned
