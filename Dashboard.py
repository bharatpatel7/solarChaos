import streamlit as st
from datetime import datetime



# from satellite_modules import satellite_age_and_EOL, predict_deorbit_location, solar_storm_risk, debris_collision_risk
from satellite_modules import (
    satellite_age_and_EOL,
    predict_deorbit_location,
    solar_storm_risk,
    debris_collision_risk
)

st.title(" Satellite Lifecycle & Space Risk Forecaster")

# --- User Inputs ---
st.sidebar.header("Satellite Launch Info")
launch_date = st.sidebar.date_input("Launch Date", value=datetime(2025, 11, 7))
altitude_km = st.sidebar.slider("Orbit Altitude (km)", 200, 2000, 500)
inclination_deg = st.sidebar.slider("Inclination (°)", 0, 180, 51)

# --- Calculations ---
launch_year = launch_date.year
age_eol = satellite_age_and_EOL(launch_date.strftime("%Y-%m-%d"), altitude_km)
deorbit = predict_deorbit_location(inclination_deg, age_eol["estimated_EOL_year"])
solar = solar_storm_risk(launch_year, age_eol["estimated_EOL_year"])
debris = debris_collision_risk(altitude_km, inclination_deg, age_eol["lifetime_years"])

# --- Results ---
st.subheader("📆 Mission Timeline")
st.write(f"Satellite Age: **{age_eol['age_years']} years**")
st.write(f"Estimated End-of-Life: **{age_eol['estimated_EOL_year']}**")

st.subheader("🌍 Predicted Deorbit Location")
st.write(f"Latitude: **{deorbit['predicted_latitude']}°**, Longitude: **{deorbit['predicted_longitude']}°**")

st.subheader("🌞 Solar Storm Risk")
st.write(f"Risk Level: **{solar['solar_storm_risk']}**")
st.write(f"Peak Years Overlap: {solar['solar_peak_overlap']}")

st.subheader("🗑️ Debris Collision Risk")
st.write(f"Zone: **{debris['debris_zone']}**")
st.write(f"Risk Level: **{debris['collision_risk_level']}** (Score: {debris['collision_risk_score']})")






