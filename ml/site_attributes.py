"""
site_attributes.py
---------------------
Three attributes requested that have NO real public dataset reachable from
this environment: ore thickness, water table depth, and nearby social
infrastructure (hospitals/schools). Every value here is SYNTHETIC-BUT-
CALIBRATED, following the exact same honesty standard as your own
docs/methodology.md — not presented as real, with a documented path to
replace with real data.

WHAT WOULD MAKE EACH ONE REAL:
  - thickness_m: real borehole/drill-core logs (MOIL/GSI internal data,
    not publicly available — this is explicitly the kind of data your own
    methodology.md already flags as "commercially held, wasn't available").
  - water_table_depth_m: download real data from India-WRIS
    (https://indiawris.gov.in) or CGWB district reports — publicly
    downloadable, just needs a human to fetch it (my sandbox can't reach
    .gov.in domains). See swap_in_real_water_table() below for the exact
    function signature to replace.
  - social_infra_score: data.gov.in publishes district-level facility
    counts (hospitals, schools) under various open datasets — same
    situation as water table, fetchable by a human, not by this sandbox.

USE IN YOUR PITCH: be upfront that these three are illustrative/synthetic
if a judge asks — same honest framing your methodology.md already uses for
the forecast model's downtime/rainfall data. Don't present these as real.
"""

import hashlib

# Deterministic per-mine "randomness" so repeated calls return the same
# value (not true randomness, which would make the API non-reproducible
# and look broken in a demo — same value every time you query the same mine).
def _stable_hash_float(seed: str, lo: float, hi: float) -> float:
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    frac = (h % 10000) / 10000.0
    return round(lo + frac * (hi - lo), 2)


# Ore thickness calibrated to the REAL geology_type categories already in
# your prospectivity model — gondite_archean seams (Balaghat-type deposits)
# are documented in mining literature as thicker/more continuous than
# laterite-hosted (Goa-type) surface deposits, so relative ordering here
# reflects real geological literature even though exact numbers are synthetic.
THICKNESS_RANGE_BY_GEOLOGY = {
    "gondite_archean": (1.5, 8.0),      # MOIL's Balaghat-belt seams — thickest, most continuous
    "kodurite_archean": (1.0, 5.0),
    "archean": (0.8, 4.0),
    "laterite": (0.3, 2.5),             # laterite-hosted deposits are typically thin, blanket-like
}


def get_thickness_estimate(lat: float, lng: float, geology_type: str):
    lo, hi = THICKNESS_RANGE_BY_GEOLOGY.get(geology_type, (0.5, 3.0))
    thickness = _stable_hash_float(f"{lat:.3f},{lng:.3f},thickness", lo, hi)
    return {
        "thickness_m": thickness,
        "is_synthetic": True,
        "note": "Illustrative — real value requires borehole/drill-core data (not publicly available).",
    }


def get_water_table_estimate(lat: float, lng: float):
    """
    Synthetic placeholder. Swap for real India-WRIS/CGWB data by replacing
    this function's body with a real lookup — keep the same return shape
    ({"water_table_depth_m": float, "is_synthetic": bool}) so nothing else
    in routes_map.py/viability_index.py needs to change.
    """
    depth = _stable_hash_float(f"{lat:.3f},{lng:.3f},water", 3.0, 40.0)
    return {
        "water_table_depth_m": depth,
        "is_synthetic": True,
        "note": "Illustrative — real value available from India-WRIS (indiawris.gov.in) or CGWB district reports.",
    }


def swap_in_real_water_table(lat: float, lng: float):
    """
    TEMPLATE for when you've downloaded real CGWB/India-WRIS data. Load your
    downloaded file (likely a CSV or shapefile keyed by district/block) here,
    do a spatial join against (lat, lng), and return the same shape:
        return {"water_table_depth_m": <real value>, "is_synthetic": False}
    Then swap the call in routes_map.py from get_water_table_estimate() to
    this function.
    """
    raise NotImplementedError("Load your real CGWB/India-WRIS file here once downloaded.")


def get_social_infra_score(lat: float, lng: float, state: str):
    """
    Synthetic 0-1 "site readiness" proxy — higher means more nearby
    hospitals/schools/infrastructure, relevant for workforce feasibility and
    CSR planning, not for the geological model itself. Weighted slightly by
    state to at least reflect real relative development levels
    (illustrative weighting, not from a real infrastructure dataset).
    """
    state_baseline = {
        "Madhya Pradesh": 0.45, "Maharashtra": 0.55, "Odisha": 0.40,
        "Karnataka": 0.60, "Andhra Pradesh": 0.50, "Goa": 0.70, "Jharkhand": 0.35,
    }.get(state, 0.45)

    noise = _stable_hash_float(f"{lat:.3f},{lng:.3f},infra", -0.15, 0.15)
    score = max(0.0, min(1.0, state_baseline + noise))
    return {
        "social_infra_score": round(score, 3),
        "is_synthetic": True,
        "note": "Illustrative — real value available from data.gov.in district facility datasets.",
    }


# REAL state averages — identical to generate_prospectivity_data_v3.py's
# state_avg_grade_pct (computed from data/real/gradewise_production_by_district_2020_21.csv).
# Used here ONLY for arbitrary exploration coordinates with no known mine —
# for a named known mine, grade_lookup.py's get_grade_for_mine() returns the
# actual real district-level breakdown instead and should always be preferred.
STATE_AVG_GRADE_PCT = {
    "Odisha": 31.4, "Karnataka": 25.1, "Madhya Pradesh": 27.6, "Maharashtra": 34.3,
    "Andhra Pradesh": 19.7, "Goa": 18.0, "Jharkhand": 22.0,
}


def get_grade_estimate(lat: float, lng: float, state: str):
    """
    Synthetic-but-real-calibrated ore grade estimate for an arbitrary
    exploration coordinate that isn't a known mine (so grade_lookup.py's
    real per-district data doesn't apply). Centers on the same real state
    average the v3 training data used, with plausible per-point noise.
    """
    baseline = STATE_AVG_GRADE_PCT.get(state, 24.0)
    grade = max(8.0, min(54.0, _stable_hash_float(f"{lat:.3f},{lng:.3f},grade", baseline - 8, baseline + 8)))
    return {
        "ore_grade_mn_pct": grade,
        "is_synthetic": True,
        "note": f"Centered on real {state} state average ({baseline}% Mn) from IBM Yearbook 2021 gradewise data; per-point value is illustrative.",
    }


if __name__ == "__main__":
    print(get_thickness_estimate(21.8, 80.18, "gondite_archean"))
    print(get_water_table_estimate(21.8, 80.18))
    print(get_social_infra_score(21.8, 80.18, "Madhya Pradesh"))
    print(get_grade_estimate(21.8, 80.18, "Madhya Pradesh"))
