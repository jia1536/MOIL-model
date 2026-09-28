import joblib
import numpy as np
import pandas as pd
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_bundle = joblib.load(os.path.join(_DIR, "models", "prospectivity_v3.pkl"))

NOMINAL_BLOCK_AREA_M2 = 1_000_000  # 1 km^2 — documented assumption, not measured
BULK_DENSITY_T_PER_M3 = 2.6        # typical for Mn-bearing gondite/archean rock


def predict_prospectivity_v3(features: dict) -> dict:
    df = pd.DataFrame([features])
    df = pd.get_dummies(df)
    df = df.reindex(columns=_bundle["columns"], fill_value=0)

    model = _bundle["model"]
    # Random Forest: each of the 250 trees votes independently. How much they
    # agree on THIS specific point is a real, per-point signal, unlike the
    # model's overall R^2 (a single number fixed at training time, the same
    # for every prediction regardless of where it is).
    tree_votes = np.array([tree.predict(df.values)[0] for tree in model.estimators_])
    score = float(tree_votes.mean())
    score = max(0.0, min(1.0, score))
    vote_std = float(tree_votes.std())
    # Score is bounded 0-1, so a std of 0 (trees fully agree) maps to 1.0
    # confidence and a std of 0.5 (near-maximum spread for a 0-1 target) maps
    # to 0.0. This is a real per-point agreement measure, not fabricated.
    point_confidence = round(max(0.0, min(1.0, 1 - vote_std / 0.5)), 2)

    thickness_m = features.get("thickness_m", 0)
    grade_pct = features.get("ore_grade_mn_pct", 0)

    central_estimate = (
        NOMINAL_BLOCK_AREA_M2 * thickness_m * BULK_DENSITY_T_PER_M3 * (grade_pct / 100) * score
    )

    return {
        "prospectivity_score": round(score, 3),
        "confidence": point_confidence,
        "model_r2": round(_bundle["r2"], 2),  # overall model skill, same for every point
        "reserve_min_tonnes": int(central_estimate * 0.7),
        "reserve_max_tonnes": int(central_estimate * 1.3),
        "reserve_estimate_note": (
            f"Illustrative block-model estimate assuming a {NOMINAL_BLOCK_AREA_M2/1e6:.0f} km^2 "
            f"nominal block and {BULK_DENSITY_T_PER_M3} t/m^3 bulk density, "
            "not a certified reserve figure."
        ),
    }


if __name__ == "__main__":
    print(predict_prospectivity_v3({
        "lat": 21.8, "lng": 80.18, "elevation": 400, "slope_deg": 12,
        "drainage_density": 1.5, "ndvi": 0.6, "ndwi": 0.1, "land_surface_temp": 30,
        "mineral_alteration_index": 0.7, "mn_ppm_soil": 1600, "magnetic_anomaly_nt": 95,
        "distance_to_fault_km": 3, "distance_to_known_mine_km": 2,
        "thickness_m": 5.0, "ore_grade_mn_pct": 34.0, "water_table_depth_m": 20.0,
        "geology_type": "gondite_archean",
    }))
