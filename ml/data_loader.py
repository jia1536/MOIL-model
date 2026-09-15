"""
data_loader.py
----------------
Loads the REAL data files from your repo (data/mock/*.json, data/real/*.csv)
and exposes clean lookup functions. This replaces every hardcoded placeholder
list from earlier drafts with your actual data.

Assumes this file sits in ml/, alongside predict.py, and that data/ is a
sibling of ml/ (matches your zip's structure exactly:
  SIH26009_deliverables/
    data/mock/..., data/real/...
    ml/predict.py, ml/data_loader.py (this file), ...
)
"""

import os
import json
import csv
from collections import defaultdict

_ML_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.normpath(os.path.join(_ML_DIR, "..", "data"))


def _load_json(*parts):
    with open(os.path.join(_DATA_DIR, *parts), encoding="utf-8") as f:
        return json.load(f)


def _load_csv(*parts):
    with open(os.path.join(_DATA_DIR, *parts), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---- Mines (data/mock/mines.json) ----
MINES = _load_json("mock", "mines.json")
MINES_BY_ID = {m["id"]: m for m in MINES}


def find_mine_by_name(name: str):
    """Case-insensitive partial match, e.g. 'balaghat' -> Balaghat Manganese Block."""
    name_l = name.lower()
    for m in MINES:
        if name_l in m["name"].lower():
            return m
    return None


def nearest_mine(lat, lng):
    import math

    def haversine_km(lat1, lng1, lat2, lng2):
        r = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))

    return min(MINES, key=lambda m: haversine_km(lat, lng, m["lat"], m["lng"]))


def distance_to_nearest_mine_km(lat, lng):
    import math

    def haversine_km(lat1, lng1, lat2, lng2):
        r = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lng2 - lng1)
        a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))

    return min(haversine_km(lat, lng, m["lat"], m["lng"]) for m in MINES)


# ---- Production history (data/mock/production.json) ----
_PRODUCTION_RAW = _load_json("mock", "production.json")
_PRODUCTION_BY_MINE = defaultdict(list)
for rec in _PRODUCTION_RAW:
    _PRODUCTION_BY_MINE[rec["mine_id"]].append(rec)
for mine_id in _PRODUCTION_BY_MINE:
    _PRODUCTION_BY_MINE[mine_id].sort(key=lambda r: r["period"])


def get_historical_avg(mine_id: str, last_n_quarters: int = 4):
    """Mean actual_tonnes over the last N quarters — feeds predict_forecast()'s historical_avg."""
    records = _PRODUCTION_BY_MINE.get(mine_id, [])
    if not records:
        return None
    recent = records[-last_n_quarters:]
    return sum(r["actual_tonnes"] for r in recent) / len(recent)


def get_latest_planned_tonnes(mine_id: str):
    records = _PRODUCTION_BY_MINE.get(mine_id, [])
    return records[-1]["planned_tonnes"] if records else None


# ---- Equipment downtime (data/mock/equipment_downtime.json) ----
_DOWNTIME_RAW = _load_json("mock", "equipment_downtime.json")
_DOWNTIME_BY_MINE_PERIOD = defaultdict(float)
for rec in _DOWNTIME_RAW:
    _DOWNTIME_BY_MINE_PERIOD[(rec["mine_id"], rec["period"])] += rec["downtime_hours"]


def get_latest_downtime_hours(mine_id: str):
    """Sums downtime across all equipment for that mine's most recent period."""
    periods = sorted({p for (mid, p) in _DOWNTIME_BY_MINE_PERIOD if mid == mine_id})
    if not periods:
        return None
    latest = periods[-1]
    return _DOWNTIME_BY_MINE_PERIOD[(mine_id, latest)]


