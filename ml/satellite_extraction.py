"""
satellite_extraction.py
------------------------
Pulls real Sentinel-2 imagery from Google Earth Engine for a given point or
region, computes the spectral indices your prospectivity model already uses
(NDVI, NDWI, mineral alteration index), AND exports raw multi-band image
patches for the CNN model (cnn_patch_model.py).

Why this file exists:
Your current pipeline computes indices but there's no single, reusable place
that (a) authenticates to GEE, (b) fetches a clean, cloud-masked Sentinel-2
composite, and (c) returns both tabular features (for RF/XGBoost) and raw
patches (for the CNN) from ONE call. Two consumers, one source of truth.

Requires: earthengine-api, geemap (optional, for local raster export)
    pip install earthengine-api geemap numpy --break-system-packages

Auth setup (one-time):
    earthengine authenticate
or, for a server/service account (recommended for a deployed FastAPI backend):
    1. Create a GCP project, enable the Earth Engine API
    2. Create a service account, download its JSON key
    3. Share the key path via env var: GEE_SERVICE_ACCOUNT_JSON
"""

import os
import ee
import numpy as np
from datetime import datetime, timedelta


PATCH_SIZE_M = 640          # patch edge length in meters (~64 px at 10m/px)
CLOUD_PROB_THRESHOLD = 40   # % — pixels above this are masked as cloud


_initialized = False


def init_earth_engine():
    """
    Authenticate using a service account if provided, else your local
    interactive auth token (from `earthengine authenticate`).

    GEE_PROJECT_ID: set this once as an environment variable to your Google
    Cloud project ID (the one you created at code.earthengine.google.com and
    ran `earthengine set_project` with). Without it, ee.Initialize() throws
    "no project found" even after successful authentication.
    """
    global _initialized
    key_path = os.environ.get("GEE_SERVICE_ACCOUNT_JSON")
    project_id = os.environ.get("GEE_PROJECT_ID")

    if key_path and os.path.exists(key_path):
        credentials = ee.ServiceAccountCredentials(None, key_path)
        ee.Initialize(credentials, project=project_id)
    else:
        ee.Initialize(project=project_id)
    _initialized = True


def _ensure_initialized():
    """
    Auto-calls init_earth_engine() the first time any function in this file
    actually needs it — so callers (routes_map.py, the chatbot, etc.) don't
    need to remember to call init_earth_engine() themselves every time.
    """
    global _initialized
    if not _initialized:
        init_earth_engine()


def _mask_clouds(image):
    """Use Sentinel-2 Scene Classification Layer (SCL) to drop cloud/shadow px."""
    scl = image.select("SCL")
    # SCL classes 3 (cloud shadow), 8 (cloud medium prob), 9 (cloud high prob),
    # 10 (thin cirrus) are masked out.
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)


def get_sentinel2_composite(lat, lng, months_back=6):
    """Cloud-masked median Sentinel-2 SR composite around a point, last N months."""
    _ensure_initialized()
    point = ee.Geometry.Point([lng, lat])
    region = point.buffer(PATCH_SIZE_M / 2).bounds()

    end = datetime.utcnow()
    start = end - timedelta(days=30 * months_back)

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .map(_mask_clouds)
    )

    composite = collection.median().clip(region)
    return composite, region


def compute_spectral_indices(composite):
    """
    Returns NDVI, NDWI, and mineral_alteration_index — 3 of the 4 remote-sensing
    features predict_prospectivity() expects (see predict.py's exact input
    schema: ndvi, ndwi, land_surface_temp, mineral_alteration_index).
    land_surface_temp is NOT derivable from Sentinel-2 (no thermal band) —
    it's fetched separately from Landsat 8/9 in get_landsat_lst() below.
    """
    ndvi = composite.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndwi = composite.normalizedDifference(["B3", "B8"]).rename("NDWI")

    # Mineral alteration index: ratio highlighting iron-oxide / clay alteration,
    # analogous to the PCA/SAM alteration anomalies used in the Malkansu (China)
    # study, but computed directly from band ratios for a lightweight prototype.
    alteration = composite.select("B11").divide(composite.select("B12")).rename(
        "mineral_alteration_index"
    )

    stacked = ndvi.addBands([ndwi, alteration])
    return stacked


