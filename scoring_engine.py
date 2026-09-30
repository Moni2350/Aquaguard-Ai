"""
scoring_engine.py
=================
AquaGuard AI - Intelligent Watershed Scoring and Recommendation Engine
Calculates Water Stress Score (1.0 to 10.0), parameter contribution breakdown,
priority classification, and evidence-based conservation recommendations.
"""

# Weights for scoring calculation (Sum = 1.0)
WEIGHTS = {
    'rainfall': 0.25,        # 25% - Deficit in rainfall drives fundamental scarcity
    'ndvi': 0.20,            # 20% - Low vegetative vigor reflects drought & ground stress
    'slope': 0.15,           # 15% - Steeper slope causes higher surface runoff velocity
    'soil': 0.15,            # 15% - Poor retention / rocky soils exacerbate runoff
    'drainage_density': 0.10,# 10% - High drainage density accelerates runoff escape
    'surface_water': 0.10,   # 10% - Low surface water storage indicates severe storage deficit
    'land_use': 0.05         # 5%  - Degradation / fallow / barren lands increase vulnerability
}

SOIL_VULNERABILITY_MAP = {
    'coarse aeolian sand': 9.5,
    'desert sand & calcareous': 9.2,
    'red rocky gravelly': 8.8,
    'deep alluvial loess': 8.2,
    'red sandy soils': 8.0,
    'black sandy loam': 7.5,
    'red and yellow soils': 7.0,
    'red sandy chalkas': 6.8,
    'laterite loam & coastal alluvium': 5.8,
    'medium black basaltic': 5.5,
    'lateritic red soil': 5.2,
    'deep black clay': 4.8,
    'mixed red & black loam': 4.5,
    'black loamy trap': 4.2,
    'piedmont sandy alluvium': 5.0,
    'glacio-fluvial skeletal stony': 6.5,
    'red sandy clay ferruginous': 4.0,
    'red sandy clayey loam': 3.8,
    'acidic red loam': 3.2,
    'tarai silt alluvium': 2.5,
    'deltaic alluvial clay': 2.0,
    'laterite humus rich': 1.8
}

LAND_USE_VULNERABILITY_MAP = {
    'hyper-arid desert & sparse shrub': 9.5,
    'semi-arid sand dunes & millets': 9.0,
    'severe gully erosion badlands': 9.2,
    'scrubland & degraded farmland': 8.5,
    'arid agriculture & fallow': 8.2,
    'rainfed agriculture & wasteland': 7.8,
    'pastureland & fodder farming': 6.5,
    'groundnut/cotton dryland': 6.2,
    'cotton/soybean cropland': 5.8,
    'mono-cropped agriculture & scrub': 5.5,
    'intensive borewell horticultural': 6.0,
    'choe torrent gullies & orchards': 5.2,
    'chilli & cotton irrigated belt': 4.2,
    'paddy, maize & urban outskirts': 4.0,
    'alpine conifer & terraced slopes': 3.5,
    'mango/cashew orchards & evergreen': 2.8,
    'deciduous forest & terraced paddy': 2.5,
    'triple crop rice agro-ecosystem': 2.0,
    'sal forest, tea gardens & beels': 1.8,
    'sugarcane & wetland marsh': 1.5,
    'dense sal forest & minor millets': 1.6,
    'coffee plantation & wet evergreen forest': 1.2
}


def normalize_rainfall(rainfall_mm):
    """
    Lower rainfall -> Higher Stress (Range: 200mm - 3200mm).
    Normalized to 1 - 10 scale.
    """
    val = max(200.0, min(float(rainfall_mm), 3200.0))
    # Inverted: 200mm -> 10.0 (extreme stress), 3200mm -> 1.0 (very low stress)
    norm = 10.0 - ((val - 200.0) / (3200.0 - 200.0)) * 9.0
    return round(norm, 2)


def normalize_ndvi(ndvi):
    """
    Lower NDVI -> Higher Stress (Range: 0.05 - 0.90).
    Normalized to 1 - 10 scale.
    """
    val = max(0.05, min(float(ndvi), 0.90))
    # Inverted: 0.05 -> 10.0 (barren/stress), 0.90 -> 1.0 (dense canopy)
    norm = 10.0 - ((val - 0.05) / (0.90 - 0.05)) * 9.0
    return round(norm, 2)


