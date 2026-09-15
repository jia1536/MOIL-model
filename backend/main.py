"""
SIH26009 Backend — FastAPI service
Serves mock mine/production/risk data and wraps the two ML models
(prospectivity + production forecast) as prediction endpoints.

Run with:
    uvicorn main:app --reload --port 8000
"""
import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ml.predict import predict_prospectivity, predict_forecast

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_DIR = os.path.join(BASE_DIR, "data", "mock")

import os

app = FastAPI(title="SIH26009 Manganese Intelligence API", version="1.0")

# Allow local dev + your deployed Vercel frontend. Set FRONTEND_URL env var on Render
# to your actual Vercel URL (e.g. https://your-app.vercel.app) once deployed.
frontend_url = os.environ.get("FRONTEND_URL", "")
allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if frontend_url else ["*"],  # wide open until FRONTEND_URL is set
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_json(filename: str):
    path = os.path.join(MOCK_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    with open(path) as f:
        return json.load(f)


# ---------- Data endpoints (serve the mock/real data as-is) ----------

@app.get("/")
def root():
    return {"status": "ok", "service": "SIH26009 Manganese Intelligence API"}


@app.get("/api/mines")
def get_mines():
    return load_json("mines.json")


@app.get("/api/production")
def get_production(mine_id: Optional[str] = None):
    data = load_json("production.json")
    if mine_id:
        data = [d for d in data if d["mine_id"] == mine_id]
    return data


@app.get("/api/equipment")
def get_equipment(mine_id: Optional[str] = None):
    data = load_json("equipment.json")
    if mine_id:
        data = [d for d in data if d["mine_id"] == mine_id]
    return data


@app.get("/api/equipment_downtime")
def get_downtime(mine_id: Optional[str] = None):
    data = load_json("equipment_downtime.json")
    if mine_id:
        data = [d for d in data if d["mine_id"] == mine_id]
    return data


@app.get("/api/forecast")
def get_forecast(mine_id: Optional[str] = None):
    data = load_json("forecast.json")
    if mine_id:
        data = [d for d in data if d["mine_id"] == mine_id]
    return data


@app.get("/api/risks")
def get_risks(mine_id: Optional[str] = None):
    data = load_json("risks.json")
    if mine_id:
        data = [d for d in data if d["mine_id"] == mine_id]
    return data


@app.get("/api/recommendations")
def get_recommendations(mine_id: Optional[str] = None):
    data = load_json("recommendations.json")
    if mine_id:
        data = [d for d in data if d["mine_id"] == mine_id]
    return data


@app.get("/api/prospectivity_zones")
def get_prospectivity_zones():
    return load_json("prospectivity.geojson")


@app.get("/api/moil_real_mines")
def get_moil_real_mines():
    """Real MOIL mine names and approximate locations, sourced from moil.nic.in and steel.gov.in."""
    path = os.path.join(BASE_DIR, "data", "moil_real_locations.json")
    with open(path) as f:
        return json.load(f)


@app.get("/api/satellite/ndvi")
def api_real_ndvi(lat: float, lng: float):
    """Fetches REAL NDVI from Sentinel-2 via Google Earth Engine — not synthetic.
    Requires `earthengine authenticate` to have been run once on this machine."""
    try:
        from satellite import get_real_ndvi
        value = get_real_ndvi(lat, lng)
        return {"lat": lat, "lng": lng, "ndvi": value, "source": "Sentinel-2 (real, via Google Earth Engine)"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Earth Engine call failed: {str(e)}. Make sure you ran 'earthengine authenticate' and installed earthengine-api.",
        )


# ---------- ML prediction endpoints (wrap predict.py) ----------

class ProspectivityRequest(BaseModel):
    lat: float
    lng: float
    elevation: float
    slope_deg: float
    drainage_density: float
    ndvi: float
    ndwi: float
    land_surface_temp: float
    mineral_alteration_index: float
    mn_ppm_soil: float
    magnetic_anomaly_nt: float
    distance_to_fault_km: float
    distance_to_known_mine_km: float
    geology_type: str  # one of: gondite_archean, archean, kodurite_archean, laterite


class ForecastRequest(BaseModel):
    mine_type: str  # "underground" or "opencast"
    historical_avg: float
    planned_tonnes: float
    downtime_hours: float
    rainfall: float


@app.post("/api/predict/prospectivity")
def api_predict_prospectivity(req: ProspectivityRequest):
    try:
        return predict_prospectivity(req.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/predict/forecast")
def api_predict_forecast(req: ForecastRequest):
    try:
        return predict_forecast(req.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
