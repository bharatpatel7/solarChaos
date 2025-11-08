## 📘 README: Satellite Lifecycle & Space Risk Forecaster

### 🚀 Overview
This project is a Streamlit-powered dashboard that predicts the lifecycle and risk profile of satellites based on launch parameters. It estimates:
- Satellite age and end-of-life
- Predicted deorbit location
- Solar storm risk during mission
- Space debris collision probability

It’s designed to help researchers, engineers, and space enthusiasts assess mission viability and environmental threats in orbit.

---

### 🧠 Features
- 📆 **Mission Timeline**: Calculates satellite age and estimated end-of-life based on orbital altitude.
- 🌍 **Deorbit Location Predictor**: Simulates where the satellite will re-enter Earth's atmosphere.
- 🌞 **Solar Storm Risk Forecaster**: Flags mission years that overlap with solar cycle peaks.
- 🗑️ **Debris Collision Analyzer**: Assesses collision risk based on altitude, inclination, and mission duration.

---

### 🛠️ Technologies Used
- Python 3
- Streamlit
- datetime, random, math (standard libraries)

---

### 📁 Project Structure
```
solarChaos/
├── Dashboard.py              # Main Streamlit app
├── satellite_modules.py      # Core logic functions
└── requirements.txt          # Python dependencies (optional for deployment)
```

---

### ▶️ How to Run Locally

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-username/solarChaos.git
   cd solarChaos
   ```

2. **Create a virtual environment**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**  
   ```bash
   pip install streamlit
   ```

4. **Run the app**  
   ```bash
   streamlit run Dashboard.py
   ```

---

### 🌐 Deployment
You can deploy this app for free using [Streamlit Cloud](https://streamlit.io/cloud). Just upload your files and include a `requirements.txt` like:

```
streamlit
```

---

### 📌 Future Enhancements
- Integrate real satellite data from CelesTrak or Space-Track
- Add orbital visualizations using CesiumJS or Folium
- Include real-time solar activity from NOAA SWPC
- Expand debris modeling with NASA ORDEM data

---

### 👨‍💻 Author
**Bharat Garsondiya**  
**Jayen Patel**  
**Laksh Patel**  
**Gurprit Singh**  
Passionate about space, data, and predictive modeling.

---
