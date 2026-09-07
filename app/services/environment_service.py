"""Internal orchestration for the environment endpoint.

Coordinates boundary, NDVI, rainfall and surface-water services, assembling
the standardized ``EnvironmentResponse``.  Each dataset is handled
independently so one missing dataset yields a ``None`` indicator plus a
warning instead of failing the whole request.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone

from app.config import SUPPORTED_DISTRICTS
from app.exceptions import (
    DataNotFoundError,
    DistrictNotFoundError,
    InvalidMonthError,
    ProcessingNotConnectedError,
)
from app.models.schemas import EnvironmentMetadata, EnvironmentResponse
from app.services import (
    boundary_service,
    ndvi_service,
    rainfall_service,
    water_service,
)

logger = logging.getLogger(__name__)

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def validate_month(month: str) -> str:
    if not isinstance(month, str) or not MONTH_RE.match(month):
        raise InvalidMonthError(month)
    return month


def get_district_meta(district_id: str) -> dict:
    config = SUPPORTED_DISTRICTS.get(district_id)
    if config is None:
        raise DistrictNotFoundError(district_id)
    return {
        "id": district_id,
        "display_name": config["display_name"],
        "state": config["state"],
    }


def calculate_environment(district_id: str, month: str) -> dict:
    """Compute all indicators for a district/month and return a plain dict."""
    start = time.perf_counter()
    get_district_meta(district_id)
    validate_month(month)

    district_area_km2 = None
    try:
        district_area_km2 = boundary_service.get_district_area_km2(district_id)
    except (DataNotFoundError, DistrictNotFoundError) as exc:
        logger.warning("District area unavailable: %s", exc)

    warnings: list[str] = []
    vegetation = None
    rainfall = None
    surface_water = None

    INDICATOR_ERRORS = (DataNotFoundError, DistrictNotFoundError, ProcessingNotConnectedError)

    try:
        vegetation = ndvi_service.calculate_ndvi(district_id, month)
    except INDICATOR_ERRORS as exc:
        warnings.append(
            "Sentinel-2 dataset is unavailable for this district/month."
            + (
                " (Geospatial processing is not connected yet.)"
                if isinstance(exc, ProcessingNotConnectedError)
                else ""
            )
        )
        logger.warning("NDVI unavailable: %s", exc)

    try:
        rainfall = rainfall_service.calculate_rainfall(district_id, month)
    except INDICATOR_ERRORS as exc:
        warnings.append(
            "CHIRPS rainfall dataset is unavailable for this district/month."
            + (
                " (Geospatial processing is not connected yet.)"
                if isinstance(exc, ProcessingNotConnectedError)
                else ""
            )
        )
        logger.warning("Rainfall unavailable: %s", exc)

    try:
        surface_water = water_service.calculate_water_coverage(district_id)
    except INDICATOR_ERRORS as exc:
        warnings.append(
            "JRC Global Surface Water data is unavailable for the requested district."
            + (
                " (Geospatial processing is not connected yet.)"
                if isinstance(exc, ProcessingNotConnectedError)
                else ""
            )
        )
        logger.warning("Surface water unavailable: %s", exc)

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    response = EnvironmentResponse(
        district=SUPPORTED_DISTRICTS[district_id]["display_name"],
        state=SUPPORTED_DISTRICTS[district_id]["state"],
        month=month,
        vegetation=vegetation,
        rainfall=rainfall,
        surface_water=surface_water,
        metadata=EnvironmentMetadata(
            district_area_km2=district_area_km2,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            processing_time_ms=elapsed_ms,
            cached=False,
        ),
        warnings=warnings,
    )
    return response.model_dump()


def get_or_calculate_environment(
    district_id: str,
    month: str,
    cache=None,
) -> dict:
    """Fetch from cache or compute, marking ``cached`` accordingly.

    ``cache`` is injectable for tests; defaults to the module-level manager.
    """
    if cache is None:
        from app.cache.cache_manager import cache_manager as default_cache

        cache = default_cache

    cached = cache.get_cached(district_id, month)
    if cached is not None:
        cached["metadata"]["cached"] = True
        logger.info("Cache hit: district=%s month=%s", district_id, month)
        return cached

    logger.info("Cache miss: district=%s month=%s", district_id, month)
    result = calculate_environment(district_id, month)
    logger.info("Calculating environmental indicators for district=%s month=%s", district_id, month)
    cache.set_cached(district_id, month, result)
    return result