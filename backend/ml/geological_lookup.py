STATE_BOUNDS = {
    "Odisha":          {"lat": (19.5, 22.5), "lng": (83.5, 87.0)},
    "Karnataka":       {"lat": (12.0, 18.5), "lng": (74.5, 78.5)},
    "Madhya Pradesh":  {"lat": (21.0, 24.5), "lng": (74.0, 82.0)},
    "Maharashtra":     {"lat": (19.0, 21.5), "lng": (78.5, 80.5)},
    "Andhra Pradesh":  {"lat": (17.5, 19.0), "lng": (82.5, 84.5)},
    "Goa":             {"lat": (15.0, 15.8), "lng": (73.8, 74.3)},
    "Jharkhand":       {"lat": (22.0, 24.0), "lng": (85.0, 87.0)},
}

STATE_GEOLOGY = {
    "Odisha": "gondite_archean", "Karnataka": "archean", "Madhya Pradesh": "gondite_archean",
    "Maharashtra": "gondite_archean", "Andhra Pradesh": "kodurite_archean",
    "Goa": "laterite", "Jharkhand": "archean",
}

GEOLOGY_BOOST_MAP = {"gondite_archean": 0.32, "archean": 0.24, "kodurite_archean": 0.14, "laterite": 0.08}

# Training-set means for the 3 location-independent terrain features and the
# fault-distance feature — used only as a fallback when real DEM data isn't fetched.
FALLBACK_ELEVATION = 500.0       # midpoint of uniform(100, 900)
FALLBACK_SLOPE_DEG = 18.0        # midpoint of uniform(1, 35)
FALLBACK_DRAINAGE_DENSITY = 1.6  # midpoint of uniform(0.2, 3.0)
FALLBACK_DISTANCE_TO_FAULT_KM = 8.0  # mean of exponential(8)


def state_for_coordinate(lat, lng):
    for state, bounds in STATE_BOUNDS.items():
        lat_lo, lat_hi = bounds["lat"]
        lng_lo, lng_hi = bounds["lng"]
        if lat_lo <= lat <= lat_hi and lng_lo <= lng <= lng_hi:
            return state
    return None  # outside all 7 mapped states — geology_type will need a manual default


def lookup_geological_features(lat, lng, real_elevation=None, real_slope_deg=None):
    state = state_for_coordinate(lat, lng)

    if state is None:
        # Outside the 7 mapped manganese-belt states — use the lowest-grade
        # geology as a conservative default rather than guessing.
        geology_type = "laterite"
        geo_boost = GEOLOGY_BOOST_MAP[geology_type]
    else:
        geology_type = STATE_GEOLOGY[state]
        geo_boost = GEOLOGY_BOOST_MAP[geology_type]

    # Same deterministic formulas as the generator, with noise terms dropped
    # (noise existed to create training variance, not because the "true" mean
    # value is unknown for a specific query point).
    mn_ppm_soil = max(50.0, 300 + geo_boost * 1500)
    magnetic_anomaly_nt = max(0.0, geo_boost * 120)
    mineral_alteration_index_prior = min(1.0, max(0.0, 0.4 + geo_boost * 0.5))

    return {
        "elevation": real_elevation if real_elevation is not None else FALLBACK_ELEVATION,
        "slope_deg": real_slope_deg if real_slope_deg is not None else FALLBACK_SLOPE_DEG,
        "drainage_density": FALLBACK_DRAINAGE_DENSITY,
        "mn_ppm_soil": round(mn_ppm_soil, 1),
        "magnetic_anomaly_nt": round(magnetic_anomaly_nt, 1),
        "distance_to_fault_km": FALLBACK_DISTANCE_TO_FAULT_KM,
        "geology_type": geology_type,
        "_state": state,  # not a model feature — useful for the chatbot/UI to display
        "_mineral_alteration_prior": round(mineral_alteration_index_prior, 3),  # cross-check against real satellite value
    }


if __name__ == "__main__":
    print("Balaghat area (MP):", lookup_geological_features(21.8, 80.18))
    print("Goa (laterite):", lookup_geological_features(15.3, 74.0))
    print("Outside mapped states:", lookup_geological_features(28.6, 77.2))  # Delhi
