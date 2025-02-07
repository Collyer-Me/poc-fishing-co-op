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
    Schedule trips based on the agreed logic:
      - Start each trip with the largest available truck.
      - Add catches if they match location, fit within truck capacity, and stay under max out-of-water time.
      - If a catch exceeds truck capacity OR has a different location, close the trip and start a new one.
      - If adding a catch would exceed max out-of-water time, close the trip and start a new one with the next largest available truck.
      - If no truck is available for a catch, mark it as unassigned.
    Returns: (trips, unassigned)
    """
    trips = []
    unassigned = []

    df["ReadyTime"] = df.apply(lambda r: parse_date_time(r.get("Offload Date"), r.get("Offload Time")), axis=1)
    df = df.dropna(subset=["ReadyTime"]).copy()
    
    if "Est. Baskets" in df.columns:
        df["Est. Baskets"] = df["Est. Baskets"].fillna(0).astype(int)
    else:
        df["Est. Baskets"] = 1
    
    df = df.sort_values(["Offload Date", "Location", "ReadyTime"])
    
    # Sort trucks by capacity (largest first)
    trucks = sorted(trucks, key=lambda t: t["Basket Total"], reverse=True)
    
    date_groups = df.groupby("Offload Date")
    
    for date_val, df_by_date in date_groups:
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
                truck_used = trucks[0]  # Start with the largest available truck
                
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
                    
                    trip_catches.append({
                        "Boat": cN.get("Boat", "Unknown"),
                        "ReadyTime": cN["ReadyTime"],
                        "LoadFinish": load_finishN,
                        "Baskets": cN["Est. Baskets"]
                    })
                    used_capacity += neededN
                    i += 1
                    
                    # Check max out-of-water time
                    final_arrival_time = load_finishN + datetime.timedelta(minutes=travel_minutes)
                    final_offload_time = final_arrival_time + datetime.timedelta(minutes=(len(trip_catches) * offload_per_catch))
                    out_of_water_time = (final_offload_time - trip_catches[0]["ReadyTime"]).total_seconds() / 60.0
                    
                    if out_of_water_time > max_time:
                        break  # Close the trip if max out-of-water time exceeded
                
                # Close and finalize the trip
                required_baskets = sum(catch["Baskets"] for catch in trip_catches)
                
                # Find the next largest available truck
                possible_trucks = [t for t in trucks if t["Basket Total"] >= required_baskets]
                if possible_trucks:
                    truck_used = max(possible_trucks, key=lambda t: t["Basket Total"])  # Largest available truck
                else:
                    unassigned.extend(trip_catches)
                    continue
                
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
