import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sgp4.earth_gravity import wgs84
from sgp4.io import twoline2rv
import requests
from io import BytesIO
try:
    from PIL import Image
except Exception:
    Image = None

from satellite_modules import (
    satellite_age_and_EOL,
    debris_collision_risk,
    solar_storm_risk,
    predict_deorbit_location,
)

# ---------- Helpers ----------

def generate_orbit_path(altitude_km: float, inclination_deg: float, num_points: int = 180):
    """
    Generate a simple illustrative 3D orbit path.

    Returns a numpy array of points with x, y, z coordinates.
    """
    inc = math.radians(inclination_deg)
    R = 6371 + altitude_km  # Earth radius + altitude in km
    points = []

    for i in range(num_points + 1):
        theta = 2 * math.pi * (i / num_points)
        
        # Calculate 3D coordinates
        x = R * math.cos(theta) * math.cos(inc)
        y = R * math.cos(theta) * math.sin(inc)
        z = R * math.sin(theta)
        
        points.append([x, y, z])

    return np.array(points)

# New helper functions for 3D visualization
def create_earth_sphere():
    """Create a textured Earth sphere for Plotly"""
    phi = np.linspace(0, 2*np.pi, 100)
    theta = np.linspace(-np.pi/2, np.pi/2, 100)
    phi, theta = np.meshgrid(phi, theta)
    
    R = 6371  # Earth radius in km
    x = R * np.cos(theta) * np.cos(phi)
    y = R * np.cos(theta) * np.sin(phi)
    z = R * np.sin(theta)
    
    return go.Surface(
        x=x, y=y, z=z,
        colorscale='Blues',
        showscale=False,
        opacity=0.8
    )

