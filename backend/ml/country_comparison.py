import os
import csv

_ML_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.normpath(os.path.join(_ML_DIR, "..", "data"))


def _load_csv(*parts):
    with open(os.path.join(_DATA_DIR, *parts), encoding="utf-8") as f:
        return list(csv.DictReader(f))


_ROWS = _load_csv("real", "world_reserves_production_2020.csv")


def _to_float(val):
    return None if val in (None, "", "NA") else float(val)


COUNTRY_DATA = {
    row["country"]: {
        "reserves_thousand_tonnes_metal_content": _to_float(row["reserves_thousand_tonnes_metal_content"]),
        "production_2018_thousand_tonnes": _to_float(row["production_2018_thousand_tonnes"]),
        "production_2019_thousand_tonnes": _to_float(row["production_2019_thousand_tonnes"]),
        "production_2020_thousand_tonnes": _to_float(row["production_2020_thousand_tonnes"]),
    }
    for row in _ROWS
}


def compare_countries(countries: list):
    world = COUNTRY_DATA.get("World_Total", {})
    world_reserves = world.get("reserves_thousand_tonnes_metal_content") or 1
    world_production_2020 = world.get("production_2020_thousand_tonnes") or 1

    result = {}
    for country in countries:
        data = COUNTRY_DATA.get(country)
        if not data:
            result[country] = {"error": "No data for this country name — check exact spelling/underscore (e.g. 'Ivory_Coast')"}
            continue
        reserves = data["reserves_thousand_tonnes_metal_content"]
        production_2020 = data["production_2020_thousand_tonnes"]
        result[country] = {
            **data,
            "share_of_world_reserves_pct": round(reserves / world_reserves * 100, 2) if reserves else None,
            "share_of_world_production_2020_pct": round(production_2020 / world_production_2020 * 100, 2) if production_2020 else None,
        }
    return result


def rank_all_countries_by_reserves():
    ranked = [
        (country, data["reserves_thousand_tonnes_metal_content"])
        for country, data in COUNTRY_DATA.items()
        if country != "World_Total" and data["reserves_thousand_tonnes_metal_content"]
    ]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


if __name__ == "__main__":
    print(compare_countries(["India", "South Africa", "Australia", "China"]))
    print()
    print("Ranked by reserves:", rank_all_countries_by_reserves())
