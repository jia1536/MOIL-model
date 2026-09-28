import io

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from .data_loader import MINES, replace_mines
from .routes_map import score_zone

router = APIRouter()

# mode=score: only lat/lng are required — everything else in score_zone is
# looked up or estimated from the coordinates themselves.
SCORE_REQUIRED_COLUMNS = {"lat", "lng"}

# mode=replace: must match data/mock/mines.json's schema exactly, since this
# becomes the live MINES list every other endpoint reads from.
REPLACE_REQUIRED_COLUMNS = {"name", "state", "lat", "lng", "status", "type"}


def _read_csv_upload(file: UploadFile) -> pd.DataFrame:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail=f"Expected a .csv file, got '{file.filename}'.")
    raw = file.file.read()
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:  # pandas raises several different error types on bad CSVs
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")
    df.columns = [c.strip().lower() for c in df.columns]  # case/whitespace-tolerant headers
    return df


def _check_required_columns(df: pd.DataFrame, required: set, mode: str):
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"mode={mode} requires columns {sorted(required)} — missing: {sorted(missing)}. "
                   f"Found columns: {list(df.columns)}",
        )


@router.post("/csv")
async def upload_csv(
    file: UploadFile = File(...),
    mode: str = Query("score", pattern="^(score|replace)$"),
    use_real_satellite: bool = Query(False, description="mode=score only — true is slower (live Earth Engine per row) but more accurate; false uses the fast geological-prior path, same as /api/map/zones."),
    persist: bool = Query(True, description="mode=replace only — also overwrite data/mock/mines.json so the new set survives a server restart."),
):
    df = _read_csv_upload(file)

    if mode == "score":
        _check_required_columns(df, SCORE_REQUIRED_COLUMNS, mode)
        results = []
        errors = []
        for i, row in df.iterrows():
            try:
                lat, lng = float(row["lat"]), float(row["lng"])
            except (ValueError, TypeError):
                errors.append({"row": i, "error": f"lat/lng not numeric: {row.get('lat')}, {row.get('lng')}"})
                continue
            try:
                result = score_zone(lat, lng, use_real_satellite=use_real_satellite)
                results.append({
                    "row": i,
                    "lat": lat,
                    "lng": lng,
                    "prospectivity_score": result["prospectivity"]["prospectivity_score"],
                    "level": result["level"],
                    "nearest_mine": result["nearest_mine"],
                    "viability_index": result["viability"]["viability_index"],
                    "forecast": result["forecast"],
                    "full_result": result,
                })
            except Exception as exc:
                errors.append({"row": i, "lat": lat, "lng": lng, "error": str(exc)})

        return {
            "mode": "score",
            "rows_received": len(df),
            "rows_scored": len(results),
            "rows_failed": len(errors),
            "results": results,
            "errors": errors,
        }

    # mode == "replace"
    _check_required_columns(df, REPLACE_REQUIRED_COLUMNS, mode)
    new_mines = []
    for i, row in df.iterrows():
        try:
            new_mines.append({
                "id": str(row["id"]) if "id" in df.columns and pd.notna(row.get("id")) else f"uploaded_{i:03d}",
                "name": str(row["name"]),
                "state": str(row["state"]),
                "lat": float(row["lat"]),
                "lng": float(row["lng"]),
                "status": str(row["status"]),
                "type": str(row["type"]),
            })
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=f"Row {i} is invalid: {exc}. Row data: {row.to_dict()}")

    if not new_mines:
        raise HTTPException(status_code=400, detail="CSV had a valid header but zero data rows — nothing to replace with.")

    previous_count = len(MINES)
    replace_mines(new_mines, persist=persist)

    return {
        "mode": "replace",
        "previous_mine_count": previous_count,
        "new_mine_count": len(new_mines),
        "persisted_to_disk": persist,
        "mines": new_mines,
        "note": (
            "Every endpoint (/api/mines, /api/map/mines, /api/map/zones, /api/predict/prospectivity) "
            "is now using this new set immediately -- no restart needed. "
            "LIMITATION: production/downtime history is separate and NOT included in this upload, "
            "so forecast-dependent tools (rank_high_risk_zones, get_shortfall_risk_for_mine) will "
            "skip these mines until matching rows exist in production.json / equipment_downtime.json."
        ),
    }


@router.get("/template")
def download_template(mode: str = Query("score", pattern="^(score|replace)$")):
    if mode == "score":
        csv_text = "lat,lng\n21.8,80.18\n"
    else:
        csv_text = "id,name,state,lat,lng,status,type\nmine_101,Example Manganese Block,Madhya Pradesh,21.8,80.18,active,existing_mine\n"

    return StreamingResponse(
        io.StringIO(csv_text),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=upload_template_{mode}.csv"},
    )
