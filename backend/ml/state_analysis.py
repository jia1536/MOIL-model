import csv
import os

from .country_comparison import COUNTRY_DATA, compare_countries

_DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))

NATIONAL_RESERVES_KEY = "All_India"
NATIONAL_PRODUCTION_KEY = "India"
YEARS = ["2018-19", "2019-20", "2020-21"]

# Illustrative thresholds, applied to years of PROVEN reserves at the latest
# production rate. These are a screening label, not a mine planning standard.
CRITICAL_YEARS = 25
WATCH_YEARS = 50


def _load_csv(*parts):
    with open(os.path.join(_DATA_DIR, *parts), encoding="utf-8") as f:
        return list(csv.DictReader(f))


_RESERVES = {
    row["state"]: {
        "reserves_kt": float(row["reserves_thousand_tonnes"]),
        "remaining_resources_kt": float(row["remaining_resources_thousand_tonnes"]),
        "total_kt": float(row["total_thousand_tonnes"]),
    }
    for row in _load_csv("real", "reserves_by_state.csv")
}

_PRODUCTION = {}
for _row in _load_csv("real", "production_by_state_2018_2021.csv"):
    _PRODUCTION.setdefault(_row["state"], {})[_row["year"]] = float(_row["quantity_tonnes"])


def _production_history(prod_key):
    series = _PRODUCTION.get(prod_key, {})
    return [{"year": y, "tonnes": series.get(y)} for y in YEARS]


def _latest_production(prod_key):
    value = _PRODUCTION.get(prod_key, {}).get(YEARS[-1])
    return value if value else None  # 0 or missing both mean "not producing"


def _avg_production(prod_key):
    # Mean over all three years, zeros included, so a state that stopped
    # producing does not look like it kept its earlier rate.
    values = [_PRODUCTION.get(prod_key, {}).get(y) or 0 for y in YEARS]
    return sum(values) / len(values) if any(values) else None


def _years_left(reserve_kt, production_t):
    if not reserve_kt or not production_t:
        return None
    return round(reserve_kt * 1000 / production_t, 1)


def _status(years_of_reserves):
    if years_of_reserves is None:
        return "Not producing"
    if years_of_reserves < CRITICAL_YEARS:
        return "Critical"
    if years_of_reserves < WATCH_YEARS:
        return "Watch"
    return "Adequate"


def _change_pct(prod_key):
    first = _PRODUCTION.get(prod_key, {}).get(YEARS[0])
    last = _PRODUCTION.get(prod_key, {}).get(YEARS[-1])
    if not first:
        return None
    return round((last - first) / first * 100, 1)


def _state_names():
    return [s for s in _RESERVES if s != NATIONAL_RESERVES_KEY]


def _match_state(name):
    target = name.strip().lower()
    for state in _RESERVES:
        if state.lower() == target:
            return state
    return None


def _state_row(state):
    res = _RESERVES[state]
    national = _RESERVES[NATIONAL_RESERVES_KEY]
    latest = _latest_production(state)
    national_latest = _latest_production(NATIONAL_PRODUCTION_KEY)
    years_reserves = _years_left(res["reserves_kt"], latest)
    return {
        "state": state,
        "reserves_kt": res["reserves_kt"],
        "remaining_resources_kt": res["remaining_resources_kt"],
        "total_resources_kt": res["total_kt"],
        "share_of_national_reserves_pct": round(res["reserves_kt"] / national["reserves_kt"] * 100, 1),
        "share_of_national_resources_pct": round(res["total_kt"] / national["total_kt"] * 100, 1),
        "production_2020_21_t": latest or 0,
        "share_of_national_production_pct": (
            round(latest / national_latest * 100, 1) if latest and national_latest else 0.0
        ),
        "production_history": _production_history(state),
        "production_change_pct": _change_pct(state),
        "years_of_reserves": years_reserves,
        "years_of_total_resources": _years_left(res["total_kt"], latest),
        "status": _status(years_reserves),
    }


def _national_row():
    national = _RESERVES[NATIONAL_RESERVES_KEY]
    latest = _latest_production(NATIONAL_PRODUCTION_KEY)
    years_reserves = _years_left(national["reserves_kt"], latest)
    return {
        "state": "All India",
        "reserves_kt": national["reserves_kt"],
        "remaining_resources_kt": national["remaining_resources_kt"],
        "total_resources_kt": national["total_kt"],
        "production_2020_21_t": latest or 0,
        "production_history": _production_history(NATIONAL_PRODUCTION_KEY),
        "production_change_pct": _change_pct(NATIONAL_PRODUCTION_KEY),
        "years_of_reserves": years_reserves,
        "years_of_total_resources": _years_left(national["total_kt"], latest),
        "status": _status(years_reserves),
    }