def normalize_slope(slope_deg):
    """
    Higher Slope -> Higher Runoff / Stress (Range: 1.0 deg - 30.0 deg).
    Normalized to 1 - 10 scale.
    """
    val = max(1.0, min(float(slope_deg), 30.0))
    norm = 1.0 + ((val - 1.0) / (30.0 - 1.0)) * 9.0
    return round(norm, 2)


def normalize_soil(soil_type):
    """
    Looks up soil vulnerability (1.0 to 10.0). Defaults to 5.0 if not listed.
    """
    key = str(soil_type).strip().lower()
    for pattern, score in SOIL_VULNERABILITY_MAP.items():
        if pattern in key or key in pattern:
            return score
    return 5.5


def normalize_drainage_density(dd_val):
    """
    Higher Drainage Density -> Rapid runoff loss -> Higher Stress (Range: 0.4 - 4.5 km/km2).
    Normalized to 1 - 10 scale.
    """
    val = max(0.4, min(float(dd_val), 4.5))
    norm = 1.0 + ((val - 0.4) / (4.5 - 0.4)) * 9.0
    return round(norm, 2)


def normalize_surface_water(sw_pct):
    """
    Lower Surface Water Storage -> Higher Stress (Range: 0.1% - 10.0%).
    Normalized to 1 - 10 scale.
    """
    val = max(0.1, min(float(sw_pct), 10.0))
    norm = 10.0 - ((val - 0.1) / (10.0 - 0.1)) * 9.0
    return round(norm, 2)


def normalize_land_use(land_use):
    """
    Looks up Land Use vulnerability (1.0 to 10.0).
    """
    key = str(land_use).strip().lower()
    for pattern, score in LAND_USE_VULNERABILITY_MAP.items():
        if pattern in key or key in pattern:
            return score
    return 5.0


def calculate_water_stress(watershed, custom_overrides=None):
    """
    Calculates the composite water stress score (1.0 - 10.0)
    using the formal weighted formula:
    
    Score = sum(Normalized_Parameter_i * Weight_i)
    
    Returns a comprehensive dict with raw, normalized, weighted, percentage contributions,
    and priority level.
    """
    data = dict(watershed)
    if custom_overrides:
        data.update(custom_overrides)

    # 1. Normalization
    n_rain = normalize_rainfall(data.get('rainfall_mm', 800))
    n_ndvi = normalize_ndvi(data.get('ndvi', 0.4))
    n_slope = normalize_slope(data.get('slope_deg', 5.0))
    n_soil = normalize_soil(data.get('soil_type', ''))
    n_dd = normalize_drainage_density(data.get('drainage_density_km_per_sq_km', 2.0))
    n_sw = normalize_surface_water(data.get('surface_water_pct', 3.0))
    n_lu = normalize_land_use(data.get('land_use', ''))

    # 2. Weighted components
    w_rain = n_rain * WEIGHTS['rainfall']
    w_ndvi = n_ndvi * WEIGHTS['ndvi']
    w_slope = n_slope * WEIGHTS['slope']
    w_soil = n_soil * WEIGHTS['soil']
    w_dd = n_dd * WEIGHTS['drainage_density']
    w_sw = n_sw * WEIGHTS['surface_water']
    w_lu = n_lu * WEIGHTS['land_use']

    composite_score = round(w_rain + w_ndvi + w_slope + w_soil + w_dd + w_sw + w_lu, 2)
    composite_score = max(1.0, min(composite_score, 10.0))

    # 3. Parameter-wise contribution percentages to the final score
    total_val = composite_score if composite_score > 0 else 1.0
    contributions = {
        'rainfall': round((w_rain / total_val) * 100, 1),
        'ndvi': round((w_ndvi / total_val) * 100, 1),
        'slope': round((w_slope / total_val) * 100, 1),
        'soil': round((w_soil / total_val) * 100, 1),
        'drainage_density': round((w_dd / total_val) * 100, 1),
        'surface_water': round((w_sw / total_val) * 100, 1),
        'land_use': round((w_lu / total_val) * 100, 1)
    }

    # 4. Priority tier assignment
    if composite_score >= 7.5:
        priority = "Critical Priority"
        priority_level = 1
        badge_color = "#ef4444"  # Red
    elif composite_score >= 5.5:
        priority = "High Priority"
        priority_level = 2
        badge_color = "#f97316"  # Orange
    elif composite_score >= 4.0:
        priority = "Medium Priority"
        priority_level = 3
        badge_color = "#eab308"  # Yellow
    else:
        priority = "Low Priority"
        priority_level = 4
        badge_color = "#10b981"  # Emerald Green

    return {
        'composite_score': composite_score,
        'priority': priority,
        'priority_level': priority_level,
        'badge_color': badge_color,
        'weights': WEIGHTS,
        'normalized': {
            'rainfall': n_rain,
            'ndvi': n_ndvi,
            'slope': n_slope,
            'soil': n_soil,
            'drainage_density': n_dd,
            'surface_water': n_sw,
            'land_use': n_lu
        },
        'weighted_values': {
            'rainfall': round(w_rain, 3),
            'ndvi': round(w_ndvi, 3),
            'slope': round(w_slope, 3),
            'soil': round(w_soil, 3),
            'drainage_density': round(w_dd, 3),
            'surface_water': round(w_sw, 3),
            'land_use': round(w_lu, 3)
        },
        'contributions_pct': contributions,
        'formula_text': "Score = (Rain_norm × 0.25) + (NDVI_norm × 0.20) + (Slope_norm × 0.15) + (Soil_norm × 0.15) + (DD_norm × 0.10) + (SW_norm × 0.10) + (LU_norm × 0.05)"
    }


