"""
grade_lookup.py
-----------------
Real ore quality/grade breakdown by district, from
data/real/gradewise_production_by_district_2020_21.csv (IBM Yearbook 2021).

Answers the "quality, how many layers" attribute from the exploration
reference sheet — this is REAL data, not synthetic. Grade bands are Mn
content by weight: 46%+ (highest), 35-46%, 25-35%, below 25% (lowest).

mines.json only stores state, not district, so DISTRICT_MAP below ties each
mock mine to its real district using actual geography (e.g. Sandur block is
genuinely in Ballari district, Karnataka). Where a mock mine's exact district
isn't in the gradewise CSV, it falls back to the nearest real manganese
district in the same state/belt — documented per entry, not guessed silently.
"""

import os
import csv
from collections import defaultdict

_ML_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.normpath(os.path.join(_ML_DIR, "..", "data"))


def _load_csv(*parts):
    with open(os.path.join(_DATA_DIR, *parts), encoding="utf-8") as f:
        return list(csv.DictReader(f))


_GRADE_ROWS = _load_csv("real", "gradewise_production_by_district_2020_21.csv")
GRADE_BY_DISTRICT = {
    (row["state"], row["district"]): {
        "num_mines": int(row["num_mines"]),
        "grade_46plus_tonnes": int(row["grade_46plus_tonnes"]),
        "grade_35to46_tonnes": int(row["grade_35to46_tonnes"]),
        "grade_25to35_tonnes": int(row["grade_25to35_tonnes"]),
        "grade_below25_tonnes": int(row["grade_below25_tonnes"]),
        "total_quantity_tonnes": int(row["total_quantity_tonnes"]),
    }
    for row in _GRADE_ROWS
}

# mine_name (from mock/mines.json) -> real (state, district) key into the
# table above. Verified against actual Indian manganese-belt geography.
DISTRICT_MAP = {
    "Balaghat Manganese Block": ("Madhya Pradesh", "Balaghat"),
    "Ukwa Manganese Mine": ("Madhya Pradesh", "Balaghat"),          # Ukwa sits in Balaghat district
    "Chhindwara Manganese Block": ("Madhya Pradesh", "Chhindwara"),
    "Jhabua Manganese Block": ("Madhya Pradesh", "Jhabua"),
    "Keonjhar Manganese Belt": ("Odisha", "Keonjhar"),
    "Bonai Manganese Block": ("Odisha", "Sundargarh"),              # Bonai is a sub-division of Sundargarh district
    "Nagpur Manganese Mine": ("Maharashtra", "Nagpur"),
    "Bhandara Manganese Block": ("Maharashtra", "Bhandara"),
    "Shimoga Manganese Mine": ("Karnataka", "Davanagere"),          # nearest gradewise-listed KA district; Shimoga itself not in this CSV
    "Sandur Manganese Block": ("Karnataka", "Ballari"),             # Sandur is genuinely within Ballari district
    "Srikakulam Manganese Mine": ("Andhra Pradesh", "Vizianagaram"),  # nearest AP manganese belt district in this CSV
    "Vizianagaram Manganese Block": ("Andhra Pradesh", "Vizianagaram"),
}


def get_grade_for_mine(mine_name: str):
    """Returns real grade breakdown + a computed 'high_grade_share' summary metric."""
    key = DISTRICT_MAP.get(mine_name)
    if not key:
        return None
    grade = GRADE_BY_DISTRICT.get(key)
    if not grade:
        return None

    total = grade["total_quantity_tonnes"] or 1
    high_grade_share = round((grade["grade_46plus_tonnes"] + grade["grade_35to46_tonnes"]) / total, 3)

    return {
        "state": key[0],
        "district": key[1],
        **grade,
        "high_grade_share_pct": round(high_grade_share * 100, 1),
    }


if __name__ == "__main__":
    for name in ["Balaghat Manganese Block", "Sandur Manganese Block", "Keonjhar Manganese Belt"]:
        print(name, "->", get_grade_for_mine(name))
