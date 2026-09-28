import joblib
import pandas as pd
import os

_DIR = os.path.dirname(os.path.abspath(__file__))
_prospectivity_bundle = joblib.load(os.path.join(_DIR, "models", "prospectivity_v2.pkl"))
_forecast_bundle = joblib.load(os.path.join(_DIR, "models", "forecast_v1.pkl"))


def predict_prospectivity(features: dict) -> dict:
    df = pd.DataFrame([features])
    df = pd.get_dummies(df)
    df = df.reindex(columns=_prospectivity_bundle["columns"], fill_value=0)
    score = float(_prospectivity_bundle["model"].predict(df)[0])
    score = max(0.0, min(1.0, score))
    return {
        "prospectivity_score": round(score, 3),
        "confidence": round(_prospectivity_bundle["r2"], 2),  # model's own hold-out R2 as a stand-in confidence signal
        "reserve_min": int(score * 150000),
        "reserve_max": int(score * 350000),
    }


def predict_forecast(features: dict) -> dict:
    df = pd.DataFrame([features])
    df = pd.get_dummies(df)
    df = df.reindex(columns=_forecast_bundle["columns"], fill_value=0)
    forecast_tonnes = float(_forecast_bundle["model"].predict(df)[0])
    forecast_tonnes = max(0.0, forecast_tonnes)

    planned = features.get("planned_tonnes", forecast_tonnes)
    shortfall_pct = round(max(0, (planned - forecast_tonnes) / planned * 100), 1) if planned else 0.0
    risk_score = min(100, int(shortfall_pct * 2.8))
    risk_level = "Low" if risk_score < 35 else "Medium" if risk_score < 65 else "High"

    return {
        "forecast_tonnes": round(forecast_tonnes, 1),
        "shortfall_pct": shortfall_pct,
        "risk_score": risk_score,
        "risk_level": risk_level,
    }


if __name__ == "__main__":
    # standalone sanity test — run `python predict.py` before handing off
    print("Prospectivity test (Balaghat-like: gondite_archean, high Mn ppm, near known mine):")
    print(predict_prospectivity({
        "lat": 21.8, "lng": 80.18, "elevation": 400, "slope_deg": 12,
        "drainage_density": 1.5, "ndvi": 0.6, "ndwi": 0.1, "land_surface_temp": 30,
        "mineral_alteration_index": 0.7, "mn_ppm_soil": 1600, "magnetic_anomaly_nt": 95,
        "distance_to_fault_km": 3, "distance_to_known_mine_km": 2,
        "geology_type": "gondite_archean"
    }))

    print("\nProspectivity test (Goa-like: laterite, low Mn ppm, far from known mines):")
    print(predict_prospectivity({
        "lat": 15.3, "lng": 74.0, "elevation": 200, "slope_deg": 8,
        "drainage_density": 0.8, "ndvi": 0.5, "ndwi": 0.2, "land_surface_temp": 29,
        "mineral_alteration_index": 0.35, "mn_ppm_soil": 350, "magnetic_anomaly_nt": 15,
        "distance_to_fault_km": 20, "distance_to_known_mine_km": 400,
        "geology_type": "laterite"
    }))

    print("\nForecast test (underground mine, high downtime):")
    print(predict_forecast({
        "mine_type": "underground", "historical_avg": 10000,
        "planned_tonnes": 12000, "downtime_hours": 180, "rainfall": 1400
    }))

    print("\nForecast test (opencast mine, low downtime):")
    print(predict_forecast({
        "mine_type": "opencast", "historical_avg": 9000,
        "planned_tonnes": 9500, "downtime_hours": 30, "rainfall": 900
    }))

    print("\nEdge case — missing optional keys:")
    print(predict_forecast({"planned_tonnes": 10000}))
