import os
import ee
import numpy as np
from datetime import datetime, timedelta


PATCH_SIZE_M = 640          # patch edge length in meters (~64 px at 10m/px)
CLOUD_PROB_THRESHOLD = 40   # % — pixels above this are masked as cloud


_initialized = False


def init_earth_engine():
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
    global _initialized
    if not _initialized:
        init_earth_engine()


def _mask_clouds(image):
    scl = image.select("SCL")
    # SCL classes 3 (cloud shadow), 8 (cloud medium prob), 9 (cloud high prob),
    # 10 (thin cirrus) are masked out.
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)


def get_sentinel2_composite(lat, lng, months_back=6):
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
