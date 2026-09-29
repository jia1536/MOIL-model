from typing import Optional

from fastapi import APIRouter, HTTPException

from .state_analysis import (
    compare_states,
    compare_countries_report,
    depletion_report,
)

router = APIRouter()


def _split(value: Optional[str]):
    if not value:
        return None
    names = [v.strip() for v in value.split(",") if v.strip()]
    return names or None


@router.get("/compare/states")
def api_compare_states(states: Optional[str] = None):
    result = compare_states(_split(states))
    if states and not result["states"]:
        raise HTTPException(status_code=404, detail=f"No matching states: {result['not_found']}")
    return result


@router.get("/compare/countries")
def api_compare_countries(countries: Optional[str] = None):
    result = compare_countries_report(_split(countries))
    if countries and not result["countries"]:
        raise HTTPException(status_code=404, detail="No matching countries in the world table")
    return result


@router.get("/depletion")
def api_depletion(state: Optional[str] = None):
    result = depletion_report(state)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No reserve data for state '{state}'")
    return result