def generate_recommendations(watershed, score_data):
    """
    Explainable recommendation engine for watershed engineering interventions.
    Evaluates hydro-geological conditions (slope, soil, rainfall, drainage) to prescribe
    tailored interventions with estimated recharge impact and rationale.
    """
    recs = []
    slope = float(watershed.get('slope_deg', 5.0))
    rain = float(watershed.get('rainfall_mm', 800))
    soil = str(watershed.get('soil_type', '')).lower()
    dd = float(watershed.get('drainage_density_km_per_sq_km', 2.0))
    area = float(watershed.get('area_sq_km', 150))
    sw = float(watershed.get('surface_water_pct', 2.0))
    score = score_data['composite_score']

    # 1. Check Dams
    if dd >= 1.5 and slope <= 15.0:
        count = max(4, int(area / 18))
        recs.append({
            'name': 'Check Dam Network',
            'type': 'Check Dam',
            'icon': 'fa-water',
            'units': f"{count} masonry/gabion structures",
            'suitability': 'Highly Suitable',
            'rationale': f"Moderate-to-steep drainage channels (DD: {dd} km/km²) are ideal for slowing storm surge velocity and arresting silt transport.",
            'est_recharge_gain_mcm': round(count * 0.14, 2),
            'impact_score_reduction': 1.15
        })

    # 2. Percolation Ponds
    if ('sandy' in soil or 'red' in soil or 'gravel' in soil or 'alluv' in soil) and slope <= 8.0:
        count = max(3, int(area / 25))
        recs.append({
            'name': 'Percolation Pond System',
            'type': 'Percolation Pond',
            'icon': 'fa-circle-notch',
            'units': f"{count} engineered recharge ponds",
            'suitability': 'Optimal Hydro-geology',
            'rationale': f"Permeable soil texture ({watershed.get('soil_type')}) and flat/gentle terrain (slope {slope}°) maximize gravitational aquifer infiltration.",
            'est_recharge_gain_mcm': round(count * 0.22, 2),
            'impact_score_reduction': 1.30
        })

    # 3. Farm Ponds
    if sw < 4.0 and rain >= 350:
        count = max(8, int(area / 8))
        recs.append({
            'name': 'Decentralized Farm Ponds',
            'type': 'Farm Pond',
            'icon': 'fa-seedling',
            'units': f"{count} on-farm harvesting ponds",
            'suitability': 'High Priority',
            'rationale': f"Critically low surface storage ({sw}%) threatens agrarian resilience during dry spells. Farm ponds provide immediate localized protective irrigation.",
            'est_recharge_gain_mcm': round(count * 0.05, 2),
            'impact_score_reduction': 0.95
        })

    # 4. Continuous Contour Trenches (CCT) & Staggered Trenches
    if slope >= 5.0:
        length_km = round(area * 1.8, 1)
        recs.append({
            'name': 'Contour Trenching & Bunding',
            'type': 'Contour Trench',
            'icon': 'fa-mountain',
            'units': f"{length_km} km ridge-to-valley trenches",
            'suitability': 'Slope Mitigation Essential',
            'rationale': f"Steep relief ({slope}°) causes severe sheet erosion and moisture loss. Trenches intercept overland flow and replenish soil moisture profile.",
            'est_recharge_gain_mcm': round(length_km * 0.015, 2),
            'impact_score_reduction': 1.05
        })

    # 5. Rooftop & Community Rainwater Harvesting (RWH)
    pop = watershed.get('population', 30000)
    structures = max(15, int(pop / 1800))
    recs.append({
        'name': 'Community Rainwater Harvesting (RWH)',
        'type': 'Rainwater Harvesting',
        'icon': 'fa-cloud-rain',
        'units': f"{structures} community/institutional recharge wells",
        'suitability': 'Universal Low-Cost',
        'rationale': f"Direct rainwater harvesting yields pristine recharge for localized shallow aquifers and secures drinking water resilience for population of {pop:,}.",
        'est_recharge_gain_mcm': round(structures * 0.04, 2),
        'impact_score_reduction': 0.70
    })

    # Sort interventions by impact score reduction descending
    recs.sort(key=lambda x: x['impact_score_reduction'], reverse=True)
    return recs


