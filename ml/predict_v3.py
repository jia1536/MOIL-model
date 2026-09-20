"""
predict_v3.py
---------------
Standalone wrapper for prospectivity_v3.pkl — kept separate from your own
predict.py so your original file is never touched; routes_map.py imports
from here instead of predict.py for the prospectivity call.

KEY DIFFERENCE FROM v2's reserve_min/reserve_max:
v2 used reserve_min = score * 150000, reserve_max = score * 350000 — arbitrary
constants with no connection to the ore body itself. v3 replaces this with an
actual simplified block-model estimate:

    tonnes = area_m2 * thickness_m * bulk_density_t_per_m3 * (ore_grade_mn_pct/100) * score

This assumes a nominal 1 km^2 exploration block (documented, not hidden) and
a bulk density of 2.6 t/m^3 (typical for manganese-bearing gondite/archean
rock — a standard mining-engineering approximation, not measured on-site).
It's still an illustrative estimate, not a certified reserve figure — real
reserve estimation requires drilling density and cutoff-grade analysis this
prototype doesn't have access to — but thickness and grade now visibly
change the number, instead of it being pure noise dressed as a range.
"""
import joblib
import pandas as pd
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_bundle = joblib.load(os.path.join(_DIR, "models", "prospectivity_v3.pkl"))

NOMINAL_BLOCK_AREA_M2 = 1_000_000  # 1 km^2 — documented assumption, not measured
BULK_DENSITY_T_PER_M3 = 2.6        # typical for Mn-bearing gondite/archean rock


def predict_prospectivity_v3(features: dict) -> dict:
    """
    Expected keys: everything predict.py's v2 predict_prospectivity() needs,
    PLUS thickness_m, ore_grade_mn_pct, water_table_depth_m.
    """
    df = pd.DataFrame([features])
    df = pd.get_dummies(df)
    df = df.reindex(columns=_bundle["columns"], fill_value=0)
    score = float(_bundle["model"].predict(df)[0])
    score = max(0.0, min(1.0, score))

    thickness_m = features.get("thickness_m", 0)
    grade_pct = features.get("ore_grade_mn_pct", 0)

    central_estimate = (
        NOMINAL_BLOCK_AREA_M2 * thickness_m * BULK_DENSITY_T_PER_M3 * (grade_pct / 100) * score
    )

    return {
        "prospectivity_score": round(score, 3),
        "confidence": round(_bundle["r2"], 2),
        "reserve_min_tonnes": int(central_estimate * 0.7),
        "reserve_max_tonnes": int(central_estimate * 1.3),
        "reserve_estimate_note": (
            f"Illustrative block-model estimate assuming a {NOMINAL_BLOCK_AREA_M2/1e6:.0f} km^2 "
            f"nominal block and {BULK_DENSITY_T_PER_M3} t/m^3 bulk density — "
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
