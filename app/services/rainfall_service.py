"""Rainfall service — thin adapter around Member A's CHIRPS processing.

Resolves the district boundary and the CHIRPS dataset folder from
configuration, then delegates the rainfall computation to Member A's
processing function through ``processing_adapter``.

The rainfall metric is `RAINFALL_METRIC` from ``app.config`` (monthly total
in mm).  Member A's processing function is responsible for summing the
CHIRPS raster values; this service does not decide an alternative metric.

Expected data layout: ``data/chirps/{YYYY-MM}/{district_id}/*.tif``
(monthly CHIRPS precipitation composite raster(s)).
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_chirps_path
from app.exceptions import DataNotFoundError
from app.services import processing_adapter
from app.services.boundary_service import (
    get_district_config_or_raise,
    get_district_geometry,
)


def _resolve_data_dir(district_id: str, month: str) -> Path:
    data_dir: Path = get_chirps_path(district_id, month)
    if not data_dir.exists() or not list(data_dir.glob("*.tif")):
        raise DataNotFoundError("CHIRPS", district_id, month)
    return data_dir


def calculate_rainfall(district_id: str, month: str) -> dict:
    """Compute monthly total rainfall (in mm) for the district.

    Returns a plain dict with ``metric``, ``value_mm`` and ``source``,
    produced by Member A's processing function.
    """
    get_district_config_or_raise(district_id)
    geom = get_district_geometry(district_id)
    data_dir = _resolve_data_dir(district_id, month)
    return processing_adapter.call_rainfall(geom, data_dir)