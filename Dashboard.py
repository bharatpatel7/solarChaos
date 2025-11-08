import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sgp4.earth_gravity import wgs84
from sgp4.io import twoline2rv

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

            st.plotly_chart(fig, use_container_width=True)

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

            st.plotly_chart(fig, use_container_width=True)

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

    try:
        import pydeck as pdk

        # Convert orbit points to DataFrame for PathLayer
        orbit_points = []
        num_points = 180
        inc = math.radians(inclination_deg)
        
        for i in range(num_points + 1):
            theta = 2 * math.pi * (i / num_points)
            lat = math.degrees(math.asin(math.sin(inc) * math.sin(theta)))
            lon = math.degrees(theta) - 180
            orbit_points.append({"lon": lon, "lat": lat})
            
        orbit_df = pd.DataFrame(orbit_points)
        orbit_df["path"] = [[[row.lon, row.lat]] for _, row in orbit_df.iterrows()]

        # Create orbit path layer
        orbit_layer = pdk.Layer(
            "PathLayer",
            orbit_df,
            get_path="path",
            get_width=20000,
            width_min_pixels=2,
            get_color=[56, 189, 248],
            pickable=True
        )

        # Create deorbit point layer
        deorbit_df = pd.DataFrame({
            "lon": [deorbit["predicted_longitude"]],
            "lat": [deorbit["predicted_latitude"]]
        })
        
        deorbit_layer = pdk.Layer(
            "ScatterplotLayer",
            deorbit_df,
            get_position=["lon", "lat"],
            get_radius=100000,
            get_fill_color=[239, 68, 68],
            pickable=True
        )

        # Set up the view state
        view_state = pdk.ViewState(
            latitude=0,
            longitude=0,
            zoom=1,
            min_zoom=1,
            max_zoom=3,
            pitch=50,
            bearing=0
        )

        # Create and display the deck
        r = pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=[orbit_layer, deorbit_layer]
        )

        st.pydeck_chart(r)

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