def plot_orbit_3d(altitude_km, inclination_deg, debris_data=None):
    """Create 3D orbit visualization with debris"""
    fig = make_subplots(specs=[[{'type': 'scene'}]])
    
    # Add Earth
    fig.add_trace(create_earth_sphere())
    
    # Generate orbit points
    orbit_points = generate_orbit_path(altitude_km, inclination_deg)
    
    # Add orbit path
    fig.add_trace(go.Scatter3d(
        x=orbit_points[:, 0],
        y=orbit_points[:, 1],
        z=orbit_points[:, 2],
        mode='lines',
        line=dict(color='#38bdf8', width=3),
        name='Orbit Path'
    ))
    
    # Add debris if provided
    if debris_data is not None:
            if 'size' in debris_data and 'color' in debris_data:
                # For enhanced debris visualization with different sizes and colors
                fig.add_trace(go.Scatter3d(
                    x=debris_data['x'],
                    y=debris_data['y'],
                    z=debris_data['z'],
                    mode='markers',
                    marker=dict(
                        size=debris_data['size'],
                        color=debris_data['color'],
                        opacity=0.7
                    ),
                    name='Space Debris'
                ))
            else:
                # Fallback for simple debris visualization
                fig.add_trace(go.Scatter3d(
                    x=debris_data['x'],
                    y=debris_data['y'],
                    z=debris_data['z'],
                    mode='markers',
                    marker=dict(
                        size=4,
                        color='red',
                        opacity=0.6
                    ),
                    name='Space Debris'
                ))
    
    # Update layout
    fig.update_layout(
        scene=dict(
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            xaxis=dict(showbackground=False),
            yaxis=dict(showbackground=False),
            zaxis=dict(showbackground=False)
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# ---------- Page Config ----------

st.set_page_config(
    page_title="SolarChaos | Satellite Lifecycle & Risk Forecaster",
    page_icon="🚀",
    layout="wide",
)

# ---------- Global Styling ----------

st.markdown(
    """
        <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root {
        --space-text: #e2e8f0;
        --space-muted: #94a3b8;
        --space-card: rgba(7,12,32,0.82);
        --space-card-border: rgba(99,102,241,0.35);
        --space-accent: #38bdf8;
    }
    .stApp {
        position: relative;
        min-height: 100vh;
        background-color: #01030f;
        background-image:
            radial-gradient(circle at 20% 20%, rgba(59,130,246,0.25), transparent 42%),
            radial-gradient(circle at 80% 15%, rgba(236,72,153,0.18), transparent 45%),
            radial-gradient(circle at 10% 85%, rgba(34,211,238,0.26), transparent 55%),
            radial-gradient(circle at 65% 75%, rgba(147,197,253,0.18), transparent 45%),
            linear-gradient(135deg, #01030f 0%, #030618 38%, #040018 100%);
        background-attachment: fixed;
        color: var(--space-text);
        font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, 'SF Pro', sans-serif;
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            radial-gradient(1px 1px at 20% 30%, rgba(248,250,252,0.45), transparent),
            radial-gradient(2px 2px at 60% 10%, rgba(96,165,250,0.45), transparent),
            radial-gradient(1.5px 1.5px at 35% 80%, rgba(34,211,238,0.35), transparent),
            radial-gradient(1px 1px at 85% 60%, rgba(248,250,252,0.4), transparent);
        opacity: 0.35;
        pointer-events: none;
        z-index: 0;
    }
    .stApp > div {
        position: relative;
        z-index: 1;
    }

    #MainMenu, footer {visibility: hidden;}
    header {background: transparent;}

    .solar-card {
        padding: 1.3rem 1.6rem;
        border-radius: 22px;
        background: var(--space-card);
        border: 1px solid var(--space-card-border);
        box-shadow: 0 25px 50px rgba(2,6,23,0.9), 0 0 45px rgba(14,165,233,0.25);
        backdrop-filter: blur(24px);
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .solar-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56,189,248,0.8);
        box-shadow: 0 30px 65px rgba(3,7,18,0.95), 0 0 60px rgba(56,189,248,0.35);
    }

    .solar-metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--space-muted);
    }
    .solar-metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: var(--space-accent);
        text-shadow: 0 0 12px rgba(56,189,248,0.45);
    }
    .solar-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.3rem 0.85rem;
        border-radius: 999px;
        background: rgba(8,12,40,0.9);
        border: 1px solid rgba(59,130,246,0.35);
        font-size: 0.72rem;
        color: var(--space-muted);
        box-shadow: inset 0 0 12px rgba(59,130,246,0.2);
    }
    .section-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        color: rgba(148,163,184,0.9);
    }
    .big-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        color: var(--space-text);
        text-shadow: 0 0 30px rgba(15,118,255,0.35);
    }
    .sub-title {
        font-size: 0.95rem;
        color: var(--space-muted);
    }
    .accent { color: var(--space-accent); }
    .risk-high { color:#fb7185; }
    .risk-medium { color:#facc15; }
    .risk-low { color:#34d399; }

    .rocket-launch {
        position: fixed;
        bottom: 2.5rem;
        left: calc(50% - 2rem);
        width: 4rem;
        z-index: 1000;
        pointer-events: none;
        animation: rocket-flight 6s ease-in-out forwards;
    }
    .rocket-emoji {
        font-size: 3.5rem;
        display: block;
        text-align: center;
        filter: drop-shadow(0 0 14px rgba(56,189,248,0.9));
        animation: rocket-wiggle 1.1s ease-in-out infinite;
    }
    .rocket-trail {
        width: 0.9rem;
        height: 5rem;
        margin: 0.4rem auto 0;
        border-radius: 999px;
        background: linear-gradient(180deg, rgba(248,250,252,0), rgba(248,113,113,0.85), rgba(251,191,36,0.9));
        box-shadow: 0 0 25px rgba(251,191,36,0.65);
        animation: trail-fade 6s ease-out forwards;
    }
    @keyframes rocket-flight {
        0% { transform: translate(0, 0) scale(0.85); opacity: 0; }
        15% { opacity: 1; }
        100% { transform: translate(0, -450px) scale(1.25); opacity: 0; }
    }
    @keyframes rocket-wiggle {
        0%,100% { transform: translateX(0); }
        50% { transform: translateX(-6px); }
    }
    @keyframes trail-fade {
        0% { opacity: 0; height: 0; }
        20% { opacity: 1; height: 5rem; }
        100% { opacity: 0; height: 7rem; }
    }
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

# ---- TAB 2: Solar & Debris Analysis (simplified) ----

with tab2:
    st.markdown("#### 🌞 Solar Storm & Space Debris Risk Analysis")

    # Let user pick which risk to explore; we'll not show the large info cards — only the 3D models
    risk_type = st.radio(
        "What would you like to learn about?",
        ["🌞 Solar Storm Risk", "🛸 Space Debris Risk"],
        horizontal=True,
        key="risk_selector"
    )

    st.markdown("### ")

    if risk_type == "🌞 Solar Storm Risk":
        # Animated, more informative solar 3D view with moving satellite and improved energy waves
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown("#### Watch How Solar Storms Affect Your Satellite!")

            # Animation controls
            autoplay = st.checkbox("Autoplay animation", value=True, key="solar_autoplay")
            speed_ms = st.slider("Animation speed (ms per frame)", 40, 800, 180, step=20, key="solar_speed")
            num_frames = 24  # slightly smoother

            # Build spherical mesh (lower resolution for performance)
            theta = np.linspace(0, 2 * np.pi, 64)
            phi = np.linspace(0, np.pi, 32)
            theta, phi = np.meshgrid(theta, phi)

            r = 1.0
            x = r * np.sin(phi) * np.cos(theta)
            y = r * np.sin(phi) * np.sin(theta)
            z = r * np.cos(phi)

            # Deterministic RNG for consistent visuals
            rng = np.random.RandomState(2025)

            # Flares specification
            n_flares = 14
            flare_angles = rng.rand(n_flares) * 2 * np.pi
            flare_heights = rng.rand(n_flares) * 0.7 + 0.35

            # Energy wave rings (concentric animated rings) for aesthetic energy ripples
            n_rings = 5
            ring_base_radii = np.linspace(1.02, 1.18, n_rings)
            ring_colors = ['#ffd93d', '#ffb86b', '#ff8a65', '#ff6b6b', '#ff4757']

            # Precompute satellite path positions for frames
            sat_radius = 2.0
            sat_path_x = [sat_radius * math.cos(2 * math.pi * f / num_frames) for f in range(num_frames)]
            sat_path_y = [sat_radius * math.sin(2 * math.pi * f / num_frames) for f in range(num_frames)]
            sat_path_z = [0.2 * math.sin(2 * math.pi * f / num_frames / 2) for f in range(num_frames)]

            # Build base surface trace
            base_intensity = np.sin(6 * theta) * np.cos(3 * phi)
            traces = [go.Surface(x=x, y=y, z=z, surfacecolor=base_intensity,
                                 colorscale=[[0, '#fff5b1'], [0.5, '#ffa07a'], [1, '#ff4500']],
                                 showscale=False, opacity=0.96, name='Solar Surface')]

            # Add placeholder for rings (as line loops) and flares; frames will update them
            for i in range(n_rings):
                t = np.linspace(0, 2 * np.pi, 120)
                xr = ring_base_radii[i] * np.cos(t)
                yr = ring_base_radii[i] * np.sin(t)
                zr = 0.025 * np.sin(3 * t)  # subtle ripples
                traces.append(go.Scatter3d(x=xr, y=yr, z=zr, mode='lines',
                                           line=dict(color=ring_colors[i], width=4), opacity=0.6, showlegend=False))

            # Add placeholder flares
            for i in range(n_flares):
                ang = flare_angles[i]
                h = flare_heights[i]
                pts = np.linspace(1.0, 1.0 + h, 30)
                xf = pts * np.cos(ang)
                yf = pts * np.sin(ang)
                zf = np.linspace(-0.35, 0.35, len(pts)) * (0.7 + 0.3 * rng.rand())
                traces.append(go.Scatter3d(x=xf, y=yf, z=zf, mode='lines',
                                           line=dict(color='#ff4757', width=3 + (i % 3)), opacity=0.9, showlegend=False))

            # Satellite path (line) and marker (will be updated per frame)
            traces.append(go.Scatter3d(x=[sat_path_x[0]], y=[sat_path_y[0]], z=[sat_path_z[0]],
                                       mode='lines', line=dict(color='#38bdf8', width=2), name='Satellite Path', showlegend=False))
            traces.append(go.Scatter3d(x=[sat_path_x[0]], y=[sat_path_y[0]], z=[sat_path_z[0]],
                                       mode='markers', marker=dict(size=8, color='#38bdf8', symbol='diamond'), name='Satellite', showlegend=False))

            fig = go.Figure(data=traces)

            # Create frames to animate surface wobble, rings and flares, and move satellite with trailing path
            frames = []
            for f in range(num_frames):
                phase = 2 * math.pi * f / num_frames
                # surface intensity with a low-frequency modulation
                intensity = np.sin(6 * (theta + 0.08 * phase)) * np.cos(3 * (phi + 0.05 * phase))
                intensity = intensity + (rng.rand(*theta.shape) - 0.5) * 0.08

                frame_data = []
                # surface update
                frame_data.append(go.Surface(x=x, y=y, z=z, surfacecolor=intensity))

                # rings update: small breathing + rotation
                for i in range(n_rings):
                    t = np.linspace(0, 2 * np.pi, 120)
                    breathing = 0.01 * math.sin(phase * (1 + 0.3 * i))
                    radius = ring_base_radii[i] + breathing
                    xr = radius * np.cos(t + phase * (0.2 + 0.05 * i))
                    yr = radius * np.sin(t + phase * (0.2 + 0.05 * i))
                    zr = 0.03 * np.sin(3 * (t + phase))
                    frame_data.append(go.Scatter3d(x=xr, y=yr, z=zr, mode='lines',
                                                   line=dict(color=ring_colors[i], width=4), opacity=0.6, showlegend=False))

                # flares update
                for i in range(n_flares):
                    ang = flare_angles[i] + phase * (0.5 + 0.2 * (i % 3))
                    h = flare_heights[i]
                    pts = np.linspace(1.0, 1.0 + h, 30)
                    xf = pts * np.cos(ang)
                    yf = pts * np.sin(ang)
                    zf = np.linspace(-0.35, 0.35, len(pts)) * (0.7 + 0.3 * ((i + f) % 5) / 5)
                    frame_data.append(go.Scatter3d(x=xf, y=yf, z=zf, mode='lines',
                                                   line=dict(color='#ff4757', width=3 + (i % 3)), opacity=0.95, showlegend=False))

                # satellite: path up to this frame and current marker
                path_x = sat_path_x[: f + 1]
                path_y = sat_path_y[: f + 1]
                path_z = sat_path_z[: f + 1]
                frame_data.append(go.Scatter3d(x=path_x, y=path_y, z=path_z, mode='lines',
                                               line=dict(color='#38bdf8', width=3), opacity=0.9, showlegend=False))
                frame_data.append(go.Scatter3d(x=[sat_path_x[f]], y=[sat_path_y[f]], z=[sat_path_z[f]], mode='markers',
                                               marker=dict(size=9, color='#38bdf8', symbol='diamond'), showlegend=False))

                frames.append(go.Frame(data=frame_data, name=str(f)))

            fig.frames = frames

            fig.update_layout(
                scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                           camera=dict(eye=dict(x=2.5, y=2.5, z=1.5))),
                margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', showlegend=False
            )

            if autoplay:
                fig.update_layout(
                    updatemenus=[{
                        'type': 'buttons', 'showactive': False, 'y': 0, 'x': 0.05,
                        'buttons': [{
                            'label': 'Play',
                            'method': 'animate',
                            'args': [None, {"frame": {"duration": speed_ms, "redraw": True}, "fromcurrent": True, "transition": {"duration": 0}}]
                        }]
                    }]
                )

            st.plotly_chart(fig, width='stretch')

        with col_right:
            # Informational side panel with visual indicators
            st.markdown("#### Solar Snapshot")
            st.markdown(f"**Solar Storm Risk:**  {solar['solar_storm_risk']}")
            st.markdown(f"**Estimated impact probability:**  {(solar_score * 100):.0f}%")
            if solar.get('solar_peak_overlap'):
                years = ", ".join(str(y) for y in solar['solar_peak_overlap'])
                st.markdown(f"**Mission overlaps peak years:**  {years}")

            st.markdown("**Visual legend:**")
            st.markdown("<div style='display:flex; gap:0.5rem; align-items:center;'>"
                        "<div style='width:14px; height:14px; background:#ff4757; border-radius:3px;'></div> <div>Flares (energetic)</div>"
                        "</div>", unsafe_allow_html=True)
            st.markdown("<div style='display:flex; gap:0.5rem; align-items:center; margin-top:6px;'>"
                        "<div style='width:14px; height:14px; background:#ffd93d; border-radius:3px;'></div> <div>Energy rings (global activity)</div>"
                        "</div>", unsafe_allow_html=True)
            st.markdown("<div style='display:flex; gap:0.5rem; align-items:center; margin-top:6px;'>"
                        "<div style='width:14px; height:14px; background:#38bdf8; border-radius:3px;'></div> <div>Your satellite (moving)</div>"
                        "</div>", unsafe_allow_html=True)

            st.markdown("**What this means:** Solar storms can disrupt radios, damage electronics, and increase charging. During peaks, strong events are more frequent — consider hardened comms and safe modes around those years.")
            st.markdown("**Try this:** Toggle autoplay or change speed to watch how active regions and flares evolve — the blue diamond is your satellite and the red lines are energetic flares.")

    else:
        # Space Debris: show 3D debris field with in-plot legend markers and a right-side visual legend
        st.markdown("#### Debris Field 3D View")

        col_left_d, col_right_d = st.columns([2, 1])

        with col_left_d:
            num_debris = 140
            radius = 6371 + altitude_km
            debris_data = {'x': [], 'y': [], 'z': [], 'size': [], 'color': []}
            for _ in range(num_debris):
                theta = np.random.random() * 2 * np.pi
                phi = np.random.random() * np.pi
                r = radius * (1 + (np.random.random() - 0.5) * 0.08)
                x = r * np.sin(phi) * np.cos(theta)
                y = r * np.sin(phi) * np.sin(theta)
                z = r * np.cos(phi)
                debris_data['x'].append(x); debris_data['y'].append(y); debris_data['z'].append(z)
                size = np.random.choice([3, 5, 8])
                color = np.random.choice(['#ff6b6b', '#ffd93d', '#4dabf7'])
                debris_data['size'].append(size); debris_data['color'].append(color)

            # Build the 3D figure and then append in-plot legend markers (positioned off to the side)
            fig = plot_orbit_3d(altitude_km, inclination_deg, debris_data)

            # Add representative markers (legend) in the 3D scene to visually indicate size/color mapping
            legend_radius = radius * 1.14
            legend_x = [legend_radius, legend_radius, legend_radius]
            legend_y = [0, legend_radius * 0.08, -legend_radius * 0.08]
            legend_z = [0, legend_radius * 0.04, -legend_radius * 0.04]
            legend_sizes = [10, 6, 3]
            legend_colors = ['#ff6b6b', '#ffd93d', '#4dabf7']
            legend_texts = ['Big junk', 'Medium junk', 'Small bits']

            fig.add_trace(go.Scatter3d(x=[legend_x[0]], y=[legend_y[0]], z=[legend_z[0]], mode='markers+text',
                                       marker=dict(size=legend_sizes[0], color=legend_colors[0]), text=[legend_texts[0]],
                                       textposition='middle right', showlegend=False))
            fig.add_trace(go.Scatter3d(x=[legend_x[1]], y=[legend_y[1]], z=[legend_z[1]], mode='markers+text',
                                       marker=dict(size=legend_sizes[1], color=legend_colors[1]), text=[legend_texts[1]],
                                       textposition='middle right', showlegend=False))
            fig.add_trace(go.Scatter3d(x=[legend_x[2]], y=[legend_y[2]], z=[legend_z[2]], mode='markers+text',
                                       marker=dict(size=legend_sizes[2], color=legend_colors[2]), text=[legend_texts[2]],
                                       textposition='middle right', showlegend=False))

            st.plotly_chart(fig, width='stretch')

        with col_right_d:
            st.markdown("**Legend (visual):**)")
            st.markdown("<div style='display:flex; flex-direction:column; gap:8px;'>"
                        "<div style='display:flex; gap:8px; align-items:center;'><div style='width:18px; height:18px; background:#ff6b6b; border-radius:4px;'></div> <div>Big junk — high impact</div></div>"
                        "<div style='display:flex; gap:8px; align-items:center;'><div style='width:14px; height:14px; background:#ffd93d; border-radius:4px;'></div> <div>Medium junk — moderate</div></div>"
                        "<div style='display:flex; gap:8px; align-items:center;'><div style='width:10px; height:10px; background:#4dabf7; border-radius:4px;'></div> <div>Small bits — nuisance</div></div>"
                        "</div>", unsafe_allow_html=True)

            st.markdown("**Tip:** Rotate the 3D view to see how the satellite path passes through the debris shell. Use the size & color to judge collision severity.")

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

    # Replace pydeck globe with an exterior Plotly 3D view showing the Earth, an animated orbit trail
    # and a moving satellite marker plus the predicted deorbit footprint. Add visual polish (atmosphere, stars)
    try:
        st.markdown("#### Interactive 3D Orbit (exterior view)")

        # Layout: figure left, info right
        col_fig, col_info = st.columns([3, 1])

        with col_fig:
            # Controls
            play_orbit = st.checkbox("Autoplay orbit", value=True, key="orbit_autoplay")
            orbit_speed = st.slider("Orbit animation speed (ms per frame)", 30, 1000, 100, step=10, key="orbit_speed")

            orbit_points = generate_orbit_path(altitude_km, inclination_deg, num_points=360)

            # Convert deorbit lat/lon to xyz
            def latlon_to_xyz(lat_deg, lon_deg, radius_km=6371.0, alt_offset_km=1.0):
                lat = math.radians(lat_deg)
                lon = math.radians(lon_deg)
                R = radius_km + alt_offset_km
                x = R * math.cos(lat) * math.cos(lon)
                y = R * math.cos(lat) * math.sin(lon)
                z = R * math.sin(lat)
                return x, y, z

            d_x, d_y, d_z = latlon_to_xyz(deorbit['predicted_latitude'], deorbit['predicted_longitude'], alt_offset_km=5.0)

            # Earth mesh (km scale)
            R_scene = 6371.0
            phi = np.linspace(0, 2*np.pi, 120)
            theta = np.linspace(-np.pi/2, np.pi/2, 60)
            phi, theta = np.meshgrid(phi, theta)
            xe = R_scene * np.cos(theta) * np.cos(phi)
            ye = R_scene * np.cos(theta) * np.sin(phi)
            ze = R_scene * np.sin(theta)

            # Atmosphere (a slightly larger translucent sphere)
            ae = 1.0125 * R_scene
            xe_a = ae * np.cos(theta) * np.cos(phi)
            ye_a = ae * np.cos(theta) * np.sin(phi)
            ze_a = ae * np.sin(theta)

            # starfield for background
            rng = np.random.RandomState(42)
            n_stars = 200
            star_r = R_scene * 18
            star_theta = rng.rand(n_stars) * np.pi
            star_phi = rng.rand(n_stars) * 2 * np.pi
            stars_x = star_r * np.sin(star_theta) * np.cos(star_phi)
            stars_y = star_r * np.sin(star_theta) * np.sin(star_phi)
            stars_z = star_r * np.cos(star_theta)

            # Orbit arrays
            orbit_x = orbit_points[:, 0]
            orbit_y = orbit_points[:, 1]
            orbit_z = orbit_points[:, 2]

            # Build base traces
            traces = []
            # stars (behind everything)
            traces.append(go.Scatter3d(x=stars_x, y=stars_y, z=stars_z, mode='markers', marker=dict(size=1.5, color='white', opacity=0.8), showlegend=False))
            # earth surface: try to map a NASA Blue Marble texture at runtime; fallback to colorscale if unavailable
            surface_mapped = False
            texture_url = 'https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57730/land_ocean_ice_2048.jpg'
            if Image is not None:
                try:
                    resp = requests.get(texture_url, timeout=6)
                    img = Image.open(BytesIO(resp.content)).convert('RGB')
                    # Resize image to mesh shape (theta rows x phi cols)
                    h, w = xe.shape
                    img = img.resize((w, h), Image.LANCZOS)
                    arr = np.array(img)
                    # Build surfacecolor as 2D array of 'rgb(r,g,b)'
                    surfacecolor = []
                    for row in arr:
                        surfacecolor.append([f'rgb({r},{g},{b})' for r, g, b in row])

                    traces.append(go.Surface(x=xe, y=ye, z=ze, surfacecolor=surfacecolor,
                                             showscale=False, opacity=1.0,
                                             lighting=dict(ambient=0.6, diffuse=0.6, specular=0.3, roughness=0.8, fresnel=0.2),
                                             lightposition=dict(x=10000, y=10000, z=20000)))
                    surface_mapped = True
                except Exception:
                    surface_mapped = False

            if not surface_mapped:
                traces.append(go.Surface(x=xe, y=ye, z=ze, colorscale='Earth', showscale=False, opacity=1.0))

            # atmosphere glow
            traces.append(go.Surface(x=xe_a, y=ye_a, z=ze_a, colorscale=[[0, 'rgba(135,206,250,0.02)'], [1, 'rgba(135,206,250,0.02)']], showscale=False, opacity=0.18))
            # orbit path (strong line + faint glow behind it)
            traces.append(go.Scatter3d(x=orbit_x, y=orbit_y, z=orbit_z, mode='lines', line=dict(color='#60a5fa', width=4), opacity=0.95, name='Orbit'))
            traces.append(go.Scatter3d(x=orbit_x, y=orbit_y, z=orbit_z, mode='lines', line=dict(color='#60a5fa', width=18), opacity=0.08, name='OrbitGlow'))
            # satellite marker and trail placeholders
            traces.append(go.Scatter3d(x=[orbit_x[0]], y=[orbit_y[0]], z=[orbit_z[0]], mode='markers', marker=dict(size=7, color='#38bdf8'), name='Satellite'))
            traces.append(go.Scatter3d(x=[orbit_x[0]], y=[orbit_y[0]], z=[orbit_z[0]], mode='markers', marker=dict(size=3, color='#60a5fa', opacity=0.9), name='Trail'))
            # deorbit marker
            traces.append(go.Scatter3d(x=[d_x], y=[d_y], z=[d_z], mode='markers+text', text=['Deorbit'], marker=dict(size=9, color='#ef4444'), textposition='top center', name='Deorbit'))

            fig_orbit = go.Figure(data=traces)

            # Prepare frames; sample to ~120 frames max
            n_pts = len(orbit_x)
            max_frames = 120
            step = max(1, n_pts // max_frames)
            indices = list(range(0, n_pts, step))
            if indices[-1] != n_pts - 1:
                indices.append(n_pts - 1)

            frames = []
            trail_len = 32
            for idx in indices:
                sat_x = orbit_x[idx]
                sat_y = orbit_y[idx]
                sat_z = orbit_z[idx]

                # build fading trail colors for last trail_len points
                start = max(0, idx - trail_len + 1)
                trail_x = orbit_x[start: idx + 1]
                trail_y = orbit_y[start: idx + 1]
                trail_z = orbit_z[start: idx + 1]
                n_trail = len(trail_x)
                colors = []
                for k in range(n_trail):
                    alpha = (k + 1) / n_trail
                    # ensure valid rgba string (close the parenthesis)
                    colors.append(f'rgba(56,189,248,{alpha:.2f})')

                # frame traces: keep static elements minimal by repeating essential visuals
                frame_traces = [
                    go.Surface(x=xe, y=ye, z=ze, showscale=False),
                    go.Surface(x=xe_a, y=ye_a, z=ze_a, showscale=False, opacity=0.18),
                    # orbit visible line + glow
                    go.Scatter3d(x=orbit_x, y=orbit_y, z=orbit_z, mode='lines', line=dict(color='#60a5fa', width=4), opacity=0.95),
                    go.Scatter3d(x=orbit_x, y=orbit_y, z=orbit_z, mode='lines', line=dict(color='#60a5fa', width=18), opacity=0.08),
                    # satellite marker
                    go.Scatter3d(x=[sat_x], y=[sat_y], z=[sat_z], mode='markers', marker=dict(size=7, color='#38bdf8')),
                    # trail as markers with per-point rgba (fallback if client supports)
                    go.Scatter3d(x=trail_x, y=trail_y, z=trail_z, mode='markers', marker=dict(size=3, color=colors)),
                    # deorbit marker
                    go.Scatter3d(x=[d_x], y=[d_y], z=[d_z], mode='markers+text', text=['Deorbit'], marker=dict(size=9, color='#ef4444'), textposition='top center')
                ]

                frames.append(go.Frame(data=frame_traces, name=str(idx)))

            fig_orbit.frames = frames

            # Zoom camera in for a larger, more immersive globe and set aspect ratio
            fig_orbit.update_layout(
                scene=dict(aspectmode='data',
                           xaxis=dict(showbackground=False, visible=False),
                           yaxis=dict(showbackground=False, visible=False),
                           zaxis=dict(showbackground=False, visible=False),
                           aspectratio=dict(x=1, y=1, z=0.62),
                           camera=dict(eye=dict(x=1.6 * R_scene, y=0.9 * R_scene, z=0.7 * R_scene))),
                margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)', showlegend=False
            )

            if play_orbit:
                fig_orbit.update_layout(
                    updatemenus=[{
                        'type': 'buttons', 'showactive': False, 'y': 0.05, 'x': 0.05,
                        'buttons': [{
                            'label': 'Play Orbit',
                            'method': 'animate',
                            'args': [None, {"frame": {"duration": orbit_speed, "redraw": True}, "fromcurrent": True, "transition": {"duration": 0}}]
                        }]
                    }]
                )

            st.plotly_chart(fig_orbit, width='stretch')

        with col_info:
            # Orbital metrics and interactive scrubber
            st.markdown("#### Orbit Details")
            # orbital period (circular approx)
            mu = 398600.4418  # Earth's GM, km^3/s^2
            a = (6371.0 + altitude_km)
            period_s = 2 * math.pi * math.sqrt((a ** 3) / mu)
            period_min = period_s / 60.0
            st.markdown(f"**Altitude:** {altitude_km} km")
            st.markdown(f"**Inclination:** {inclination_deg}°")
            st.markdown(f"**Orbital period:** {period_min:.1f} min")

            # scrubber to inspect a frame
            frame_idx = st.slider("Inspect frame", 0, max(0, len(indices) - 1), 0)
            sel_idx = indices[frame_idx]
            sx, sy, sz = orbit_x[sel_idx], orbit_y[sel_idx], orbit_z[sel_idx]
            # convert to lat/lon/alt
            r_sat = math.sqrt(sx*sx + sy*sy + sz*sz)
            lat = math.degrees(math.asin(sz / r_sat))
            lon = math.degrees(math.atan2(sy, sx))
            alt_km = r_sat - 6371.0
            st.markdown(f"**Frame:** {sel_idx} / {n_pts}")
            st.markdown(f"**Latitude:** {lat:.2f}°")
            st.markdown(f"**Longitude:** {lon:.2f}°")
            st.markdown(f"**Instant altitude:** {alt_km:.1f} km")

            st.markdown("---")
            st.markdown("**Deorbit prediction**")
            st.markdown(f"Lat: {deorbit['predicted_latitude']}°, Lon: {deorbit['predicted_longitude']}°, Year: {deorbit['predicted_deorbit_year']}")

    except Exception as e:
        st.error(f"3D orbit visualization failed: {e}")
        st.info("Plotly 3D visualization requires a modern browser. If problems persist, check your environment.")

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
    st.markdown(
        """
        <div class="rocket-launch">
            <div class="rocket-emoji">🚀</div>
            <div class="rocket-trail"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