def simulate_interventions(base_score_data, selected_interventions, custom_modifiers=None):
    """
    Intervention Impact Simulator:
    Given selected intervention names, computes:
    - Current Score
    - Predicted Future Score
    - Percentage Risk Reduction
    - Estimated Total Recharge Gain (MCM)
    - Recommended Intervention Combination
    """
    current_score = base_score_data['composite_score']
    
    # Intervention reduction matrix
    impact_catalog = {
        'Check Dam': {'reduction': 1.15, 'recharge_mcm': 0.85},
        'Farm Pond': {'reduction': 0.95, 'recharge_mcm': 0.65},
        'Percolation Pond': {'reduction': 1.30, 'recharge_mcm': 1.20},
        'Rainwater Harvesting': {'reduction': 0.70, 'recharge_mcm': 0.40},
        'Contour Trench': {'reduction': 1.05, 'recharge_mcm': 0.75}
    }

    total_reduction = 0.0
    total_recharge = 0.0
    active_interventions = []

    for name in selected_interventions:
        for k, meta in impact_catalog.items():
            if k.lower() in name.lower():
                # Apply diminishing returns for multiple interventions
                diminish_factor = 0.88 ** len(active_interventions)
                total_reduction += meta['reduction'] * diminish_factor
                total_recharge += meta['recharge_mcm']
                active_interventions.append(k)
                break

    # If climate stress modifier applied
    if custom_modifiers:
        rain_drop = custom_modifiers.get('rainfall_drop_pct', 0)
        # rainfall drop increases stress
        stress_bump = (rain_drop / 100.0) * 1.8
        current_score = min(10.0, current_score + stress_bump)

    predicted_score = max(1.0, round(current_score - total_reduction, 2))
    risk_reduction_pct = round(((current_score - predicted_score) / current_score) * 100, 1) if current_score > 0 else 0.0

    # Priority tier for predicted score
    if predicted_score >= 7.5:
        predicted_priority = "Critical Priority"
        pred_color = "#ef4444"
    elif predicted_score >= 5.5:
        predicted_priority = "High Priority"
        pred_color = "#f97316"
    elif predicted_score >= 4.0:
        predicted_priority = "Medium Priority"
        pred_color = "#eab308"
    else:
        predicted_priority = "Low Priority (Safe/Resilient)"
        pred_color = "#10b981"

    # Strategic combination recommendation
    combo_rec = "Synergistic Ridge-to-Valley Integrated Suite: " + " + ".join(active_interventions if active_interventions else ['Base Monitoring'])

    return {
        'current_score': round(current_score, 2),
        'predicted_score': predicted_score,
        'risk_reduction_pct': risk_reduction_pct,
        'estimated_recharge_gain_mcm': round(total_recharge, 2),
        'predicted_priority': predicted_priority,
        'pred_color': pred_color,
        'active_interventions': active_interventions,
        'recommended_combo': combo_rec
    }
