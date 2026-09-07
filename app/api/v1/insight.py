"""LLM insight endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.schemas import InsightResponse
from app.services.environment_service import get_district_meta, validate_month, get_or_calculate_environment
from app.services.insight_service import generate_insight

router = APIRouter(prefix="/api/v1", tags=["Insight"])


@router.get(
    "/insight",
    response_model=InsightResponse,
    summary="Generate an AI environmental insight",
    description=(
        "Retrieves the computed environmental indicators for a district/month "
        "(from cache when available) and returns a short, data-grounded summary. "
        "Uses a local Ollama model when reachable; otherwise falls back to a "
        "deterministic template summary. The text only restates computed indicators."
    ),
)
def get_insight(
    district: str = Query(..., description="Lowercase district id, e.g. kamrup"),
    month: str = Query(..., description="Month in YYYY-MM format, e.g. 2026-06"),
) -> InsightResponse:
    meta = get_district_meta(district)
    validate_month(month)
    env_result = get_or_calculate_environment(district, month)

    indicators = {
        "vegetation": env_result.get("vegetation"),
        "rainfall": env_result.get("rainfall"),
        "surface_water": env_result.get("surface_water"),
    }
    generated = generate_insight(
        district=env_result["district"],
        state=env_result["state"],
        month=month,
        indicators=indicators,
    )
    return InsightResponse(
        district=meta["display_name"],
        month=month,
        insight=generated["insight"],
    )