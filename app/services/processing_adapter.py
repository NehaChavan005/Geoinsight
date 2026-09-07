"""Member A ↔ Member B integration adapter.

This module is the **only** place where Member B's service layer may touch
geospatial processing.  Member B never imports raster/geospatial code
directly; every boundary→raster call flows through the functions below to
Member A's contract functions in ``app.processing``.

While Member A has not wired their functions yet, each adapter call raises
``ProcessingNotConnectedError`` and the API reports the dataset as
unavailable — no indicator value is ever fabricated.

Expected Member A function signatures (in ``app.processing/__init__.py``)::

    def calculate_ndvi(boundary_geom, raster_dir) -> dict
        returns {"average_ndvi": float, "pixel_count": int, "source": "Sentinel-2"}

    def calculate_rainfall(boundary_geom, raster_dir) -> dict
        returns {"metric": RAINFALL_METRIC, "value_mm": float, "source": "CHIRPS"}

    def calculate_water(boundary_geom, raster_dir, district_area_km2) -> dict
        returns {"coverage_percent": float, "area_km2": float,
                 "source": "JRC Global Surface Water"}

    def load_layer_raster(layer_type, boundary_geom, raster_dir) -> tuple
        returns (2-D numpy array, bounds), for layer types
        "ndvi" | "water" | "rainfall"

Where:
    boundary_geom  – a shapely geometry in EPSG:4326 (see
                     ``app.services.boundary_service.get_district_geometry``)
    raster_dir     – a ``pathlib.Path`` to the district/month dataset folder
                     (see helper functions in ``app.config``)
"""

from __future__ import annotations

import importlib
import logging

from app.exceptions import ProcessingNotConnectedError

logger = logging.getLogger(__name__)

PROCESSING_MODULE = "app.processing"


def _processing_function(name: str):
    """Import and return a Member A function, or raise not-connected."""
    module = importlib.import_module(PROCESSING_MODULE)
    func = getattr(module, name, None)
    if func is None or not callable(func):
        logger.info(
            "Processing function '%s.%s' not connected; raising ProcessingNotConnectedError",
            PROCESSING_MODULE,
            name,
        )
        raise ProcessingNotConnectedError(f"{PROCESSING_MODULE}.{name}")
    return func


def call_ndvi(boundary_geom, raster_dir) -> dict:
    return _processing_function("calculate_ndvi")(boundary_geom, raster_dir)


def call_rainfall(boundary_geom, raster_dir) -> dict:
    return _processing_function("calculate_rainfall")(boundary_geom, raster_dir)


def call_water(boundary_geom, raster_dir, district_area_km2: float | None = None) -> dict:
    return _processing_function("calculate_water")(
        boundary_geom, raster_dir, district_area_km2
    )


def load_layer(layer_type: str, boundary_geom, raster_dir):
    """Load a clipped raster for overlay rendering: (array, bounds)."""
    return _processing_function("load_layer_raster")(
        layer_type, boundary_geom, raster_dir
    )