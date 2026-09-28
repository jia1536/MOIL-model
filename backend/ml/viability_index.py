RISK_TO_SCORE = {"low": 0.2, "medium": 0.55, "high": 0.9}

DEFAULT_WEIGHTS = {
    "prospectivity": 0.40,
    "shortfall_risk": 0.25,   # subtracted — high risk lowers viability
    "water_stress": 0.15,     # subtracted — high stress lowers viability
    "reserve_urgency": 0.20,  # added — more urgent reserves should be prioritized
}


def normalize_water_stress(depth_m):
    if depth_m is None:
        return 0.3  # unknown -> mild default penalty, not zero
    if depth_m < 5:
        return 1.0
    if depth_m > 30:
        return 0.0
    return round(1.0 - (depth_m - 5) / 25, 3)


def normalize_reserve_urgency(remaining_reserve_tonnes, annual_production_tonnes):
    if not remaining_reserve_tonnes or not annual_production_tonnes:
        return 0.3
    years_left = remaining_reserve_tonnes / annual_production_tonnes
    if years_left < 75:
        return 1.0
    if years_left > 400:
        return 0.0
    return round(1.0 - (years_left - 75) / 325, 3)


def compute_viability_index(
    prospectivity_score: float,
    shortfall_risk_label: str,
    water_table_depth_m: float = None,
    remaining_reserve_tonnes: float = None,
    annual_production_tonnes: float = None,
    weights: dict = None,
):
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

    best_risk, worst_risk = min(RISK_TO_SCORE.values()), max(RISK_TO_SCORE.values())
    raw_max = w["prospectivity"] * 1.0 - w["shortfall_risk"] * best_risk - w["water_stress"] * 0.0 + w["reserve_urgency"] * 1.0
    raw_min = w["prospectivity"] * 0.0 - w["shortfall_risk"] * worst_risk - w["water_stress"] * 1.0 + w["reserve_urgency"] * 0.0

    index = (raw - raw_min) / (raw_max - raw_min)
    index = max(0.0, min(1.0, index))  # guard against float edge cases only

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
