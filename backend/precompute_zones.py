import time

from ml.routes_map import get_zones

# (bbox as "min_lon,min_lat,max_lon,max_lat", resolution)
VIEWS = [
    ("78.0,18.0,84.0,25.0", 20),   # default full India-belt view (matches get_zones' default)
    ("78.0,18.0,84.0,25.0", 10),   # coarser/faster fallback, useful on a slow demo machine
]

if __name__ == "__main__":
    for bbox, resolution in VIEWS:
        t0 = time.time()
        result = get_zones(bbox=bbox, resolution=resolution)
        elapsed = time.time() - t0
        print(f"bbox={bbox} resolution={resolution}x{resolution}: "
              f"{len(result['features'])} cells cached in {elapsed:.1f}s")
    print("\nDone. These views will now be served instantly from cache.")
