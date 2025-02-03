# scheduling_logic.py

import datetime
import pandas as pd
from location_mapping import get_location_info

def parse_date_time(date_val, time_val):
    """Combine 'Offload Date' + 'Offload Time' into a single datetime or None."""
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
        for fmt in ["%H:%M","%H:%M:%S"]:
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
    The final clarified approach:
      - group by Offload Date, then by Location
      - sort by time
      - pick fresh truck each trip (area match + capacity)
      - add multiple catches if earliest loaded won't exceed 4h (stack logic)
      - finalize trip once no more can be added, move on.
    Returns: (trips, unassigned)
    """

    trips = []
    unassigned = []

    # unify date/time into "ReadyTime"
    df["ReadyTime"] = df.apply(
        lambda r: parse_date_time(r.get("Offload Date"), r.get("Offload Time")),
        axis=1
    )
    df = df.dropna(subset=["ReadyTime"]).copy()

    # ensure baskets is int
    if "Est. Baskets" in df.columns:
        df["Est. Baskets"] = df["Est. Baskets"].fillna(0).astype(int)
    else:
        df["Est. Baskets"] = 1

    # group by Offload Date
    date_groups = df.groupby("Offload Date")

    for date_val, df_by_date in date_groups:
        # sort by location, then time
        df_by_date = df_by_date.sort_values(["Location","ReadyTime"])

        loc_groups = df_by_date.groupby("Location")
        for loc, df_loc in loc_groups:
            df_loc_sorted = df_loc.sort_values("ReadyTime").to_dict("records")

            # get location info => area, dropoff
            loc_info = get_location_info(loc)
            loc_area = loc_info["area"]
            drop_dest = loc_info["drop_off_location"]
            travel_minutes = loc_info["travel_minutes"]

            i = 0
            n = len(df_loc_sorted)

            while i < n:
                c0 = df_loc_sorted[i]
                needed0 = c0["Est. Baskets"]

                # pick a truck with area & capacity
                feasible_trucks = [
                    t for t in trucks
                    if t["Basket Total"] >= needed0 and t.get("Area","").lower() == loc_area.lower()
                ]
                if not feasible_trucks:
                    unassigned.append({
                        "Boat": c0.get("Boat","Unknown"),
                        "Location": loc,
                        "Reason": "No available truck matching area/capacity"
                    })
                    i += 1
                    continue

                truck_used = feasible_trucks[0]  # pick first or any

                trip_catches = []
                used_capacity = 0

                load_time_min = config["load_time_minutes"]
                offload_per_catch = config["offload_time_per_catch_minutes"]
                max_time = config["max_time_out_of_water_minutes"]

                # first catch
                load_start_first = c0["ReadyTime"]
                load_finish_first = load_start_first + datetime.timedelta(minutes=load_time_min)
                earliest_load_finish = load_finish_first
                used_capacity += needed0

                trip_catches.append({
                    "Boat": c0.get("Boat","Unknown"),
                    "ReadyTime": c0["ReadyTime"],
                    "LoadFinish": load_finish_first,
                    "EarliestLoadFinish": earliest_load_finish,
                    "Baskets": c0["Est. Baskets"]
                })

                i_next = i+1
                i += 1

                # try adding subsequent
                while i_next < n:
                    cN = df_loc_sorted[i_next]
                    needN = cN["Est. Baskets"]
                    if used_capacity + needN > truck_used["Basket Total"]:
                        break

                    last_load_finish = trip_catches[-1]["LoadFinish"]
                    actual_load_startN = max(last_load_finish, cN["ReadyTime"])
                    load_finishN = actual_load_startN + datetime.timedelta(minutes=load_time_min)

                    M = len(trip_catches)+1
                    final_arrival = load_finishN + datetime.timedelta(minutes=travel_minutes)
                    final_offload = final_arrival + datetime.timedelta(minutes=(M*offload_per_catch))
                    out_of_water = final_offload - earliest_load_finish
                    out_of_water_min = out_of_water.total_seconds()/60.0

                    if out_of_water_min <= max_time:
                        trip_catches.append({
                            "Boat": cN.get("Boat","Unknown"),
                            "ReadyTime": cN["ReadyTime"],
                            "LoadFinish": load_finishN,
                            "EarliestLoadFinish": earliest_load_finish,
                            "Baskets": cN["Est. Baskets"]
                        })
                        used_capacity += needN
                        i_next += 1
                    else:
                        break

                # finalize trip
                last_load_finish = trip_catches[-1]["LoadFinish"]
                final_arrival = last_load_finish + datetime.timedelta(minutes=travel_minutes)
                M_catches = len(trip_catches)
                final_offload = final_arrival + datetime.timedelta(minutes=M_catches*offload_per_catch)

                trips.append({
                    "trip_date": str(date_val.date()) if isinstance(date_val, datetime.datetime) else str(date_val),
                    "truck_id": truck_used["FLEET"],
                    "location": loc,
                    "dropoffDestination": drop_dest,
                    "departTime": last_load_finish,     # "Depart Port"
                    "arriveDropTime": final_arrival,
                    "finalOffloadTime": final_offload,
                    "catches": trip_catches
                })

                i = i_next

    return trips, unassigned
