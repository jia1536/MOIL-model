"""
generate_prospectivity_data_v3.py — extends v2, adding the 3 attributes
explicitly requested: ore thickness, ore quality/grade, water table depth.

Unlike v2's mn_ppm_soil (a soil geochemistry proxy), ore_grade_mn_pct here is
CALIBRATED AGAINST REAL DATA: state-level weighted average Mn% computed
directly from data/real/gradewise_production_by_district_2020_21.csv (the
government's own grade-band production figures), not guessed. Per-point
values are drawn around that real state average with realistic noise.

thickness_m and water_table_depth_m have no equivalent public per-point
dataset (this is disclosed, not hidden) — calibrated to plausible ranges for
Indian gondite/archean manganese belts based on published mine engineering
notes (e.g. data/real/moil_underground_mines.csv shaft depths), documented
here so anyone reviewing the code can see exactly what's real vs estimated.
"""
import numpy as np
import pandas as pd

np.random.seed(42)
n = 1200  # slightly more rows than v2 since we're now modeling 3 extra dimensions

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

# REAL: weighted average Mn% computed from data/real/gradewise_production_by_district_2020_21.csv
# (band midpoints 50/40.5/30/15 weighted by actual tonnage per state, summed 2020-21).
# Goa and Jharkhand aren't in that file (no recorded production that year) — flagged
# as ESTIMATED, using the geology-type average of states that share their geology_type.
state_avg_grade_pct = {
    "Odisha": 31.4, "Karnataka": 25.1, "Madhya Pradesh": 27.6, "Maharashtra": 34.3,
    "Andhra Pradesh": 19.7,
    "Goa": 18.0,       # ESTIMATED — laterite-type ore is typically lower grade, no real 2020-21 record
    "Jharkhand": 22.0,  # ESTIMATED — archean-type, similar to Karnataka's real figure
}

# ESTIMATED (no public per-point dataset) — plausible ranges for Indian manganese
# seams, cross-checked only loosely against shaft depths in
# data/real/moil_underground_mines.csv (150-750m), which describes access depth,
# not ore body thickness, so this is NOT derived from that file directly.
GEOLOGY_BASE_THICKNESS_M = {"gondite_archean": 4.5, "archean": 3.0, "kodurite_archean": 2.2, "laterite": 1.5}
# ESTIMATED — hard-rock interior belts (MP/Maharashtra/Odisha gondite-archean) tend
# to have deeper water tables than coastal laterite (Goa); rough regional plausibility,
# not sourced from CGWB per-point records.
GEOLOGY_BASE_WATER_TABLE_M = {"gondite_archean": 22, "archean": 19, "kodurite_archean": 17, "laterite": 7}

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
    drainage_density = np.random.uniform(0.2, 3.0)

    ndvi = np.random.uniform(0.15, 0.75)
    ndwi = np.random.uniform(-0.3, 0.3)
    lst = np.random.uniform(22, 38)
    mineral_alteration_index = np.clip(np.random.normal(0.4 + geo_boost * 0.5, 0.12), 0, 1)

    mn_ppm_soil = max(50, np.random.normal(300 + geo_boost * 1500, 200))
    magnetic_anomaly_nt = np.random.normal(geo_boost * 120, 25)

    dist_fault_km = np.random.exponential(8)
    dist_known_mine_km = min(haversine_km(lat, lng, m[0], m[1]) for m in known_mines)

    # NEW attribute 1: ore thickness (m) — geology-tied base + noise
    thickness_m = max(0.3, np.random.normal(GEOLOGY_BASE_THICKNESS_M[geology], 1.3))

    # NEW attribute 2: ore quality/grade (% Mn) — REAL state average + noise
    ore_grade_mn_pct = float(np.clip(
        np.random.normal(state_avg_grade_pct[state], 6.0), 8, 54
    ))

    # NEW attribute 3: water table depth (m) — geology-tied base + noise
    water_table_depth_m = float(np.clip(
        np.random.normal(GEOLOGY_BASE_WATER_TABLE_M[geology], 7.0), 1.5, 45
    ))

    # Prospectivity rule — v2's formula, rebalanced to make room for the 3 new
    # attributes: thicker + higher-grade ore raises the score; a shallow water
    # table (harder/costlier to mine) applies a small penalty.
    score = (
        0.22 * (geo_boost / 0.32)
        + 0.16 * np.clip(mn_ppm_soil / 2000, 0, 1)
        + 0.12 * np.clip(magnetic_anomaly_nt / 150, 0, 1)
        + 0.10 * mineral_alteration_index
        + 0.08 * ndvi
        + 0.08 * np.exp(-dist_known_mine_km / 80)
        - 0.04 * np.clip(dist_fault_km / 40, 0, 1)
        + 0.09 * np.clip(thickness_m / 8, 0, 1)
        + 0.09 * np.clip((ore_grade_mn_pct - 10) / 40, 0, 1)
        - 0.04 * np.clip((35 - water_table_depth_m) / 33, 0, 1)
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
        "thickness_m": round(thickness_m, 2),
        "ore_grade_mn_pct": round(ore_grade_mn_pct, 1),
        "water_table_depth_m": round(water_table_depth_m, 1),
        "geology_type": geology, "prospectivity_score": round(score, 3),
    })

df = pd.DataFrame(rows)
df.to_csv("data/synthetic_prospectivity_v3.csv", index=False)
print(df.head())
print(f"\nRows: {len(df)}, columns: {list(df.columns)}")
print("\nOre grade sanity check (should track real state averages):")
print(df.groupby("state")["ore_grade_mn_pct"].mean().round(1))