# ---- Real state reserves (data/real/reserves_by_state.csv) ----
_RESERVES_ROWS = _load_csv("real", "reserves_by_state.csv")
RESERVES_BY_STATE = {
    row["state"]: {
        "reserves_thousand_tonnes": float(row["reserves_thousand_tonnes"]),
        "remaining_resources_thousand_tonnes": float(row["remaining_resources_thousand_tonnes"]),
        "total_thousand_tonnes": float(row["total_thousand_tonnes"]),
    }
    for row in _RESERVES_ROWS
}

# ---- Real state production, most recent year (data/real/production_by_state_2018_2021.csv) ----
_PROD_STATE_ROWS = _load_csv("real", "production_by_state_2018_2021.csv")
PRODUCTION_BY_STATE_2020_21 = {
    row["state"]: float(row["quantity_tonnes"])
    for row in _PROD_STATE_ROWS
    if row["year"] == "2020-21"
}


def get_state_reserve_and_production(state: str):
    """
    Real reserve (converted to tonnes) and real 2020-21 production for a state
    — feeds viability_index.py's reserve_urgency calculation.
    """
    reserve = RESERVES_BY_STATE.get(state)
    remaining_tonnes = reserve["total_thousand_tonnes"] * 1000 if reserve else None
    annual_production_tonnes = PRODUCTION_BY_STATE_2020_21.get(state)
    return remaining_tonnes, annual_production_tonnes


# ---- Real MOIL underground mine details (data/real/moil_underground_mines.csv) ----
_MOIL_ROWS = _load_csv("real", "moil_underground_mines.csv")
_MOIL_TYPE_BY_NAME = {row["mine_name"].lower(): row["mine_type"] for row in _MOIL_ROWS}


def infer_mine_type(mine_name: str) -> str:
    """
    Matches against the real MOIL underground mine list first (exact operational
    data: Balaghat, Ukwa = underground; Tirodi = opencast_mechanised; etc.).
    Falls back to "underground" for MOIL's historical MP/Maharashtra belt,
    "opencast" elsewhere — most non-MOIL Indian manganese producers (Odisha,
    Karnataka, AP state mines) predominantly use opencast methods.
    """
    name_l = mine_name.lower()
    for real_name, mine_type in _MOIL_TYPE_BY_NAME.items():
        if real_name in name_l or name_l.split()[0] in real_name:
            return "opencast" if "opencast" in mine_type else "underground"
    return "opencast"  # default for non-MOIL state producers not in the underground-mines list


def get_mine_operational_inputs(mine_id_or_name: str, rainfall_mm: float = 1200):
    """
    Assembles a full predict_forecast() input dict for a mine, using REAL
    production + downtime data where available.

    rainfall_mm: not present in any provided dataset (mock or real) — defaults
    to 1200mm, roughly mid-range of synthetic_forecast.csv's training
    distribution (~900-1800mm). Replace with real IMD/OpenWeatherMap data for
    the mine's district once available — see docs/API_KEYS_SETUP.md.
    """
    mine = MINES_BY_ID.get(mine_id_or_name) or find_mine_by_name(mine_id_or_name)
    if not mine:
        return None

    mine_id = mine["id"]
    historical_avg = get_historical_avg(mine_id)
    planned_tonnes = get_latest_planned_tonnes(mine_id)
    downtime_hours = get_latest_downtime_hours(mine_id)

    if historical_avg is None:
        # This mine has no production.json records (only 8 of 12 mock mines do)
        return None

    return {
        "mine": mine,
        "forecast_input": {
            "mine_type": infer_mine_type(mine["name"]),
            "historical_avg": historical_avg,
            "planned_tonnes": planned_tonnes,
            "downtime_hours": downtime_hours if downtime_hours is not None else 60,
            "rainfall": rainfall_mm,
        },
    }


if __name__ == "__main__":
    print(f"{len(MINES)} mines loaded")
    print("Balaghat operational inputs:", get_mine_operational_inputs("Balaghat"))
    print("MP reserve/production:", get_state_reserve_and_production("Madhya Pradesh"))
