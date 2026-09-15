"""
routes_map.py
--------------
Fully wired to your ACTUAL files (from SIH26009_deliverables.zip):
  - predict.py returns {"prospectivity_score", "confidence", "reserve_min",
    "reserve_max"} and {"forecast_tonnes", "shortfall_pct", "risk_score",
    "risk_level"} (risk_level is "Low"/"Medium"/"High", capitalized) — every
    reference below uses these exact keys, not the guessed "score" from
    earlier drafts.
  - data_loader.py — real mines (mock/mines.json), real production/downtime
    history, real state reserves (data/real/reserves_by_state.csv).
  - geological_lookup.py — deterministic geology features matching your
    generator's exact state_bounds/geology mapping.

Plug into your FastAPI app:
    from routes_map import router as map_router
    app.include_router(map_router, prefix="/api")

Still TODO (no public source found for these — flagged, not faked):
  - Real per-mine rainfall (currently a documented 1200mm default)
  - Real water table depth (still returns an empty /watertable collection
    until you download CGWB/India-WRIS data — see docs/API_KEYS_SETUP.md)
"""

from fastapi import APIRouter
import numpy as np

from predict import predict_prospectivity, predict_forecast
from satellite_extraction import extract_point_features, get_real_terrain, init_earth_engine
from geological_lookup import lookup_geological_features
from viability_index import compute_viability_index
from data_loader import (
    MINES,
    nearest_mine,
    distance_to_nearest_mine_km,
    get_mine_operational_inputs,
    get_state_reserve_and_production,
)

router = APIRouter()

LEVEL_BREAKS = [
    (0.0, 0.2, "very low"),
    (0.2, 0.4, "low"),
    (0.4, 0.6, "medium"),
    (0.6, 0.8, "high"),
    (0.8, 1.01, "very high"),
]

# Fallback baselines for perturbation-based explainability — matches
# geological_lookup.py's fallback constants + a mid-range remote-sensing value.
FEATURE_BASELINES = {
    "elevation": 500.0, "slope_deg": 18.0, "drainage_density": 1.6,
    "ndvi": 0.45, "ndwi": 0.0, "land_surface_temp": 30.0,
    "mineral_alteration_index": 0.4, "mn_ppm_soil": 1000.0,
    "magnetic_anomaly_nt": 76.8, "distance_to_fault_km": 8.0,
    "distance_to_known_mine_km": 50.0,
}


def score_to_level(score: float) -> str:
    for lo, hi, label in LEVEL_BREAKS:
        if lo <= score < hi:
            return label
    return "very low"


def build_full_feature_set(lat, lng, use_real_satellite=True):
    """
    Assembles the exact 14-key dict predict_prospectivity() expects.
    use_real_satellite=False skips the live GEE calls (faster, for the
    precomputed grid job) and uses geological_lookup.py's fallback constants
    for elevation/slope/remote-sensing too — see routes_map.py's /zones
    docstring for why that matters for demo speed.
    """
    geological = lookup_geological_features(lat, lng)

    if use_real_satellite:
        remote_sensing = extract_point_features(lat, lng)
        real_elevation, real_slope = get_real_terrain(lat, lng)
        geological["elevation"] = real_elevation or geological["elevation"]
        geological["slope_deg"] = real_slope or geological["slope_deg"]
    else:
        remote_sensing = {
            "ndvi": FEATURE_BASELINES["ndvi"],
            "ndwi": FEATURE_BASELINES["ndwi"],
            "land_surface_temp": FEATURE_BASELINES["land_surface_temp"],
            "mineral_alteration_index": geological.pop("_mineral_alteration_prior", 0.4),
        }

    geological.pop("_state", None)
    geological.pop("_mineral_alteration_prior", None)

    return {
        "lat": lat,
        "lng": lng,
        **geological,
        **remote_sensing,
        "distance_to_known_mine_km": distance_to_nearest_mine_km(lat, lng),
    }


