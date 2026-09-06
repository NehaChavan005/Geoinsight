"""Surface-water service — thin adapter around Member A's JRC processing.

Resolves the district boundary, district area and the JRC dataset folder
from configuration, then delegates the water-class processing to Member A's
function through ``processing_adapter``.  The JRC water-class thresholds,
pixel-area conversion and percentage math belong to Member A.

Expected data layout: ``data/jrc_water/{district_id}/*.tif``
(JRC Global Surface Water classification raster(s), not month-specific).
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_water_path
from app.exceptions import DataNotFoundError
from app.services import processing_adapter
from app.services.boundary_service import (
    get_district_area_km2,
    get_district_config_or_raise,
    get_district_geometry,
)


def _resolve_data_dir(district_id: str) -> Path:
    data_dir = get_water_path(district_id)
    if not data_dir.exists() or not list(data_dir.glob("*.tif")):
        raise DataNotFoundError("JRC Global Surface Water", district_id)
    return data_dir


def calculate_water_coverage(district_id: str) -> dict:
    """Compute surface-water coverage for the district.

    Returns a plain dict with ``coverage_percent``, ``area_km2`` and
    ``source``, produced by Member A's processing function.
    """
    get_district_config_or_raise(district_id)
    geom = get_district_geometry(district_id)
    district_area_km2 = get_district_area_km2(district_id)
    data_dir = _resolve_data_dir(district_id)
    return processing_adapter.call_water(geom, data_dir, district_area_km2)