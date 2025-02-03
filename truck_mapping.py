# truck_mapping.py

import json

def load_truck_data(json_path: str):
    """
    Reads trucks + config from a combined_logistics.json file.
    Returns a (trucks_list, config_dict).
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    trucks = data["trucks"]
    config = data["logistics_config"]

    for t in trucks:
        t["Basket Total"] = int(t["Basket Total"]) if t["Basket Total"] else 0

    # Filter only active trucks
    active_trucks = [t for t in trucks if t.get("Status","").lower() == "active"]

    return active_trucks, config