def explain_by_perturbation(features: dict, n=4):
    """
    Model-agnostic explainability: swap each feature for its baseline value,
    re-run predict_prospectivity(), measure the score's movement. Works as a
    black box against prospectivity_v2.pkl — no SHAP dependency needed.
    """
    baseline_score = predict_prospectivity(features)["prospectivity_score"]

    contributions = []
    for key, baseline_val in FEATURE_BASELINES.items():
        if key not in features:
            continue
        perturbed = dict(features)
        perturbed[key] = baseline_val
        perturbed_score = predict_prospectivity(perturbed)["prospectivity_score"]
        contributions.append({"name": key, "contribution": round(baseline_score - perturbed_score, 4)})

    contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
    return contributions[:n], baseline_score


def score_zone(lat, lng, use_real_satellite=True):
    """One full pipeline pass for a single coordinate: prospectivity ->
    nearest-mine forecast -> viability index. Used by both /zones and the
    single-point prediction path."""
    features = build_full_feature_set(lat, lng, use_real_satellite=use_real_satellite)
    prospectivity = predict_prospectivity(features)
    score = prospectivity["prospectivity_score"]
    top_features, _ = explain_by_perturbation(features)

    mine = nearest_mine(lat, lng)
    op_inputs = get_mine_operational_inputs(mine["id"])
    if op_inputs:
        forecast = predict_forecast(op_inputs["forecast_input"])
        risk_level = forecast["risk_level"]
    else:
        forecast = None
        risk_level = "Medium"  # no production history for this mine (4 of 12 mock mines lack records)

    remaining_reserve, annual_production = get_state_reserve_and_production(mine["state"])

    viability = compute_viability_index(
        prospectivity_score=score,
        shortfall_risk_label=risk_level,
        water_table_depth_m=None,  # wire to CGWB once downloaded
        remaining_reserve_tonnes=remaining_reserve,
        annual_production_tonnes=annual_production,
    )

    return {
        "prospectivity": prospectivity,
        "level": score_to_level(score),
        "top_features": top_features,
        "nearest_mine": mine["name"],
        "forecast": forecast,
        "viability": viability,
    }


@router.get("/predict_point")
def predict_point(lat: float, lng: float):
    """Single-coordinate prediction — the live, full-accuracy path (real
    satellite fetch). Use this for a user-clicked point, not for the whole grid."""
    return score_zone(lat, lng, use_real_satellite=True)


@router.get("/zones")
def get_zones(bbox: str = "78.0,18.0,84.0,25.0", resolution: int = 20):
    """
    NOTE ON DEMO SPEED: use_real_satellite=False below skips live Earth Engine
    calls for the grid (fast, uses geological_lookup.py's calibrated priors
    instead of live NDVI/NDWI/LST/SRTM per cell). For SIH day-of-demo, this
    is the right tradeoff — precompute this once, cache to a file/DB, serve
    the cache. Reserve the real-satellite path (predict_point above) for
    "predict this exact spot the judge just clicked."
    """
    min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    lons = np.linspace(min_lon, max_lon, resolution)
    lats = np.linspace(min_lat, max_lat, resolution)
    cell_w = (max_lon - min_lon) / resolution
    cell_h = (max_lat - min_lat) / resolution

    features_out = []
    for lat in lats:
        for lon in lons:
            result = score_zone(float(lat), float(lon), use_real_satellite=False)
            score = result["prospectivity"]["prospectivity_score"]

            polygon = [
                [lon, lat], [lon + cell_w, lat],
                [lon + cell_w, lat + cell_h], [lon, lat + cell_h], [lon, lat],
            ]
            features_out.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [polygon]},
                "properties": {
                    "score": score,
                    "level": result["level"],
                    "confidence": result["prospectivity"]["confidence"],
                    "reserve_min": result["prospectivity"]["reserve_min"],
                    "reserve_max": result["prospectivity"]["reserve_max"],
                    "top_features": result["top_features"],
                    "viability_index": result["viability"]["viability_index"],
                    "viability_components": result["viability"]["components"],
                },
            })

    return {"type": "FeatureCollection", "features": features_out}


@router.get("/mines")
def get_mines():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [m["lng"], m["lat"]]},
                "properties": {"name": m["name"], "state": m["state"], "status": m["status"], "type": m["type"]},
            }
            for m in MINES
        ],
    }


@router.get("/watertable")
def get_watertable():
    """Placeholder — replace with a real CGWB/India-WRIS GeoJSON download."""
    return {"type": "FeatureCollection", "features": []}
