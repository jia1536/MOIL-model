# Methodology Notes — SIH26009

## Real data sources used (grounding, not training labels)
- **IBM Indian Minerals Yearbook 2021 (60th Edition)** — state/district reserve figures, gradewise
  production tonnage, real principal producer names (MOIL, Tata Steel, Sandur Manganese, etc.),
  real MOIL underground mine names (Balaghat, Ukwa, Chikla, Kandri, Mansar, Gumgaon) with real
  operational details (shaft depths, mining methods).
- Used for: geographic grounding, realistic value ranges for synthetic data, context/benchmark slides.
- **Not** used for: direct ML training labels — no real prospectivity scores or per-mine downtime
  logs exist publicly, so these remain synthetic (see below).

## Synthetic data — what's real vs. illustrative

### Prospectivity dataset — v2 (`ml/data/synthetic_prospectivity_v2.csv`)
Expanded to cover 6 of the 8 standard exploration-parameter categories (geological,
remote sensing, geochemical, geophysical, terrain, and ground-truth), following the
team's exploration-parameter reference:

| Category | Features included | Status |
|---|---|---|
| 1. Geological | `geology_type`, `distance_to_fault_km` | Partial — full lithology/fault mapping out of scope |
| 2. Remote sensing | `ndvi`, `ndwi`, `land_surface_temp`, `mineral_alteration_index` | Synthetic, realistic ranges |
| 3. Geochemical | `mn_ppm_soil` | Synthetic, calibrated to real IBM grade bands |
| 4. Geophysical | `magnetic_anomaly_nt` | Synthetic — manganese ores are a known magnetic indicator |
| 5. Terrain | `elevation`, `slope_deg`, `drainage_density` | Synthetic, realistic ranges |
| 6. Ground truth | `distance_to_known_mine_km` | Computed from REAL MOIL mine coordinates |
| 7. Spatial | folded into `distance_to_fault_km` / `distance_to_known_mine_km` | Partial |
| 8. Economic/reserve | *not included* | Deliberately excluded — this is a reserve-estimation problem, not a prospectivity-classifier input; positioned as a downstream step after AI narrows down zones |

State sampling weights still approximate real national reserve shares (Odisha 34%,
Karnataka 24%, etc. — from IBM Yearbook Table 1). Geology categories still follow the
real geological series named in the yearbook (Gondite Series, Kodurite Series, laterite).

The prospectivity_score is still a **hand-defined rule + noise**, now combining geology,
geochemistry (Mn ppm), geophysics (magnetic anomaly), remote sensing (NDVI, alteration
index), and proximity to a known real mine — weighted so geology dominates but the other
categories meaningfully move the score, matching how a geologist would actually weigh
multiple lines of evidence rather than relying on one signal alone.

v1 (`synthetic_prospectivity.csv`, `prospectivity_v1.pkl`) is kept for reference but
v2 is the current model used by `predict.py`.

### Forecast dataset (`ml/data/synthetic_forecast.csv`)
- Shortfall volatility range calibrated against real observed swings (national production fell
  ~7.6% 2019-20→2020-21; individual states like Andhra Pradesh fell ~24% in the same period, per
  `production_by_state_2018_2021.csv`).
- Underground vs. opencast downtime gap reflects real operational text in the yearbook (ongoing
  shaft-sinking/ventilation work at MOIL's underground mines).
- forecast_tonnes is generated from a hand-defined downtime/rainfall penalty rule + noise — not
  real per-mine planned-vs-actual records (those are commercially held by MOIL and weren't
  available to us).

## Model evaluation — read this before quoting numbers to judges
Both models were evaluated on a **synthetic hold-out set**. This measures whether the model
learned the rules we defined, not real-world geological or operational accuracy.

- Prospectivity model v2 (RandomForestRegressor, 15 features across 6 parameter categories): MAE ≈ 0.052, R² ≈ 0.71 on synthetic hold-out.
- Forecast model (GradientBoostingRegressor): MAE ≈ 670 tonnes, R² ≈ 0.94 on synthetic hold-out.

**Honest framing for judges:** "We built and validated the full ML pipeline — feature engineering,
training, evaluation, and a production-ready prediction API — against synthetic data calibrated
to real IBM reserve, grade, and production statistics. The architecture is ready to retrain on
real MOIL exploration/production data the moment it's shared; the pipeline itself doesn't change,
only the training CSV would be swapped."

## What would change with real MOIL data
If MOIL shares real borehole assays, mine-lease-level production, or equipment logs:
1. Replace `ml/data/synthetic_*.csv` with real feature tables (same column schema).
2. Re-run `train_prospectivity.py` / `train_forecast.py` unchanged.
3. `predict.py`'s function signatures don't change — Backend integration is unaffected.
