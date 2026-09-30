# AquaGuard AI – Intelligent Watershed Priority Mapping & Water Conservation Decision Support System

AquaGuard AI is a full-stack Decision Support System (DSS) developed for hydrological planning, drought-proofing, and watershed engineering. It calculates water stress scores across micro-watersheds using multi-criteria hydrological parameters, simulates climate risks, and prescribes explainable engineering interventions with projected aquifer recharge gains.

---

## 🚀 Key Features

1. **Interactive Leaflet GIS Mapping**:
   - Focuses on Indian micro-watersheds with polygon boundaries, geo-referenced centroids, and color-coded priority alerts.
   - Powered by free OpenStreetMap tiles — zero external paid APIs, Mapbox, or Google keys required. Operates offline.

2. **Hydrological Water Stress Scoring Engine (1.0 – 10.0)**:
   - Formally integrates seven weighted hydrological indicators:
     - **Rainfall Deficit (25%)**
     - **Vegetation Vigor / NDVI (20%)**
     - **Relief & Slope (15%)**
     - **Soil Vulnerability / Permeability (15%)**
     - **Drainage Density (10%)**
     - **Surface Water Storage Deficit (10%)**
     - **Land Use Class (5%)**

3. **Explainable AI / "Explain Score" Modal**:
   - Shows the exact mathematical formula, normalized parameter metrics, and interactive Chart.js doughnut chart breaking down individual parameter contribution percentages.

4. **Dynamic Water Risk Climate Simulator**:
   - Allows users to simulate real-time climate shocks (e.g. -20% rainfall deficit, -15% NDVI drought reduction) and instantly recalculates ranked priorities across all watersheds.

5. **Intervention Impact Simulator**:
   - Users can toggle structural conservation interventions:
     - *Check Dam Network*
     - *Percolation Pond System*
     - *Decentralized Farm Ponds*
     - *Contour Trenching & Bunding*
     - *Community Rainwater Harvesting (RWH)*
   - Dynamically calculates **Predicted Future Score**, **% Risk Reduction**, and **Estimated Aquifer Recharge Gain (Million Cubic Meters - MCM)**.

6. **Instant Export Engine**:
   - **Download PDF Diagnostic**: Executive diagnostic report featuring watershed attributes, formula calculation breakdown, intervention impact, and priority tiers using ReportLab.
   - **Download CSV Rankings**: Full tabular export of all 22 micro-watersheds with priority rankings and contribution percentages.

7. **National Hackathon Ready UI**:
   - Modern dark-theme glassmorphism interface with real-time responsive cards, no placeholder buttons, and complete functional sample datasets.

---

## 📁 Project Structure

```
aquaguard_ai/
├── app.py                     # Flask web server and REST API controllers
├── scoring_engine.py          # Hydrological formulas, normalization, recommendations & simulation
├── reports.py                 # PDF generation (ReportLab) and CSV exporter
├── requirements.txt           # Python library dependencies
├── README.md                  # Complete documentation and user guide
├── data/
│   └── watersheds.json        # 22 realistic Indian micro-watershed GeoJSON profiles
├── static/
│   ├── css/
│   │   └── style.css          # Dark-theme glassmorphism styling
│   └── js/
│       └── main.js            # Leaflet GIS, Chart.js, and client simulation controller
└── templates/
    └── index.html             # Tri-pane responsive dashboard and explainability modal
```

---

## 🛠️ Installation & Quickstart

### Prerequisites
- Python 3.9+ (Python 3.11 recommended)
- `pip` package manager

### 1. Clone or Navigate to Directory
```bash
cd aquaguard_ai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the Dashboard
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📐 Scoring Formula & Logic

The composite Water Stress Score is calculated on a 1.0 to 10.0 scale:

$$\text{Score} = \sum_{i=1}^{n} (\text{Normalized\_Value}_i \times \text{Weight}_i)$$

$$\begin{aligned}
\text{Score} = & (\text{Rainfall}_{\text{norm}} \times 0.25) + (\text{NDVI}_{\text{norm}} \times 0.20) + (\text{Slope}_{\text{norm}} \times 0.15) \\
& + (\text{Soil}_{\text{norm}} \times 0.15) + (\text{DrainageDensity}_{\text{norm}} \times 0.10) \\
& + (\text{SurfaceWater}_{\text{norm}} \times 0.10) + (\text{LandUse}_{\text{norm}} \times 0.05)
\end{aligned}$$

### Priority Tiers
- **Critical Priority (Red)**: $\ge 7.5$
- **High Priority (Orange)**: $5.5 - 7.4$
- **Medium Priority (Yellow)**: $4.0 - 5.4$
- **Low Priority (Green)**: $1.0 - 3.9$
