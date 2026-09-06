"""
Synthetic production-shortfall training data — calibrated against REAL IBM figures.

Real anchors used (from data/real/production_by_state_2018_2021.csv):
  - National production fell from 2,910,186 t (2019-20) to 2,688,038 t (2020-21): ~7.6% YoY drop
    -> baseline "typical shortfall" for a bad year is roughly 5-10% at state level
  - Individual states swing much more: Andhra Pradesh fell ~24% (330,530 -> 250,255) in one year
    -> per-mine shortfall_pct range set wider (0-35%) to reflect real state-level volatility

Real anchors used (from IBM Yearbook 2021 text, MOIL underground mine operations):
  - Underground mines (Balaghat, Chikla, Kandri, Mansar, Gumgaon) report ongoing shaft-sinking
    and mechanisation work -> higher baseline downtime_hours for underground vs opencast mines
"""
import numpy as np
import pandas as pd

np.random.seed(7)
n = 600

mine_types = ["underground", "opencast"]
type_weights = [0.35, 0.65]  # most manganese mining in India is opencast; MOIL runs the main underground ones

rows = []
for _ in range(n):
    mtype = np.random.choice(mine_types, p=type_weights)
    historical_avg = np.random.uniform(6000, 18000)          # tonnes/quarter, plausible mine-level scale
    planned_tonnes = historical_avg * np.random.uniform(1.0, 1.12)

    # underground mines have real higher downtime due to shaft/ventilation work (per IBM text)
    downtime_hours = np.random.uniform(80, 220) if mtype == "underground" else np.random.uniform(20, 140)
    rainfall = np.random.uniform(700, 1800)                  # mm, monsoon disruption factor

    # rule: downtime and heavy rainfall reduce achieved production vs planned; add noise
    downtime_penalty = (downtime_hours / 220) * 0.28
    rainfall_penalty = max(0, (rainfall - 1200) / 1800) * 0.15
    noise = np.random.normal(0, 0.06)

    shortfall_frac = np.clip(downtime_penalty + rainfall_penalty + noise, 0, 0.4)
    forecast_tonnes = planned_tonnes * (1 - shortfall_frac)

    rows.append({
        "mine_type": mtype,
        "historical_avg": round(historical_avg, 1),
        "planned_tonnes": round(planned_tonnes, 1),
        "downtime_hours": round(downtime_hours, 1),
        "rainfall": round(rainfall, 1),
        "forecast_tonnes": round(forecast_tonnes, 1),
    })

df = pd.DataFrame(rows)
df.to_csv("/home/claude/ml/data/synthetic_forecast.csv", index=False)
print(df.head())
print(f"\nRows: {len(df)}")
print(df.groupby("mine_type")[["downtime_hours", "forecast_tonnes"]].mean())
