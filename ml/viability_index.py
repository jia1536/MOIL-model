"""
viability_index.py
--------------------
The actual code behind the "genuine innovation" claim in INNOVATION_SUMMARY.md.
Every cited paper stops at a prospectivity score. This fuses FOUR signals
into one rankable number per zone:

    1. prospectivity_score   — from predict_prospectivity() (0-1, higher = better geology)
    2. shortfall_risk        — from predict_forecast() (Low/Medium/High -> 0-1, higher = worse)
    3. water_stress          — from CGWB water table depth (0-1, higher = harder to mine)
    4. reserve_urgency       — how depleted the known reserve is (0-1, higher = more urgent)

None of these four are new models — they're your existing two models plus
two lookups, combined with a transparent, tunable weighted formula. That's
deliberate: a defensible formula you can explain in 10 seconds beats an
opaque 5th model nobody can justify live in front of judges.
"""

RISK_TO_SCORE = {"low": 0.2, "medium": 0.55, "high": 0.9}

DEFAULT_WEIGHTS = {
    "prospectivity": 0.40,
    "shortfall_risk": 0.25,   # subtracted — high risk lowers viability
    "water_stress": 0.15,     # subtracted — high stress lowers viability
    "reserve_urgency": 0.20,  # added — more urgent reserves should be prioritized
}


def normalize_water_stress(depth_m):
    """
    Shallower water table = higher stress for underground mining (flooding
    risk, pumping cost). depth_m below 5m -> high stress; above 30m -> low.
    Tune these thresholds against real CGWB bands for your target districts.
    """
    if depth_m is None:
        return 0.3  # unknown -> mild default penalty, not zero
    if depth_m < 5:
        return 1.0
    if depth_m > 30:
        return 0.0
    return round(1.0 - (depth_m - 5) / 25, 3)


def normalize_reserve_urgency(remaining_reserve_tonnes, annual_production_tonnes):
    """
    Years-of-reserve-left, inverted and capped: a mine with <5 years left at
    current production rate is "urgent" (1.0); >30 years is low urgency (0.0).
    This is the depletion-rate metric requested to answer "how much manganese
    is left" — computed straight from IBM Yearbook reserve + production figures.
    """
    if not remaining_reserve_tonnes or not annual_production_tonnes:
        return 0.3
    years_left = remaining_reserve_tonnes / annual_production_tonnes
    if years_left < 5:
        return 1.0
    if years_left > 30:
        return 0.0
    return round(1.0 - (years_left - 5) / 25, 3)


def compute_viability_index(
    prospectivity_score: float,
    shortfall_risk_label: str,
    water_table_depth_m: float = None,
    remaining_reserve_tonnes: float = None,
    annual_production_tonnes: float = None,
    weights: dict = None,
):
    """
    Returns the fused 0-1 Mine Viability Index plus the component breakdown,
    so the map popup / chatbot can show exactly why a zone ranked where it did.
    """
    w = weights or DEFAULT_WEIGHTS
    risk_score = RISK_TO_SCORE.get((shortfall_risk_label or "medium").lower(), 0.55)
    water_stress = normalize_water_stress(water_table_depth_m)
    urgency = normalize_reserve_urgency(remaining_reserve_tonnes, annual_production_tonnes)

    raw = (
        w["prospectivity"] * prospectivity_score
        - w["shortfall_risk"] * risk_score
        - w["water_stress"] * water_stress
        + w["reserve_urgency"] * urgency
    )
    # Clip to 0-1 since the subtractive terms can push it negative
    index = max(0.0, min(1.0, raw))

    return {
        "viability_index": round(index, 4),
        "components": {
            "prospectivity_score": prospectivity_score,
            "shortfall_risk_score": risk_score,
            "water_stress_score": water_stress,
            "reserve_urgency_score": urgency,
        },
        "weights_used": w,
    }


if __name__ == "__main__":
    example = compute_viability_index(
        prospectivity_score=0.82,
        shortfall_risk_label="high",
        water_table_depth_m=8,
        remaining_reserve_tonnes=1_200_000,
        annual_production_tonnes=90_000,
    )
    print(example)