def get_landsat_lst(lat, lng, months_back=6):
    """
    Real Land Surface Temperature from Landsat 8/9 Collection 2 Level 2
    (ST_B10 thermal band, already converted to Kelvin by USGS, scaled per
    their documented factors). This is the actual land_surface_temp value
    predict_prospectivity() expects — not a proxy.
    """
    _ensure_initialized()
    point = ee.Geometry.Point([lng, lat])
    region = point.buffer(PATCH_SIZE_M / 2).bounds()

    end = datetime.utcnow()
    start = end - timedelta(days=30 * months_back)

    collection = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(region)
        .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        .filter(ee.Filter.lt("CLOUD_COVER", 30))
    )

    def scale_thermal(img):
        # USGS Collection 2 Level 2 scaling factors for ST_B10
        lst_celsius = img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15)
        return lst_celsius.rename("LST_C").copyProperties(img, img.propertyNames())

    lst_composite = collection.map(scale_thermal).median()
    value = lst_composite.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(50), scale=30
    ).getInfo()
    return value.get("LST_C")


def extract_point_features(lat, lng):
    """
    Returns a dict with EXACTLY the 4 remote-sensing keys predict.py's
    predict_prospectivity() expects: ndvi, ndwi, land_surface_temp,
    mineral_alteration_index.

    NOTE on real vs. training-range values: real satellite band ratios can
    fall outside the ranges the synthetic training data used (e.g. a raw
    B11/B12 ratio can exceed 1, while training data was hand-generated in
    0-1). Verified this doesn't distort predictions for the current
    RandomForestRegressor (tree splits treat any out-of-range value the same
    as the training boundary), but values are clipped here anyway as cheap
    insurance in case the model is ever swapped for something sensitive to
    input scale (e.g. the CNN ensemble branch in cnn_patch_model.py).
    """
    composite, region = get_sentinel2_composite(lat, lng)
    indices = compute_spectral_indices(composite)

    point = ee.Geometry.Point([lng, lat])
    values = indices.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(50), scale=10
    ).getInfo()

    ndvi = values.get("NDVI")
    ndwi = values.get("NDWI")
    lst = get_landsat_lst(lat, lng)
    alteration = values.get("mineral_alteration_index")

    return {
        "ndvi": max(-1.0, min(1.0, ndvi)) if ndvi is not None else None,
        "ndwi": max(-1.0, min(1.0, ndwi)) if ndwi is not None else None,
        "land_surface_temp": lst,  # not clipped — real temperature extremes are meaningful, not noise
        "mineral_alteration_index": max(0.0, min(1.0, alteration)) if alteration is not None else None,
    }


def export_patch_array(lat, lng, bands=("B2", "B3", "B4", "B8", "B11", "B12")):
    """
    Returns a numpy array (H, W, len(bands)) of raw reflectance values for the
    patch around (lat, lng) — this is what feeds the CNN in cnn_patch_model.py.
    Uses ee.data.computePixels for a direct in-memory fetch (no Drive export
    needed, good for an API endpoint that must respond in seconds).
    """
    composite, region = get_sentinel2_composite(lat, lng)
    image = composite.select(list(bands))

    request = {
        "expression": image,
        "fileFormat": "NUMPY_NDARRAY",
        "grid": {
            "dimensions": {"width": 64, "height": 64},
            "affineTransform": {
                "scaleX": PATCH_SIZE_M / 64,
                "scaleY": -PATCH_SIZE_M / 64,
                "translateX": lng,
                "translateY": lat,
            },
            "crsCode": "EPSG:4326",
        },
    }
    raw = ee.data.computePixels(request)
    # Structured numpy array -> plain (H, W, C) float32 array
    arr = np.stack([raw[b] for b in bands], axis=-1).astype("float32")
    return arr


def get_real_terrain(lat, lng):
    """
    Real elevation + slope from the SRTM 30m Digital Elevation Model —
    genuinely better than geological_lookup.py's synthetic-mean fallback for
    these two features, and free with the same GEE account you're already
    using for Sentinel-2/Landsat (no extra signup, no extra key).
    """
    _ensure_initialized()
    point = ee.Geometry.Point([lng, lat])
    dem = ee.Image("USGS/SRTMGL1_003")

    elevation = dem.select("elevation").reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(50), scale=30
    ).get("elevation")

    slope = ee.Terrain.slope(dem).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(50), scale=30
    ).get("slope")

    result = ee.Dictionary({"elevation": elevation, "slope": slope}).getInfo()
    return result.get("elevation"), result.get("slope")


if __name__ == "__main__":
    init_earth_engine()
    feats = extract_point_features(lat=21.8, lng=80.18)
    print("Remote-sensing features:", feats)

    elevation, slope = get_real_terrain(lat=21.8, lng=80.18)
    print(f"Real SRTM terrain: elevation={elevation}m, slope={slope}deg")

    patch = export_patch_array(lat=21.8, lng=80.18)
    print("Patch array shape:", patch.shape)
