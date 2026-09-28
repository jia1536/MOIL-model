from fastapi import APIRouter
import numpy as np

from .predict import predict_forecast
from .predict_v3 import predict_prospectivity_v3
from .satellite_extraction import extract_point_features, get_real_terrain, init_earth_engine
from .geological_lookup import lookup_geological_features
from .viability_index import compute_viability_index
from .site_attributes import get_thickness_estimate, get_water_table_estimate, get_social_infra_score, get_grade_estimate
from .grade_lookup import get_grade_for_mine
from .companies_lookup import get_companies_for_mine
from .zone_cache import load_zones_cache, save_zones_cache
from .data_loader import (
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
# Includes the 3 v3 attributes now that they're real model inputs, not just
# reported alongside the score.
FEATURE_BASELINES = {
    "elevation": 500.0, "slope_deg": 18.0, "drainage_density": 1.6,
    "ndvi": 0.45, "ndwi": 0.0, "land_surface_temp": 30.0,
    "mineral_alteration_index": 0.4, "mn_ppm_soil": 1000.0,
    "magnetic_anomaly_nt": 76.8, "distance_to_fault_km": 8.0,
    "distance_to_known_mine_km": 50.0,
    "thickness_m": 3.0, "ore_grade_mn_pct": 25.0, "water_table_depth_m": 18.0,
}


def score_to_level(score: float) -> str:
    for lo, hi, label in LEVEL_BREAKS:
        if lo <= score < hi:
            return label
    return "very low"


def build_full_feature_set(lat, lng, use_real_satellite=True):
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
    baseline_score = predict_prospectivity_v3(features)["prospectivity_score"]

    contributions = []
    for key, baseline_val in FEATURE_BASELINES.items():
        if key not in features:
            continue
        perturbed = dict(features)
        perturbed[key] = baseline_val
        perturbed_score = predict_prospectivity_v3(perturbed)["prospectivity_score"]
        contributions.append({"name": key, "contribution": round(baseline_score - perturbed_score, 4)})

    contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
    return contributions[:n], baseline_score


def score_zone(lat, lng, use_real_satellite=True):
    geo_features = build_full_feature_set(lat, lng, use_real_satellite=use_real_satellite)
    mine = nearest_mine(lat, lng)
    state = mine["state"]  # nearest known mine's state used as the region for grade/social-infra baselines

    # Grade for the MODEL INPUT uses the synthetic-but-real-calibrated
    # per-point estimator (real IBM data is a district-level tonnage
    # breakdown by grade band, not a single per-point Mn% figure, so it
    # can't be fed directly into a point-based model). The REAL district
    # breakdown is still shown separately below as `grade` for context.
    real_grade = get_grade_for_mine(mine["name"])

    thickness = get_thickness_estimate(lat, lng, geo_features["geology_type"])
    water_table = get_water_table_estimate(lat, lng)
    grade_estimate = get_grade_estimate(lat, lng, state)
    social_infra = get_social_infra_score(lat, lng, state)

    # Build the exact 17-key dict predict_prospectivity_v3() expects.
    v3_features = {
        **geo_features,
        "thickness_m": thickness["thickness_m"],
        "ore_grade_mn_pct": grade_estimate["ore_grade_mn_pct"],  # synthetic-but-real-calibrated per-point value
        "water_table_depth_m": water_table["water_table_depth_m"],
    }

    prospectivity = predict_prospectivity_v3(v3_features)
    score = prospectivity["prospectivity_score"]
    top_features, _ = explain_by_perturbation(v3_features)

    op_inputs = get_mine_operational_inputs(mine["id"])
    if op_inputs:
        forecast = predict_forecast(op_inputs["forecast_input"])
        risk_level = forecast["risk_level"]
    else:
        forecast = None
        risk_level = "Medium"  # no production history for this mine (4 of 12 mock mines lack records)

    remaining_reserve, annual_production = get_state_reserve_and_production(state)

    # Real grade/company breakdown for known mines (separate from the
    # synthetic per-point grade_estimate fed into the model above — this is
    # the REAL IBM Yearbook district breakdown, shown for context).
    grade = real_grade
    companies = get_companies_for_mine(mine["name"])

    viability = compute_viability_index(
        prospectivity_score=score,
        shortfall_risk_label=risk_level,
        water_table_depth_m=water_table["water_table_depth_m"],
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
        "thickness": thickness,
        "water_table": water_table,
        "social_infra": social_infra,
        "grade": grade,
        "companies": companies,
    }


@router.get("/predict_point")
def predict_point(lat: float, lng: float):
    return score_zone(lat, lng, use_real_satellite=True)


@router.get("/zones")
def get_zones(bbox: str = "78.0,18.0,84.0,25.0", resolution: int = 20):
    cached = load_zones_cache(bbox, resolution)
    if cached is not None:
        return cached

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
                    "reserve_min_tonnes": result["prospectivity"]["reserve_min_tonnes"],
                    "reserve_max_tonnes": result["prospectivity"]["reserve_max_tonnes"],
                    "top_features": result["top_features"],
                    "viability_index": result["viability"]["viability_index"],
                    "viability_components": result["viability"]["components"],
                    "thickness_m": result["thickness"]["thickness_m"],
                    "water_table_depth_m": result["water_table"]["water_table_depth_m"],
                    "social_infra_score": result["social_infra"]["social_infra_score"],
                    "grade": result["grade"],
                    "companies": result["companies"],
                    "attributes_are_partly_synthetic": True,  # thickness/water/social-infra — see site_attributes.py
                },
            })

    result = {"type": "FeatureCollection", "features": features_out}
    save_zones_cache(bbox, resolution, result)
    return result


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
    from .site_attributes import get_water_table_estimate

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [m["lng"], m["lat"]]},
                "properties": {"name": m["name"], **get_water_table_estimate(m["lat"], m["lng"])},
            }
            for m in MINES
        ],
    }
