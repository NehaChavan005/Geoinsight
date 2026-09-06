"""Layer endpoints returning PNG overlays for Leaflet.

The route only validates input and delegates to ``layer_service``; no
raster/geospatial code lives here.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.schemas import LayerResponse
from app.services import layer_service

router = APIRouter(prefix="/api/v1", tags=["Layers"])

ALLOWED_LAYER_TYPES = set(layer_service.ALLOWED_LAYER_TYPES)


@router.get(
    "/layers/{layer_type}",
    response_model=LayerResponse,
    summary="Get a raster layer as a PNG overlay with geographic bounds",
    description=(
        "Returns a base64-encoded PNG image of the raster clipped to the district "
        "together with its geographic bounds, ready for a Leaflet ImageOverlay. "
        "layer_type must be one of: ndvi, water, rainfall."
    ),
)
def get_layer(
    layer_type: str,
    district: str = Query(..., description="Lowercase district id, e.g. kamrup"),
    month: str = Query(default="", description="Month in YYYY-MM format, e.g. 2026-06"),
):
    if layer_type not in ALLOWED_LAYER_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_LAYER_TYPE",
                "message": f"layer_type must be one of {sorted(ALLOWED_LAYER_TYPES)}",
            },
        )
    payload = layer_service.get_layer_payload(layer_type, district, month)
    return JSONResponse(payload)