"""District listing and boundary endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import SUPPORTED_DISTRICTS
from app.models.schemas import DistrictListResponse
from app.services.boundary_service import get_district_boundary

router = APIRouter(prefix="/api/v1", tags=["Districts"])


@router.get(
    "/districts",
    response_model=DistrictListResponse,
    summary="List supported districts",
    description="Returns every district registered in the configuration registry.",
)
def list_districts() -> DistrictListResponse:
    districts = [
        {
            "id": district_id,
            "display_name": cfg["display_name"],
            "state": cfg["state"],
        }
        for district_id, cfg in SUPPORTED_DISTRICTS.items()
    ]
    return DistrictListResponse(districts=districts)


@router.get(
    "/districts/{district_id}/boundary",
    summary="Get district boundary GeoJSON",
    description="Raw GeoJSON Feature for the district, suitable for a Leaflet GeoJSON layer.",
)
def district_boundary(district_id: str) -> dict:
    return get_district_boundary(district_id)