"""Integration bridge between backend services and Member A processing.

Backend contract (Member B)
---------------------------
The service layer calls exactly these functions (via ``app.services.
processing_adapter``)::

    calculate_ndvi(boundary_geom, raster_dir) -> dict
    calculate_rainfall(boundary_geom, raster_dir) -> dict
    calculate_water(boundary_geom, raster_dir, district_area_km2) -> dict
    load_layer_raster(layer_type, boundary_geom, raster_dir) -> (array, bounds)

Each wrapper resolves the district boundary from the registered configuration,
picks the actual on-disk dataset raster deterministically (see ``app.config``
for the dataset registry) and delegates the real computation to Member A's
processing functions.  No indicator value is ever fabricated: missing data
raises ``DataNotFoundError`` so the API reports the dataset as unavailable.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from app.config import (
    CHIRPS_DISTRICT_RASTER,
    JRC_DISTRICT_RASTER,
    SENTINEL2_BAND_NAME_PAIRS,
    SUPPORTED_DISTRICTS,
    get_district_config,
)
from app.exceptions import DataNotFoundError, ProcessingError
from app.processing.clipping import clip_raster_to_boundary
from app.processing.ndvi import calculate_ndvi as _calculate_ndvi
from app.processing.ndvi import calculate_ndvi_array
from app.processing.rainfall import calculate_monthly_rainfall
from app.processing.water import calculate_water_area


def _find_district_id(boundary_geom) -> str:
    """Return the registered district whose boundary matches ``boundary_geom``.

    Derives the district from the geometry instead of hardcoding a name, so the
    bridge keeps working as districts are added to the registry.
    """
    if (
        boundary_geom is None
        or not hasattr(boundary_geom, "is_empty")
        or boundary_geom.is_empty
    ):
        raise DataNotFoundError("Boundary")

    for district_id, config in SUPPORTED_DISTRICTS.items():
        boundary_path = Path(config["boundary_path"])
        if not boundary_path.exists():
            continue
        boundary_gdf = gpd.read_file(boundary_path)
        if boundary_gdf.empty:
            continue
        if boundary_geom.intersects(boundary_gdf.geometry.iloc[0]):
            return district_id

    raise DataNotFoundError("Boundary")


def _district_context(boundary_geom) -> tuple[str, Path]:
    """Return ``(district_id, boundary_path)`` for the given geometry."""
    district_id = _find_district_id(boundary_geom)
    config = get_district_config(district_id)
    if config is None:
        raise DataNotFoundError("Boundary")

    boundary_path = Path(config["boundary_path"])
    if not boundary_path.exists():
        raise DataNotFoundError("Boundary", district_id)
    return district_id, boundary_path


def _prefer_named_raster(
    raster_dir: Path,
    district_id: str,
    dataset_raster: Path,
    dataset_name: str,
) -> Path:
    """Select the district-scope raster file inside ``raster_dir``.

    Prefers the exact dataset filename registered in ``app.config`` so the pick
    is deterministic even when a state-wide sibling raster shares the folder;
    falls back to an existing TIFF only when the registered file is absent.
    """
    candidate = raster_dir / dataset_raster.name
    if candidate.is_file():
        return candidate

    raster_files = sorted(raster_dir.glob("*.tif"))
    for raster_path in raster_files:
        if raster_path.is_file():
            return raster_path

    raise DataNotFoundError(dataset_name, district_id)


def _bounds_from_meta(meta: dict):
    """Convert clipped-raster metadata into a ``rasterio`` BoundingBox."""
    from rasterio.coords import BoundingBox
    from rasterio.transform import array_bounds

    left, bottom, right, top = array_bounds(
        meta["height"], meta["width"], meta["transform"]
    )
    return BoundingBox(left=left, bottom=bottom, right=right, top=top)


def _resolve_ndvi_band_files(raster_dir: Path, district_id: str) -> tuple[Path, Path]:
    """Locate the Sentinel-2 red (B4) and nir (B8) bands inside ``raster_dir``.

    Accepts both Member A's export naming (``sentinel2_B04_june2026.tif`` /
    ``sentinel2_B08_june2026.tif``) and the legacy ``B4.tif``/``B8.tif`` pairs,
    so the dataset folder is used as-is without duplicating large TIFFs.
    """
    for red_name, nir_name in SENTINEL2_BAND_NAME_PAIRS:
        red, nir = raster_dir / red_name, raster_dir / nir_name
        if red.is_file() and nir.is_file():
            return red, nir
    raise DataNotFoundError("Sentinel-2", district_id)


def calculate_ndvi(boundary_geom, raster_dir) -> dict:
    """Backend-compatible wrapper for Member A's NDVI calculation."""
    raster_dir = Path(raster_dir)
    district_id, boundary_path = _district_context(boundary_geom)

    b4_path, b8_path = _resolve_ndvi_band_files(raster_dir, district_id)

    value = _calculate_ndvi(b4_path, b8_path, boundary_path)

    return {
        "average_ndvi": float(value),
        "pixel_count": None,
        "source": "Sentinel-2",
    }


