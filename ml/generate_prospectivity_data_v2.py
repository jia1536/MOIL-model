"""
Synthetic prospectivity training data v2 — expanded to cover 6 of the 8 parameter
categories from the exploration reference sheet:
  1. Geological     -> geology_type, distance_to_fault_km
  2. Remote sensing  -> ndvi, ndwi, land_surface_temp, mineral_alteration_index
  3. Geochemical     -> mn_ppm_soil
  4. Geophysical     -> magnetic_anomaly_nt
  5. Terrain         -> elevation, slope_deg, drainage_density
  6. Ground truth     -> distance_to_known_mine_km (real MOIL mine coords used as anchors)
  (7. Spatial folded into distance_to_fault / distance_to_known_mine)
  (8. Economic/reserve deliberately excluded -- not a prospectivity-classifier input)
"""
import numpy as np
import pandas as pd

np.random.seed(42)
n = 1000

states = ["Odisha", "Karnataka", "Madhya Pradesh", "Maharashtra", "Andhra Pradesh", "Goa", "Jharkhand"]
state_weights = [0.30, 0.22, 0.14, 0.14, 0.08, 0.07, 0.05]

state_bounds = {
    "Odisha":          {"lat": (19.5, 22.5), "lng": (83.5, 87.0)},
    "Karnataka":       {"lat": (12.0, 18.5), "lng": (74.5, 78.5)},
    "Madhya Pradesh":  {"lat": (21.0, 24.5), "lng": (74.0, 82.0)},
    "Maharashtra":     {"lat": (19.0, 21.5), "lng": (78.5, 80.5)},
    "Andhra Pradesh":  {"lat": (17.5, 19.0), "lng": (82.5, 84.5)},
    "Goa":             {"lat": (15.0, 15.8), "lng": (73.8, 74.3)},
    "Jharkhand":       {"lat": (22.0, 24.0), "lng": (85.0, 87.0)},
}
state_geology = {
    "Odisha": "gondite_archean", "Karnataka": "archean", "Madhya Pradesh": "gondite_archean",
    "Maharashtra": "gondite_archean", "Andhra Pradesh": "kodurite_archean", "Goa": "laterite", "Jharkhand": "archean",
}
geology_boost_map = {"gondite_archean": 0.32, "archean": 0.24, "kodurite_archean": 0.14, "laterite": 0.08}

# Real MOIL mine anchors (from data/real/moil_underground_mines.csv) used to compute
# a realistic distance_to_known_mine feature
known_mines = [(21.80, 80.18), (21.17, 79.65), (21.15, 79.09)]  # Balaghat, Bhandara, Nagpur approx

def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlmb = np.radians(lng2 - lng1)
    a = np.sin(dphi/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dlmb/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

rows = []
for _ in range(n):
    state = np.random.choice(states, p=state_weights)
    b = state_bounds[state]
    lat = np.random.uniform(*b["lat"])
    lng = np.random.uniform(*b["lng"])
    geology = state_geology[state]
    geo_boost = geology_boost_map[geology]

    elevation = np.random.uniform(100, 900)
    slope_deg = np.random.uniform(1, 35)
    drainage_density = np.random.uniform(0.2, 3.0)  # km/km^2

    ndvi = np.random.uniform(0.15, 0.75)
    ndwi = np.random.uniform(-0.3, 0.3)
    lst = np.random.uniform(22, 38)
    mineral_alteration_index = np.clip(np.random.normal(0.4 + geo_boost * 0.5, 0.12), 0, 1)

    # geochemical: Mn ppm in soil, higher near high-grade geology (calibrated loosely to real grade bands)
    mn_ppm_soil = np.random.normal(300 + geo_boost * 1500, 200)
    mn_ppm_soil = max(50, mn_ppm_soil)

    # geophysical: manganese ores often show magnetic anomaly (nanotesla deviation from background)
    magnetic_anomaly_nt = np.random.normal(geo_boost * 120, 25)

    dist_fault_km = np.random.exponential(8)
    dist_known_mine_km = min(haversine_km(lat, lng, m[0], m[1]) for m in known_mines)

    # prospectivity rule: geology + geochemistry + geophysics dominate, terrain/remote-sensing moderate, distance decays
    score = (
        0.28 * (geo_boost / 0.32)
        + 0.20 * np.clip(mn_ppm_soil / 2000, 0, 1)
        + 0.15 * np.clip(magnetic_anomaly_nt / 150, 0, 1)
        + 0.12 * mineral_alteration_index
        + 0.10 * ndvi
        + 0.08 * np.exp(-dist_known_mine_km / 80)   # closer to a known mine -> more prospective
        - 0.05 * np.clip(dist_fault_km / 40, 0, 1)   # far from faults -> slightly less prospective
        + np.random.normal(0, 0.06)
    )
    score = float(np.clip(score, 0, 1))

    rows.append({
        "state": state, "lat": round(lat, 4), "lng": round(lng, 4),
        "elevation": round(elevation, 1), "slope_deg": round(slope_deg, 1),
        "drainage_density": round(drainage_density, 2),
        "ndvi": round(ndvi, 3), "ndwi": round(ndwi, 3), "land_surface_temp": round(lst, 1),
        "mineral_alteration_index": round(mineral_alteration_index, 3),
        "mn_ppm_soil": round(mn_ppm_soil, 1), "magnetic_anomaly_nt": round(magnetic_anomaly_nt, 1),
        "distance_to_fault_km": round(dist_fault_km, 2),
        "distance_to_known_mine_km": round(dist_known_mine_km, 2),
        "geology_type": geology, "prospectivity_score": round(score, 3),
    })

df = pd.DataFrame(rows)
df.to_csv("/home/claude/ml/data/synthetic_prospectivity_v2.csv", index=False)
print(df.head())
print(f"\nRows: {len(df)}, columns: {list(df.columns)}")
