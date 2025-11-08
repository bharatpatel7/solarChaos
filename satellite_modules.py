from datetime import datetime
import math
import random
from typing import Dict, List, Union

# --- Constants ---
SOLAR_CYCLE_25_PEAK_YEARS = [2025, 2026, 2027]
CLUTTER_ZONES = {
    "Low": (200, 500),
    "Medium": (500, 800),
    "High": (800, 1000)
}

# --- Lifetime Estimation ---
def estimate_satellite_lifetime(altitude_km: float) -> float:
    """
    Estimate satellite lifetime in months based on altitude.

    Parameters:
        altitude_km (float): Orbital altitude in kilometers

    Returns:
        float: Estimated lifetime in months
    """
    if altitude_km < 300:
        return 0.5
    elif altitude_km < 500:
        return 2 + (altitude_km - 300) * 0.05
    elif altitude_km < 800:
        return 10 + (altitude_km - 500) * 0.1
    else:
        return 50 + (altitude_km - 800) * 0.2

def satellite_age_and_EOL(launch_date_str: str, altitude_km: float) -> Dict[str, Union[int, float]]:
    """
    Calculate satellite age and estimated end-of-life year.

    Parameters:
        launch_date_str (str): Launch date in YYYY-MM-DD format
        altitude_km (float): Orbital altitude in kilometers

    Returns:
        dict: Age in years, estimated EOL year, and lifetime in years
    """
    launch_date = datetime.strptime(launch_date_str, "%Y-%m-%d")
    today = datetime.today()
    age_years = (today - launch_date).days / 365.25

    lifetime_months = estimate_satellite_lifetime(altitude_km)
    lifetime_years = lifetime_months / 12
    eol_year = launch_date.year + int(lifetime_years)

    return {
        "age_years": round(age_years, 2),
        "estimated_EOL_year": eol_year,
        "lifetime_years": round(lifetime_years, 2)
    }

# --- Debris Risk ---
def debris_collision_risk(altitude_km: float, inclination_deg: float, mission_years: float) -> Dict[str, Union[str, float]]:
    """
    Estimate debris collision risk based on altitude, inclination, and mission duration.

    Parameters:
        altitude_km (float): Orbital altitude in kilometers
        inclination_deg (float): Orbital inclination in degrees
        mission_years (float): Mission duration in years

    Returns:
        dict: Debris zone, risk score, and risk level
    """
    zone = "Very Low"
    risk_score = 0.05

    for label, (low, high) in CLUTTER_ZONES.items():
        if low <= altitude_km <= high:
            zone = label
            risk_score = {"Low": 0.1, "Medium": 0.3, "High": 0.6}[label]
            break

    if inclination_deg > 80:
        risk_score *= 1.5

    risk_score *= mission_years / 5

    if risk_score > 0.5:
        level = "High"
    elif risk_score > 0.2:
        level = "Moderate"
    else:
        level = "Low"

    return {
        "debris_zone": zone,
        "collision_risk_score": round(risk_score, 2),
        "collision_risk_level": level
    }

# --- Solar Storm Risk ---
def solar_storm_risk(launch_year: int, eol_year: int, peak_years: List[int] = SOLAR_CYCLE_25_PEAK_YEARS) -> Dict[str, Union[str, List[int]]]:
    """
    Estimate solar storm risk based on overlap with solar cycle peaks.

    Parameters:
        launch_year (int): Launch year
        eol_year (int): Estimated end-of-life year
        peak_years (list): List of solar peak years (default: Solar Cycle 25)

    Returns:
        dict: Mission years, overlapping peak years, and risk level
    """
    mission_years = list(range(launch_year, eol_year + 1))
    overlap = [year for year in peak_years if year in mission_years]

    if len(overlap) >= 2:
        risk = "High"
    elif len(overlap) == 1:
        risk = "Moderate"
    else:
        risk = "Low"

    return {
        "mission_years": mission_years,
        "solar_peak_overlap": overlap,
        "solar_storm_risk": risk
    }

# --- Deorbit Prediction ---
def predict_deorbit_location(inclination_deg: float, eol_year: int) -> Dict[str, Union[int, float]]:
    """
    Predict approximate deorbit location based on inclination and randomness.

    Parameters:
        inclination_deg (float): Orbital inclination in degrees
        eol_year (int): Estimated end-of-life year

    Returns:
        dict: Predicted latitude, longitude, and year
    """
    max_lat = min(abs(inclination_deg), 90)
    latitude = round(random.uniform(-max_lat, max_lat), 2)
    longitude = round(random.uniform(-180, 180), 2)

    return {
        "predicted_deorbit_year": eol_year,
        "predicted_latitude": latitude,
        "predicted_longitude": longitude
    }
