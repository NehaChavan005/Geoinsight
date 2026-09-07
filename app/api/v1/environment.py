"""Main environment endpoint returning all computed indicators."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.schemas import EnvironmentResponse
from app.services.environment_service import get_or_calculate_environment

router = APIRouter(prefix="/api/v1", tags=["Environment"])


@router.get(
    "/environment",
    response_model=EnvironmentResponse,
    summary="Environmental indicators for a district and month",
    description=(
        "Computes (or returns cached) average NDVI from Sentinel-2, monthly total rainfall "
        "from CHIRPS (metric: total_mm), and surface-water coverage from JRC Global Surface "
        "Water for the given district and YYYY-MM month. If an individual dataset is missing, "
        "the corresponding field is null and a warning is added to the response."
    ),
)
def get_environment(
    district: str = Query(..., description="Lowercase district id, e.g. kamrup"),
    month: str = Query(..., description="Month in YYYY-MM format, e.g. 2026-06"),
) -> dict:
    return get_or_calculate_environment(district, month)