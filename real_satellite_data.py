import requests
from skyfield.api import load

# --- 1. Get Satellite Metadata from OBDH.space ---
def get_satellite_metadata(norad_id: int):
    """
    Fetch launch info, status, and decay history for a satellite using NORAD ID.
    """
    try:
        url = f"https://api.obdh.space/satellite/{norad_id}"
        response = requests.get(url, timeout=10)
        data = response.json()

        return {
            "name": data.get("OBJECT_NAME"),
            "launch_date": data.get("LAUNCH_DATE"),
            "launch_site": data.get("LAUNCH_SITE"),
            "operator": data.get("OBJECT_OWNER"),
            "status": data.get("OBJECT_STATUS"),
            "decay_date": data.get("DECAY_DATE"),
            "object_type": data.get("OBJECT_TYPE")
        }
    except Exception as e:
        return {"error": f"Failed to fetch metadata: {e}"}

# --- 2. Get Live Orbital Position from CelesTrak TLE ---
def get_live_position(norad_id: int):
    """
    Fetch current latitude, longitude, and altitude using TLE data from CelesTrak.
    """
    try:
        tle_url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"
        lines = requests.get(tle_url).text.strip().splitlines()
        if len(lines) < 3:
            return {"error": "TLE data not found"}

        ts = load.timescale()
        satellite = load.tle(lines[1], lines[2], ts)
        now = ts.now()
        subpoint = satellite.at(now).subpoint()

        return {
            "latitude": round(subpoint.latitude.degrees, 2),
            "longitude": round(subpoint.longitude.degrees, 2),
            "altitude_km": round(subpoint.elevation.km, 2)
        }
    except Exception as e:
        return {"error": f"Failed to fetch position: {e}"}

#test code
if __name__ == "__main__":
    # Example: ISS (ZARYA) has NORAD ID 25544
    norad_id = 25544

    meta = get_satellite_metadata(norad_id)
    print("📄 Metadata:", meta)

    pos = get_live_position(norad_id)
    print("📍 Live Position:", pos)