def compare_states(states=None):
    """Side by side state comparison. `states` is an optional list of names."""
    not_found = []
    if states:
        chosen = []
        for name in states:
            match = _match_state(name)
            if match and match != NATIONAL_RESERVES_KEY:
                chosen.append(match)
            else:
                not_found.append(name)
    else:
        chosen = _state_names()

    rows = sorted((_state_row(s) for s in chosen), key=lambda r: r["total_resources_kt"], reverse=True)
    return {
        "states": rows,
        "national": _national_row(),
        "not_found": not_found,
        "notes": [
            "Reserves and resources are ore, in thousand tonnes. Production is ore, in tonnes.",
            "Reserves are the economically extractable part. Remaining resources are the less certain part.",
            "States with no production figure for 2020-21 show 0 and no years-left value.",
        ],
    }


def depletion_report(state=None):
    if state:
        match = _match_state(state)
        if not match:
            return None
        names = [match] if match != NATIONAL_RESERVES_KEY else []
    else:
        names = _state_names()

    entries = []
    for name in names:
        res = _RESERVES[name]
        latest = _latest_production(name)
        avg = _avg_production(name)
        years_reserves = _years_left(res["reserves_kt"], latest)
        entries.append({
            "state": name,
            "reserves_kt": res["reserves_kt"],
            "total_resources_kt": res["total_kt"],
            "production_2020_21_t": latest or 0,
            "production_3yr_avg_t": round(avg) if avg else 0,
            "production_change_pct": _change_pct(name),
            "years_of_reserves": years_reserves,
            "years_of_reserves_at_3yr_avg": _years_left(res["reserves_kt"], avg) if latest else None,
            "years_of_total_resources": _years_left(res["total_kt"], latest),
            "status": _status(years_reserves),
        })

    # Producing states first, shortest life first. Non producing states last.
    entries.sort(key=lambda e: (e["years_of_reserves"] is None, e["years_of_reserves"] or 0))

    return {
        "states": entries,
        "national": _national_row() if not state or _match_state(state) == NATIONAL_RESERVES_KEY else None,
        "thresholds": {
            "critical_below_years": CRITICAL_YEARS,
            "watch_below_years": WATCH_YEARS,
            "basis": "Years of proven reserves at the 2020-21 production rate. "
                     "Illustrative screening thresholds, not a mine planning standard.",
        },
    }


def _norm_country(name):
    return name.strip().lower().replace("_", "").replace(" ", "")


def compare_countries_report(countries=None):
    all_names = [c for c in COUNTRY_DATA if c != "World_Total"]
    detail = compare_countries(all_names)

    rows = []
    for name in all_names:
        d = detail[name]
        reserves = d.get("reserves_thousand_tonnes_metal_content")
        p2018 = d.get("production_2018_thousand_tonnes")
        p2020 = d.get("production_2020_thousand_tonnes")
        rows.append({
            "country": name.replace("_", " "),
            "reserves_kt": reserves,
            "production_2018_kt": p2018,
            "production_2019_kt": d.get("production_2019_thousand_tonnes"),
            "production_2020_kt": p2020,
            "share_of_world_reserves_pct": d.get("share_of_world_reserves_pct"),
            "share_of_world_production_pct": d.get("share_of_world_production_2020_pct"),
            "years_at_2020_rate": round(reserves / p2020, 1) if reserves and p2020 else None,
            "production_change_pct": round((p2020 - p2018) / p2018 * 100, 1) if p2018 and p2020 else None,
            "rank_by_reserves": None,
            "rank_by_production": None,
        })

    by_reserves = sorted([r for r in rows if r["reserves_kt"]], key=lambda r: r["reserves_kt"], reverse=True)
    by_production = sorted([r for r in rows if r["production_2020_kt"]], key=lambda r: r["production_2020_kt"], reverse=True)
    for i, r in enumerate(by_reserves, 1):
        r["rank_by_reserves"] = i
    for i, r in enumerate(by_production, 1):
        r["rank_by_production"] = i

    rows.sort(key=lambda r: r["reserves_kt"] or 0, reverse=True)
    india = next((r for r in rows if r["country"] == "India"), None)

    if countries:
        wanted = {_norm_country(c) for c in countries}
        rows = [r for r in rows if _norm_country(r["country"]) in wanted]

    world = COUNTRY_DATA.get("World_Total", {})
    return {
        "countries": rows,
        "india": india,
        "countries_ranked": {"by_reserves": len(by_reserves), "by_production": len(by_production)},
        "world_total": {
            "reserves_kt": world.get("reserves_thousand_tonnes_metal_content"),
            "production_2020_kt": world.get("production_2020_thousand_tonnes"),
        },
        "notes": [
            "Metal content basis, thousand tonnes, 2020 world table.",
            "Only the countries in this table are ranked. Other producers are inside the world total but not listed.",
            "India's figure here is contained manganese metal, so it is lower than the state ore reserve figures used on the state tab.",
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(depletion_report()["states"][:3], indent=1))
    print(json.dumps(compare_countries_report()["india"], indent=1))
