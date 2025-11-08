import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import math

from satellite_modules import (
    satellite_age_and_EOL,
    debris_collision_risk,
    solar_storm_risk,
    predict_deorbit_location,
)

# ---------- Helpers ----------

def generate_orbit_path(altitude_km: float, inclination_deg: float, num_points: int = 180):
    """
    Generate a simple illustrative ground-track style orbit path.

    Not physically perfect, but visually compelling and parameter-driven:
    - Uses inclination to tilt the track.
    - Wraps longitude  -180 to 180.
    """
    inc = math.radians(inclination_deg)
    points = []

    for i in range(num_points + 1):
        # angle along orbit
        theta = 2 * math.pi * (i / num_points)

        # simple model: lat oscillates with inclination, lon sweeps 0-360
        lat = math.degrees(math.asin(math.sin(inc) * math.sin(theta)))
        lon = math.degrees(theta) - 180  # center on 0

        points.append([lon, lat])

    return [{"name": "Orbit Path", "path": points}]

# ---------- Page Config ----------

st.set_page_config(
    page_title="SolarChaos | Satellite Lifecycle & Risk Forecaster",
    page_icon="🛰️",
    layout="wide",
)

# ---------- Global Styling ----------

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top, #0f172a 0, #020817 35%, #000000 100%);
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro", sans-serif;
    }
    #MainMenu, footer {visibility: hidden;}
    header {background: transparent;}

    .solar-card {
        padding: 1.3rem 1.5rem;
        border-radius: 18px;
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(148,163,253,0.18);
        box-shadow: 0 18px 40px rgba(15,23,42,0.9);
        backdrop-filter: blur(18px);
        transition: all 0.25s ease;
    }
    .solar-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 24px 65px rgba(56,189,248,0.25);
        border-color: rgba(129,140,248,0.55);
    }

    .solar-metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #9ca3af;
    }
    .solar-metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .solar-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.9);
        border: 1px solid rgba(148,163,253,0.35);
        font-size: 0.72rem;
        color: #9ca3af;
    }
    .section-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #6b7280;
    }
    .big-title {
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        color: #e5e7eb;
    }
    .sub-title {
        font-size: 0.9rem;
        color: #9ca3af;
    }
    .accent { color: #38bdf8; }
    .risk-high { color:#f97316; }
    .risk-medium { color:#fde047; }
    .risk-low { color:#22c55e; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------

col_logo, col_title, col_mode = st.columns([0.9, 3, 1.3])

with col_logo:
    st.markdown(
        """
        <div class="solar-card" style="padding:0.65rem 0.8rem; display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.35rem;">🛰️</span>
            <div>
                <div style="font-size:0.75rem; color:#9ca3af;">Mission Control</div>
                <div style="font-weight:600; font-size:0.92rem; color:#e5e7eb;">SolarChaos</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_title:
    st.markdown(
        """
        <div>
            <div class="section-label">Satellite Lifecycle & Space Risk Forecaster</div>
            <div class="big-title">
                Design safer missions. <span class="accent">Before launch.</span>
            </div>
            <div class="sub-title">
                Predict lifecycle, debris exposure, solar storm overlap & deorbit footprint in one interactive cockpit.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_mode:
    st.markdown(
        """
        <div class="solar-card" style="padding:0.7rem 0.8rem;">
            <div class="solar-pill">
                <span>👨‍⚖️</span><span>Judge Mode</span>
            </div>
            <div style="margin-top:0.45rem; font-size:0.7rem; color:#9ca3af;">
                Use presets + sliders live to narrate risk in seconds.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Sidebar Inputs ----------

with st.sidebar:
    st.markdown("## 🛰️ Mission Setup")

    demo_presets = {
        "Custom": None,
        "LEO Earth Observation": {
            "altitude": 550,
            "inclination": 97.6,
            "duration": 5,
        },
        "GEO Comms": {
            "altitude": 35786,
            "inclination": 0,
            "duration": 15,
        },
        "MEO Navigation": {
            "altitude": 20200,
            "inclination": 55,
            "duration": 12,
        },
    }

    preset = st.selectbox("Preset Scenarios", list(demo_presets.keys()), index=1)

    today = dt.date.today()
    default_launch = dt.date(today.year - 1, 1, 15)

    if demo_presets[preset]:
        alt_default = demo_presets[preset]["altitude"]
        inc_default = demo_presets[preset]["inclination"]
        dur_default = demo_presets[preset]["duration"]
    else:
        alt_default = 550
        inc_default = 97.6
        dur_default = 5

    mission_name = st.text_input("Mission Name", "Aurora-1 Recon")
    operator = st.text_input("Operator / Agency", "SolarChaos Labs")
    launch_date = st.date_input("Launch Date", default_launch)

    # These feed your module + visuals
    altitude_km = st.slider("Orbit Altitude (km)", 160, 42000, int(alt_default), step=10)
    inclination_deg = st.slider("Inclination (deg)", 0.0, 120.0, float(inc_default), step=0.5)

    # Planned mission duration (used for debris risk scaling / story)
    mission_duration_years = st.slider("Planned Mission Duration (years)", 1, 20, int(dur_default))

    st.markdown("---")
    st.caption("All visuals update live. Use this for 'what-if' storytelling in front of judges.")

# ---------- Core Calculations (your module) ----------

launch_str = launch_date.strftime("%Y-%m-%d")
lifecycle = satellite_age_and_EOL(launch_str, altitude_km)

age_years = lifecycle["age_years"]
lifetime_years = lifecycle["lifetime_years"]
eol_year_est = lifecycle["estimated_EOL_year"]

debris = debris_collision_risk(altitude_km, inclination_deg, mission_duration_years)
solar = solar_storm_risk(launch_date.year, eol_year_est)
deorbit = predict_deorbit_location(inclination_deg, eol_year_est)

# For charts: solar risk is categorical, create simple numeric score
solar_risk_map = {"Low": 0.25, "Moderate": 0.6, "High": 0.9}
solar_score = solar_risk_map.get(solar["solar_storm_risk"], 0.25)

# ---------- Top Metrics ----------

st.markdown("### ")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="solar-card">
            <div class="solar-metric-label">Mission Age</div>
            <div class="solar-metric-value">{age_years} yrs</div>
            <div class="sub-title">since {launch_date.strftime('%d %b %Y')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="solar-card">
            <div class="solar-metric-label">Est. Natural EOL</div>
            <div class="solar-metric-value">{eol_year_est}</div>
            <div class="sub-title">{lifetime_years} yrs lifetime @ {altitude_km} km</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    s_class = (
        "risk-high" if solar["solar_storm_risk"] == "High"
        else "risk-medium" if solar["solar_storm_risk"] == "Moderate"
        else "risk-low"
    )
    st.markdown(
        f"""
        <div class="solar-card">
            <div class="solar-metric-label">Solar Storm Risk</div>
            <div class="solar-metric-value {s_class}">{solar['solar_storm_risk']}</div>
            <div class="sub-title">Overlap with peak cycle years</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    d_level = debris["collision_risk_level"]
    d_score = debris["collision_risk_score"]
    d_class = (
        "risk-high" if d_level == "High"
        else "risk-medium" if d_level == "Moderate"
        else "risk-low"
    )
    st.markdown(
        f"""
        <div class="solar-card">
            <div class="solar-metric-label">Debris Collision Risk</div>
            <div class="solar-metric-value {d_class}">{d_level}</div>
            <div class="sub-title">Score: {d_score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Tabs ----------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🛰️ Mission Timeline",
        "🌞 Solar & Debris Analysis",
        "🌍 3D Orbit & Deorbit View",
        "📊 Technical Breakdown",
    ]
)

# ---- TAB 1: Mission Timeline ----

with tab1:
    colA, colB = st.columns([1.6, 1.4])

    with colA:
        st.markdown("#### 📆 Mission Lifecycle View")

        st.markdown(
            f"""
            <div class="solar-card">
                <div class="section-label">Narrative</div>
                <p>
                <b>{mission_name}</b> by <b>{operator}</b> operates at <b>{altitude_km} km</b>,
                inclined <b>{inclination_deg}°</b>. Based on atmospheric drag and altitude
                heuristics, the natural end-of-life is projected around <b>{eol_year_est}</b>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Build simple mission timeline using your mission_years
        mission_years = solar["mission_years"]
        df_timeline = pd.DataFrame(
            {
                "Year": mission_years,
                "Solar Peak Overlap": [
                    1 if y in solar["solar_peak_overlap"] else 0 for y in mission_years
                ],
            }
        )

        st.markdown("##### Solar Peak Overlap Across Mission")
        st.bar_chart(df_timeline.set_index("Year"), height=260)

    with colB:
        st.markdown("#### 🎯 Mission Health Index")

        # Combine risks + lifetime into one score (for judges)
        score = 92

        if d_level == "High":
            score -= 22
        elif d_level == "Moderate":
            score -= 10

        if solar["solar_storm_risk"] == "High":
            score -= 18
        elif solar["solar_storm_risk"] == "Moderate":
            score -= 7

        if altitude_km < 300:
            score -= 15

        score = max(35, min(99, score))

        if score >= 80:
            label = "Robust mission profile with manageable risks."
            emoji = "🟢"
        elif score >= 60:
            label = "Viable mission. Recommended mitigations for key phases."
            emoji = "🟡"
        else:
            label = "Aggressive / fragile profile. Revisit orbital & shielding choices."
            emoji = "🟠"

        st.markdown(
            f"""
            <div class="solar-card">
                <div class="solar-metric-label">Mission Health</div>
                <div class="solar-metric-value">{score}/100</div>
                <div class="sub-title">{emoji} {label}</div>
                <div style="margin-top:0.45rem; font-size:0.72rem; color:#9ca3af;">
                    Computed from debris band, solar exposure class, and orbital aggressiveness.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---- TAB 2: Solar & Debris Analysis ----

with tab2:
    col1, col2 = st.columns([1.4, 1.6])

    with col1:
        st.markdown("#### 🌞 Solar Storm Risk Profile")

        df_solar = pd.DataFrame(
            {
                "Year": mission_years,
                "Relative Risk": [
                    solar_score if y in solar["solar_peak_overlap"] else solar_score * 0.35
                    for y in mission_years
                ],
            }
        )
        st.line_chart(df_solar.set_index("Year"), height=260)

        overlap = solar["solar_peak_overlap"]
        if overlap:
            st.markdown(
                f"""
                <div class="solar-card" style="margin-top:0.7rem; font-size:0.78rem;">
                    <b>Peak overlap years:</b> {", ".join(map(str, overlap))}. 
                    Critical systems should be hardened for these epochs.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="solar-card" style="margin-top:0.7rem; font-size:0.78rem;">
                    No direct overlap with cycle peaks: lower long-term solar stress.
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown("#### 🗑️ Debris Collision Assessment")

        st.markdown(
            f"""
            <div class="solar-card" style="font-size:0.8rem;">
                <p>
                Orbit resides in the <b>{debris['debris_zone']}</b> congestion band with a 
                normalized collision risk score of <b>{debris['collision_risk_score']}</b>
                over a planned <b>{mission_duration_years}-year</b> mission.
                </p>
                <p>
                Risk level: <b>{debris['collision_risk_level']}</b>.
                Use this comparatively when exploring nearby orbital shells live.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        radar = {
            "Debris": min(5, debris["collision_risk_score"] * 8),
            "Solar": solar_score * 5,
            "Lifetime": min(5, lifetime_years / 6),
        }
        radar_str = " | ".join(f"{k}: {'█' * int(v)}" for k, v in radar.items())

        st.markdown(
            f"""
            <div class="solar-card" style="margin-top:0.7rem; font-size:0.78rem;">
                <div class="section-label">Compact Risk Radar</div>
                <div style="margin-top:0.25rem; font-family:monospace;">{radar_str}</div>
                <div style="margin-top:0.35rem; color:#6b7280;">
                    More blocks = more stress on that axis. Great for side-by-side mission comparisons.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---- TAB 3: 3D Orbit & Deorbit View ----

with tab3:
    st.markdown("#### 🌍 3D Orbit Path & Deorbit Corridor (Globe View)")

    st.markdown(
        f"""
        <div class="solar-card" style="margin-bottom:0.8rem; font-size:0.8rem;">
            <p>
            This globe visualizes an illustrative orbit based on your inputs:
            <b>{altitude_km} km</b>, <b>{inclination_deg}°</b>.
            The red marker shows the predicted deorbit footprint center at
            <b>{deorbit['predicted_latitude']}°</b>,
            <b>{deorbit['predicted_longitude']}°</b>
            around <b>{deorbit['predicted_deorbit_year']}</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        import pydeck as pdk

        # Build orbit polyline
        orbit_data = generate_orbit_path(altitude_km, inclination_deg)

        orbit_layer = pdk.Layer(
            "PathLayer",
            data=orbit_data,
            get_path="path",
            get_width=200000,
            width_min_pixels=2,
            get_color=[56, 189, 248],
            opacity=0.9,
        )

        deorbit_layer = pdk.Layer(
            "ScatterplotLayer",
            data=pd.DataFrame(
                {
                    "lat": [deorbit["predicted_latitude"]],
                    "lon": [deorbit["predicted_longitude"]],
                }
            ),
            get_position=["lon", "lat"],
            get_radius=600000,
            get_fill_color=[239, 68, 68],
            opacity=0.95,
        )

        view_state = pdk.ViewState(
            latitude=0,
            longitude=0,
            zoom=0,      # 0 shows full globe
            min_zoom=0,
            max_zoom=4,
            pitch=25,
            bearing=20,
        )

        globe_view = pdk.View(
            "GlobeView",
            controller=True,
        )

        deck = pdk.Deck(
            views=[globe_view],
            layers=[orbit_layer, deorbit_layer],
            initial_view_state=view_state,
            tooltip={"text": "Orbit path / Deorbit focus"},
        )

        st.pydeck_chart(deck)

    except Exception as e:
        st.error(f"3D globe visualization unavailable: {e}")
        st.info("Ensure `pydeck` is upgraded and this tab uses GlobeView exactly as shown.")

# ---- TAB 4: Technical Breakdown ----

with tab4:
    colL, colR = st.columns([1.6, 1.4])

    with colL:
        st.markdown(
            """
            <div class="solar-card" style="font-size:0.8rem;">
                <div class="section-label">Model Stack</div>
                <ul style="padding-left:1rem;">
                    <li><b>Lifetime:</b> Altitude-driven heuristic via <code>estimate_satellite_lifetime</code>.</li>
                    <li><b>Solar Storms:</b> Overlap of mission years with Solar Cycle 25 peak years.</li>
                    <li><b>Debris:</b> Altitude + inclination + mission length =&gt; congestion band + risk class.</li>
                    <li><b>Deorbit:</b> Inclination-based latitude band with stochastic longitudes.</li>
                    <li><b>3D Orbit:</b> Parameterized orbit track rendered via PyDeck.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with colR:
        st.markdown(
            """
            <div class="solar-card" style="font-size:0.78rem;">
                <div class="section-label">Hackathon Upgrade Hooks</div>
                <ul style="padding-left:1rem;">
                    <li>Swap heuristics with CelesTrak / Space-Track orbital elements.</li>
                    <li>Integrate NOAA SWPC for real-time solar indices.</li>
                    <li>Use NASA ORDEM data to weight debris zones realistically.</li>
                    <li>Export a one-page PDF risk brief per mission.</li>
                    <li>Add multi-satellite / constellation comparison mode.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# One-time flair
if "launched" not in st.session_state:
    st.session_state["launched"] = True
    st.balloons()
