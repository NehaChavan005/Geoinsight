"""FastAPI application entrypoint.

Member B owns this file: app factory, OpenAPI metadata, CORS, error handling
and router registration.  It contains no geospatial processing.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import districts, environment, insight, layers
from app.exceptions import (
    DataNotFoundError,
    DistrictNotFoundError,
    InvalidMonthError,
    ProcessingNotConnectedError,
    ProcessingError,
)
from app.models.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="GeoInsight API",
    description=(
        "Geospatial environmental intelligence API for district-level analysis. "
        "Computes average NDVI (Sentinel-2), monthly total rainfall in mm (CHIRPS, "
        "metric total_mm), and surface-water coverage (JRC Global Surface Water) for "
        "any registered district and YYYY-MM month."
    ),
    version="1.0.0",
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "Health", "description": "Liveness checks."},
        {"name": "Districts", "description": "District registry and boundary GeoJSON."},
        {"name": "Environment", "description": "NDVI, rainfall and surface-water indicators."},
        {"name": "Layers", "description": "Raster overlays (PNG + bounds) for the web map."},
        {"name": "Insight", "description": "AI-generated, data-grounded insights."},
    ],
)


@app.exception_handler(DistrictNotFoundError)
async def district_not_found_handler(request: Request, exc: DistrictNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "DISTRICT_NOT_FOUND", "message": str(exc)}},
    )


@app.exception_handler(InvalidMonthError)
async def invalid_month_handler(request: Request, exc: InvalidMonthError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_MONTH_FORMAT",
                "message": "Month must use YYYY-MM format.",
            }
        },
    )


@app.exception_handler(DataNotFoundError)
async def data_not_found_handler(request: Request, exc: DataNotFoundError):
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "DATA_NOT_FOUND", "message": str(exc)}},
    )


@app.exception_handler(ProcessingNotConnectedError)
async def processing_not_connected_handler(
    request: Request, exc: ProcessingNotConnectedError
):
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "PROCESSING_NOT_CONNECTED",
                "message": str(exc),
            }
        },
    )


@app.exception_handler(ProcessingError)
async def processing_error_handler(request: Request, exc: ProcessingError):
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "PROCESSING_ERROR", "message": str(exc)}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": detail["code"], "message": detail["message"]}},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(detail)}},
    )


_default_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

_extra_origins = [
    o.strip()
    for o in os.environ.get(
        "GEOINSIGHT_CORS_ORIGINS", ""
    ).split(",")
    if o.strip()
]

origins = _default_origins + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(districts.router)
app.include_router(environment.router)
app.include_router(layers.router)
app.include_router(insight.router)


@app.get(
    "/healthz",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Liveness check",
    description="Returns status ok. Does not depend on any geospatial datasets.",
)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok")