"""
Real satellite NDVI fetcher — uses Google Earth Engine's Python API to pull
actual Sentinel-2 imagery, not synthetic estimates.

Requires:
  pip install earthengine-api
  earthengine authenticate   (run once, opens browser for Google login)
"""
import ee

_initialized = False


def _ensure_init():
    global _initialized
    if not _initialized:
        ee.Initialize()
        _initialized = True


def get_real_ndvi(lat: float, lng: float, buffer_m: int = 500):
    """Returns real NDVI computed from the least-cloudy Sentinel-2 scene
    in the last 6 months over the given point."""
    _ensure_init()
    point = ee.Geometry.Point([lng, lat])
    image = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(point)
        .filterDate("2025-01-01", "2025-06-30")
        .sort("CLOUDY_PIXEL_PERCENTAGE")
        .first()
    )
    ndvi = image.normalizedDifference(["B8", "B4"])
    result = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(buffer_m), scale=10
    ).getInfo()
    return result.get("nd")
