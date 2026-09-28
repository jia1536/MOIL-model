import os
import csv
from collections import defaultdict

_ML_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.normpath(os.path.join(_ML_DIR, "..", "data"))


def _load_csv(*parts):
    with open(os.path.join(_DATA_DIR, *parts), encoding="utf-8") as f:
        return list(csv.DictReader(f))


_PRODUCER_ROWS = _load_csv("real", "principal_producers_2020_21.csv")

PRODUCERS_BY_DISTRICT = defaultdict(list)
for row in _PRODUCER_ROWS:
    PRODUCERS_BY_DISTRICT[(row["state"], row["district"])].append(
        {"producer": row["producer"], "sector": row["sector"]}
    )

PRODUCERS_BY_STATE = defaultdict(list)
for row in _PRODUCER_ROWS:
    PRODUCERS_BY_STATE[row["state"]].append({"producer": row["producer"], "district": row["district"], "sector": row["sector"]})


def get_companies_for_mine(mine_name: str):
    from .grade_lookup import DISTRICT_MAP

    key = DISTRICT_MAP.get(mine_name)
    if not key:
        return None
    producers = PRODUCERS_BY_DISTRICT.get(key, [])
    public_count = sum(1 for p in producers if p["sector"] == "Public")
    private_count = sum(1 for p in producers if p["sector"] == "Private")
    return {
        "state": key[0],
        "district": key[1],
        "total_producers": len(producers),
        "public_sector_count": public_count,
        "private_sector_count": private_count,
        "producers": producers,
    }


def get_companies_for_state(state: str):
    producers = PRODUCERS_BY_STATE.get(state, [])
    return {
        "state": state,
        "total_producers": len(producers),
        "producers": producers,
    }


if __name__ == "__main__":
    print(get_companies_for_mine("Balaghat Manganese Block"))
    print(get_companies_for_state("Madhya Pradesh"))
