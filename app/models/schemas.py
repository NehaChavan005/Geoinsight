"""Pydantic v2 response models for the GeoInsight API."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.config import RAINFALL_METRIC

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


class VegetationResult(BaseModel):
    average_ndvi: Optional[float] = None
    source: str = "Sentinel-2"
    pixel_count: Optional[int] = None


class RainfallResult(BaseModel):
    metric: str = RAINFALL_METRIC
    value_mm: Optional[float] = None
    source: str = "CHIRPS"


class SurfaceWaterResult(BaseModel):
    coverage_percent: Optional[float] = None
    area_km2: Optional[float] = None
    source: str = "JRC Global Surface Water"


class EnvironmentMetadata(BaseModel):
    district_area_km2: Optional[float] = None
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    processing_time_ms: Optional[int] = None
    cached: bool = False


class EnvironmentResponse(BaseModel):
    district: str
    state: str
    month: str
    vegetation: Optional[VegetationResult] = None
    rainfall: Optional[RainfallResult] = None
    surface_water: Optional[SurfaceWaterResult] = None
    metadata: EnvironmentMetadata
    warnings: list[str] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class DistrictInfo(BaseModel):
    id: str
    display_name: str
    state: str


class DistrictListResponse(BaseModel):
    districts: list[DistrictInfo]


class BoundaryResponse(BaseModel):
    district: str
    geojson: dict


class InsightResponse(BaseModel):
    district: str
    month: str
    insight: str


class LayerResponse(BaseModel):
    layer_type: str
    image: str
    bounds: list[list[float]]


class HealthResponse(BaseModel):
    status: str = "ok"
