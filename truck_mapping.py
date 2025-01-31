# truck_mapping.py
import json

def load_truck_data(json_path: str):
    with open(json_path, "r") as f:
        data = json.load(f)
    
    trucks = data["trucks"]
    config = data["logistics_config"]

    # Convert basket totals
    for t in trucks:
        t["Basket Total"] = int(t["Basket Total"]) if t["Basket Total"] else 0

    # Keep only active
    active_trucks = [t for t in trucks if t.get("Status","").lower() == "active"]
    return active_trucks, config
