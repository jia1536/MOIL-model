"""
SIH26009 Backend — FastAPI service
Serves mock mine/production/risk data and wraps the two ML models
(prospectivity + production forecast) as prediction endpoints.

Run with:
    uvicorn main:app --reload --port 8000
"""
import csv
import io
import json
import os
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ml.predict import predict_prospectivity, predict_forecast

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_DIR = os.path.join(BASE_DIR, "data", "mock")

app = FastAPI(title="SIH26009 Manganese Intelligence API", version="1.0")

# Allow the React dev server (localhost:5173 for Vite, 3000 for CRA) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your actual frontend URL before final deployment
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


# ---------- CSV upload endpoint ----------

UPLOAD_REQUIRED_COLUMNS = {"mine_id", "period", "planned_tonnes", "actual_tonnes"}


@app.post("/api/upload")
async def upload_production_csv(file: UploadFile = File(...)):
    """
    Accepts a production CSV (mine_id, period, planned_tonnes, actual_tonnes),
    validates it, and appends the rows into production.json so the dashboard,
    charts, and forecast tools immediately reflect the new data.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only .csv files are supported")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="Could not decode file as UTF-8 text")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=422, detail="Could not read CSV headers")

    missing = UPLOAD_REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    new_rows = []
    row_errors = []
    for line_num, row in enumerate(reader, start=2):  # row 1 is the header
        try:
            new_rows.append({
                "mine_id": row["mine_id"].strip(),
                "period": row["period"].strip(),
                "planned_tonnes": float(row["planned_tonnes"]),
                "actual_tonnes": float(row["actual_tonnes"]),
            })
        except (ValueError, AttributeError):
            row_errors.append(f"Row {line_num}: invalid or missing numeric value")

    if not new_rows:
        raise HTTPException(status_code=422, detail="No valid rows found in file")

    path = os.path.join(MOCK_DIR, "production.json")
    existing = load_json("production.json") if os.path.exists(path) else []
    existing.extend(new_rows)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

    return {
        "status": "success",
        "filename": file.filename,
        "rows_added": len(new_rows),
        "rows_skipped": len(row_errors),
        "errors": row_errors[:10],  # cap so a bad file doesn't flood the response
    }


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
