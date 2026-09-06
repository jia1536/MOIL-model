# SIH26009 — Manganese Prospectivity & Production Forecasting (ML Pipeline)

This repo contains my individual ML/data contribution to **Smart India Hackathon 2026**, for Problem Statement **SIH26009**: *"Using AI/ML and Space Technology to Identify Manganese Reserves and Overcome Production Shortfalls"* (MOIL Limited / Ministry of Steel).

> This is a personal portfolio copy of my contribution. The full team submission, including frontend and backend, lives at the team repo: **[Rounak-T/sih26009_prototype](https://github.com/Rounak-T/sih26009_prototype)**

---

## What's in this repo

| Folder | Contents |
|---|---|
| `data/mock/` | Synthetic mine, production, equipment, and risk data (JSON/GeoJSON) used to unblock frontend/backend development before real data was available |
| `data/real/` | Real Indian Bureau of Mines (IBM) Yearbook 2021 data — state-wise reserves, production, gradewise output, and real MOIL mine names/locations |
| `ml/` | Synthetic training data generators, model training scripts, trained models, and a prediction wrapper |
| `docs/methodology.md` | Full methodology notes — what's real vs. synthetic, and why |

---

## Two ML models

### 1. Manganese Prospectivity Model (`prospectivity_v2.pkl`)
Predicts a 0–1 prospectivity score for a given location, using **15 features across 6 exploration-parameter categories**:

- **Geological** — geology type, distance to fault
- **Remote sensing** — NDVI, NDWI, land surface temperature, mineral alteration index
- **Geochemical** — Mn ppm in soil
- **Geophysical** — magnetic anomaly
- **Terrain** — elevation, slope, drainage density
- **Ground truth** — distance to nearest real MOIL mine

**Performance:** MAE 0.052, R² 0.71 (on synthetic hold-out data)

### 2. Production Shortfall Forecast Model (`forecast_v1.pkl`)
Predicts forecasted production tonnage given historical average, planned target, equipment downtime, and rainfall — flags shortfall risk as Low/Medium/High.

**Performance:** MAE 670 tonnes, R² 0.94 (on synthetic hold-out data)

---

## Honest data disclosure

No real, labeled manganese exploration dataset (borehole assays, per-mine downtime logs) is publicly available in India. This project uses:
- **Real data** wherever public: state/district reserves, production, gradewise breakdowns, and real MOIL mine names/coordinates (IBM Yearbook 2021).
- **Synthetic data** for everything requiring proprietary or field-collected data, but **calibrated against the real numbers above** — e.g., geology-type weighting matches real state reserve shares, and shortfall volatility ranges match real observed production swings.

Full transparency on every feature is in [`docs/methodology.md`](docs/methodology.md).

---

## Quick start

```bash
cd ml
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
python predict.py
```

`predict.py` exposes two functions:

```python
from predict import predict_prospectivity, predict_forecast

predict_prospectivity({
    "lat": 21.8, "lng": 80.18, "elevation": 400, "slope_deg": 12,
    "drainage_density": 1.5, "ndvi": 0.6, "ndwi": 0.1, "land_surface_temp": 30,
    "mineral_alteration_index": 0.7, "mn_ppm_soil": 1600, "magnetic_anomaly_nt": 95,
    "distance_to_fault_km": 3, "distance_to_known_mine_km": 2,
    "geology_type": "gondite_archean"
})

predict_forecast({
    "mine_type": "underground", "historical_avg": 10000,
    "planned_tonnes": 12000, "downtime_hours": 120, "rainfall": 1200
})
```

**Note:** requires `scikit-learn==1.8.0` specifically — a version mismatch will cause a `ModuleNotFoundError: No module named '_loss'` when loading the models.

---

## Retraining on new data

If real MOIL data becomes available, only the CSVs in `ml/data/` need to change — the training scripts (`train_prospectivity_v2.py`, `train_forecast.py`) and `predict.py`'s function signatures stay the same.
