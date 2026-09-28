import hashlib
import json
import os

_CACHE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "cache"))
os.makedirs(_CACHE_DIR, exist_ok=True)


def _cache_key(bbox: str, resolution: int) -> str:
    return hashlib.md5(f"{bbox}:{resolution}".encode()).hexdigest()


def _cache_path(bbox: str, resolution: int) -> str:
    return os.path.join(_CACHE_DIR, f"zones_{_cache_key(bbox, resolution)}.json")


def load_zones_cache(bbox: str, resolution: int):
    path = _cache_path(bbox, resolution)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None  # corrupted/partial write -> treat as a cache miss, recompute


def save_zones_cache(bbox: str, resolution: int, data: dict):
    path = _cache_path(bbox, resolution)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp_path, path)


def clear_zones_cache():
    removed = 0
    for name in os.listdir(_CACHE_DIR):
        if name.startswith("zones_") and name.endswith(".json"):
            os.remove(os.path.join(_CACHE_DIR, name))
            removed += 1
    return removed
