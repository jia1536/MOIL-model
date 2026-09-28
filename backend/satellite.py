import ee

from ml.satellite_extraction import _ensure_initialized


def get_real_ndvi(lat: float, lng: float, buffer_m: int = 500):
    _ensure_initialized()
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
