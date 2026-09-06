"""NDVI service — thin adapter around Member A's Sentinel-2 processing.

This service resolves the district boundary and the Sentinel-2 dataset folder
from configuration, then delegates the actual NDVI computation to Member A's
processing function through ``processing_adapter``.  No raster arithmetic
lives here; the NDVI formula belongs to Member A.

Expected data layout: ``data/sentinel2/{YYYY-MM}/{district_id}/B4.tif``
(red band) and ``B8.tif`` (near-infrared band).
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_sentinel_path
from app.exceptions import DataNotFoundError
from app.services import processing_adapter
from app.services.boundary_service import (
    get_district_config_or_raise,
    get_district_geometry,
)


def _resolve_data_dir(district_id: str, month: str) -> Path:
    data_dir: Path = get_sentinel_path(district_id, month)
    if not (data_dir / "B4.tif").exists() or not (data_dir / "B8.tif").exists():
        raise DataNotFoundError("Sentinel-2", district_id, month)
    return data_dir


def calculate_ndvi(district_id: str, month: str) -> dict:
    """Compute average NDVI across the district for a given month.

    Returns a plain dict with ``average_ndvi``, ``pixel_count`` and
    ``source``, produced by Member A's processing function.
    """
    get_district_config_or_raise(district_id)
    geom = get_district_geometry(district_id)
    data_dir = _resolve_data_dir(district_id, month)
    return processing_adapter.call_ndvi(geom, data_dir)