def calculate_rainfall(boundary_geom, raster_dir) -> dict:
    """Backend-compatible wrapper for Member A's rainfall calculation."""
    raster_dir = Path(raster_dir)
    district_id, boundary_path = _district_context(boundary_geom)

    raster_path = _prefer_named_raster(
        raster_dir, district_id, CHIRPS_DISTRICT_RASTER, "CHIRPS"
    )
    value = calculate_monthly_rainfall(raster_path, boundary_path)

    return {
        "metric": "total_mm",
        "value_mm": float(value),
        "source": "CHIRPS",
    }


def calculate_water(
    boundary_geom,
    raster_dir,
    district_area_km2=None,
) -> dict:
    """Backend-compatible wrapper for Member A's water calculation."""
    raster_dir = Path(raster_dir)
    district_id, boundary_path = _district_context(boundary_geom)

    raster_path = _prefer_named_raster(
        raster_dir,
        district_id,
        JRC_DISTRICT_RASTER,
        "JRC Global Surface Water",
    )
    result = calculate_water_area(raster_path, boundary_path)

    return {
        "coverage_percent": result["water_percentage"],
        "area_km2": result["water_area_km2"],
        "source": "JRC Global Surface Water",
    }


def _load_ndvi_layer(boundary_path: Path, raster_dir: Path, district_id: str):
    """Return the clipped NDVI array and its geographic bounds."""
    b4_path, b8_path = _resolve_ndvi_band_files(raster_dir, district_id)

    red_clipped, _, red_meta = clip_raster_to_boundary(b4_path, boundary_path)
    nir_clipped, _, nir_meta = clip_raster_to_boundary(b8_path, boundary_path)

    if red_clipped.shape != nir_clipped.shape or (
        red_meta["transform"] != nir_meta["transform"]
    ):
        raise ProcessingError(
            "Sentinel-2 B4 and B8 grids are not compatible after clipping.",
            dataset="sentinel2",
        )

    ndvi_array = calculate_ndvi_array(red_clipped[0], nir_clipped[0])
    return ndvi_array, _bounds_from_meta(red_meta)


def load_layer_raster(layer_type: str, boundary_geom, raster_dir):
    """Load a clipped single-band raster for overlay rendering.

    Returns ``(2-D numpy array, rasterio BoundingBox)`` in the raster CRS
    (EPSG:4326 for all current datasets) ready for a Leaflet ``ImageOverlay``.

    Parameters
    ----------
    layer_type:
        One of ``"ndvi"``, ``"rainfall"`` or ``"water"``.
    boundary_geom:
        Shapely district geometry in EPSG:4326.
    raster_dir:
        District/month dataset directory resolved via ``app.config``.

    Returns
    -------
    tuple
        ``(array, bounds)`` where ``array`` is the clipped 2-D band and
        ``bounds`` exposes ``left``/``bottom``/``right``/``top``.
    """
    raster_dir = Path(raster_dir)
    district_id, boundary_path = _district_context(boundary_geom)

    if layer_type == "ndvi":
        return _load_ndvi_layer(boundary_path, raster_dir, district_id)

    if layer_type == "rainfall":
        raster_path = _prefer_named_raster(
            raster_dir, district_id, CHIRPS_DISTRICT_RASTER, "CHIRPS"
        )
    elif layer_type == "water":
        raster_path = _prefer_named_raster(
            raster_dir,
            district_id,
            JRC_DISTRICT_RASTER,
            "JRC Global Surface Water",
        )
    else:
        raise DataNotFoundError(layer_type, district_id)

    clipped, _, meta = clip_raster_to_boundary(raster_path, boundary_path)
    return clipped[0], _bounds_from_meta(meta)