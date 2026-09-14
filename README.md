# SIH26009 — Manganese Intelligence Dashboard

A working full-stack app: FastAPI backend serving mock/real data + your two ML models, and a React frontend with a live map, production charts, risk breakdown, and an interactive prospectivity prediction tool.

## Backend setup

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit http://127.0.0.1:8000/docs to see and test every endpoint interactively (FastAPI auto-generates this).

**Note:** requires `scikit-learn==1.8.0` exactly — already pinned in requirements.txt.

## Frontend setup

Open a **second** terminal (keep the backend running in the first):

```powershell
cd frontend
npm install
npm run dev
```

It'll print a local URL (usually http://localhost:5173) — open that in your browser.

## What you'll see

- **Overview tab:** a Leaflet map of all 12 mock mines plus the prospectivity zones (colored by score), a risk breakdown panel, and a planned-vs-actual production chart — click any mine on the map to update everything.
- **Prospectivity model tab:** an interactive form where you enter site conditions (geology, NDVI, Mn ppm, etc.) and get a live prediction from your trained `prospectivity_v2.pkl` model.

## API endpoints (backend)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/mines` | GET | List all mines |
| `/api/production?mine_id=` | GET | Production history |
| `/api/equipment?mine_id=` | GET | Equipment list |
| `/api/equipment_downtime?mine_id=` | GET | Downtime logs |
| `/api/forecast?mine_id=` | GET | Shortfall forecast |
| `/api/risks?mine_id=` | GET | Risk factor breakdown |
| `/api/recommendations?mine_id=` | GET | Suggested actions |
| `/api/prospectivity_zones` | GET | GeoJSON prospectivity map |
| `/api/predict/prospectivity` | POST | Live prospectivity prediction |
| `/api/predict/forecast` | POST | Live shortfall forecast prediction |

## Known limitations to be aware of

- Map tiles (OpenStreetMap) require internet access — if your laptop is offline, markers will still show but the background map won't render.
- CORS is currently wide open (`allow_origins=["*"]`) for easy local development — tighten this to your actual frontend URL before any public deployment.
- This uses mock data throughout — see `docs/methodology.md` in your ML deliverables for the full honest breakdown of what's real vs. synthetic.
