# location_mapping.py

LOCATION_MAP = {
    "Lancelin": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 90
    },
    "Leeman": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 110
    },
    "Dongara (Port Denison)": {
        "area": "North",
        "drop_off_location": "Geraldton",
        "travel_minutes": 70
    },
    "Cervantes": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 120
    },
    "Two Rocks": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 60
    },
    "Freshwater": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 30
    },
    "Jurien": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 160
    },
    "Mandurah": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 75
    },
    "Ledge Point": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 140
    },
    "Kalbarri": {
        "area": "North",
        "drop_off_location": "Geraldton",
        "travel_minutes": 160
    },
    "Wedge Island": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 130
    },
    "Geraldton": {
        "area": "North",
        "drop_off_location": "Geraldton",
        "travel_minutes": 15
    },
    "Fremantle": {
        "area": "South",
        "drop_off_location": "Fremantle/Welshpool",
        "travel_minutes": 5
    }
    # Add or modify entries as needed for your real ports
}

def get_location_info(location: str):
    """
    Return a dict with:
      - area (North/South)
      - drop_off_location (e.g. "Geraldton", "Fremantle/Welshpool")
      - travel_minutes (int)
    If location not found, return a fallback with 'Unknown' and 90 minutes.
    """
    key = location.strip()
    info = LOCATION_MAP.get(key, None)
    if info is not None:
        return info
    else:
        return {
            "area": "Unknown",
            "drop_off_location": "Unknown",
            "travel_minutes": 90
        }
