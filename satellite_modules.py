from datetime import datetime
import math

def estimate_satellite_lifetime(altitude_km):
    """
    Estimate satellite lifetime based on altitude using a simplified exponential model.
    """
    if altitude_km < 300:
        return 0.5  # months
    elif altitude_km < 500:
        return 2 + (altitude_km - 300) * 0.05  # months
    elif altitude_km < 800:
        return 10 + (altitude_km - 500) * 0.1  # months
    else:
        return 50 + (altitude_km - 800) * 0.2  # months

def satellite_age_and_EOL(launch_date_str, altitude_km):
    """
    Calculate satellite age and estimated end-of-life.
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

# Example usage
result = satellite_age_and_EOL("2025-11-07", 500)
print(result)


def debris_collision_risk(altitude_km, inclination_deg, mission_years):
    """
    Estimate debris collision risk based on altitude and inclination.
    """
    # Define clutter zones (simplified)
    clutter_zones = {
        "low": (200, 500),
        "medium": (500, 800),
        "high": (800, 1000)
    }

    # Determine zone
    if clutter_zones["low"][0] <= altitude_km <= clutter_zones["low"][1]:
        zone = "Low"
        risk_score = 0.1
    elif clutter_zones["medium"][0] <= altitude_km <= clutter_zones["medium"][1]:
        zone = "Medium"
        risk_score = 0.3
    elif clutter_zones["high"][0] <= altitude_km <= clutter_zones["high"][1]:
        zone = "High"
        risk_score = 0.6
    else:
        zone = "Very Low"
        risk_score = 0.05

    # Adjust for inclination (polar orbits face more risk)
    if inclination_deg > 80:
        risk_score *= 1.5

    # Adjust for mission duration
    risk_score *= mission_years / 5  # Normalize to 5-year missions

    # Final risk level
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

# Example usage
debris_result = debris_collision_risk(altitude_km=500, inclination_deg=51.6, mission_years=6)
print(debris_result)

def solar_storm_risk(launch_year, eol_year):
    """
    Estimate solar storm risk based on overlap with solar cycle peaks.
    """
    # Known peak years for Solar Cycle 25
    peak_years = [2025, 2026, 2027]

    # Count how many peak years overlap with mission
    risk_years = [year for year in peak_years if launch_year <= year <= eol_year]
    risk_level = "High" if len(risk_years) >= 2 else "Moderate" if len(risk_years) == 1 else "Low"

    return {
        "mission_years": list(range(launch_year, eol_year + 1)),
        "solar_peak_overlap": risk_years,
        "solar_storm_risk": risk_level
    }

# Example usage
solar_result = solar_storm_risk(launch_year=2025, eol_year=2031)
print(solar_result)




import random

def predict_deorbit_location(inclination_deg, eol_year):
    """
    Predict approximate deorbit location based on inclination and random decay factors.
    This would suggest a re-entry near southern Australia — a common zone for uncontrolled deorbits.
    """
    # Latitude range based on inclination
    max_lat = min(abs(inclination_deg), 90)
    latitude = round(random.uniform(-max_lat, max_lat), 2)

    # Longitude based on Earth's rotation and randomness
    longitude = round(random.uniform(-180, 180), 2)

    return {
        "predicted_deorbit_year": eol_year,
        "predicted_latitude": latitude,
        "predicted_longitude": longitude
    }

# Example usage
deorbit_result = predict_deorbit_location(inclination_deg=51.6, eol_year=2031)
print(deorbit_result)
