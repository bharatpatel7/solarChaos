from skyfield.api import load, EarthSatellite
import requests

# --- 1. Local Metadata Fallback ---
SATELLITE_METADATA = {
    25544: {
        "name": "ISS (ZARYA)",
        "launch_date": "1998-11-20",
        "launch_site": "Baikonur Cosmodrome",
        "operator": "Roscosmos / NASA",
        "status": "Active",
        "decay_date": None,
        "object_type": "Space Station"
    },
    20580: {
        "name": "Hubble Space Telescope",
        "launch_date": "1990-04-24",
        "launch_site": "Kennedy Space Center",
        "operator": "NASA",
        "status": "Active",
        "decay_date": None,
        "object_type": "Telescope"
    },
    39084: {
        "name": "NOAA-20",
        "launch_date": "2017-11-18",
        "launch_site": "Vandenberg AFB",
        "operator": "NOAA",
        "status": "Active",
        "decay_date": None,
        "object_type": "Weather Satellite"
    }
}

def get_satellite_metadata(norad_id: int):
    """
    Return satellite metadata from local dictionary.
    """
    return SATELLITE_METADATA.get(norad_id, {"error": "Metadata not available for this satellite."})

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
        satellite = EarthSatellite(lines[1], lines[2], lines[0], ts)
        now = ts.now()
        subpoint = satellite.at(now).subpoint()

        return {
            "latitude": round(subpoint.latitude.degrees, 2),
            "longitude": round(subpoint.longitude.degrees, 2),
            "altitude_km": round(subpoint.elevation.km, 2)
        }
    except Exception as e:
        return {"error": f"Failed to fetch position: {e}"}

# --- Test Code ---
if __name__ == "__main__":
    norad_id = 25544  # ISS

    meta = get_satellite_metadata(norad_id)
    print("📄 Metadata:", meta)

    pos = get_live_position(norad_id)
    print("📍 Live Position:", pos)
