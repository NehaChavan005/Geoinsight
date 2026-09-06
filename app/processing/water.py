"""JRC Global Surface Water area calculation.

Water classification
--------------------
The JRC raster band ``occurrence`` holds values from 0 to 100 (percent of
time a pixel was detected as water, 1984-2021).  Pixels with
``occurrence >= water_threshold`` (default 50) are treated as water.

IMPORTANT
---------
JRC Global Surface Water v1.4 represents historical surface-water occurrence
through 2021; the water metric is therefore a historical/reference
water-coverage metric, not a June 2026 observation.

Area convention
---------------
The JRC dataset is nominally 30 m resolution:
``water_area_km2 = water_pixel_count * pixel_area_m2 / 1_000_000`` with the
``pixel_area_m2`` taken from the raster transform when the CRS is projected,
otherwise the nominal ``30 * 30 = 900`` m2/px used for the JRC raster.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from app.processing.clipping import clip_raster_to_boundary

DEFAULT_WATER_THRESHOLD = 50.0
NOMINAL_JRC_PIXEL_AREA_M2 = 900.0


def _pixel_area_m2(meta: dict) -> float:
    """Return pixel area in square metres from the clipped raster metadata."""
    crs = meta.get("crs")
    transform = meta.get("transform")
    if crs is not None and crs.is_projected and transform is not None:
        return float(abs(transform.a) * abs(transform.e))
    return NOMINAL_JRC_PIXEL_AREA_M2


def _classify_water(
    data: NDArray[np.float32],
    valid: NDArray[np.bool_],
    threshold: float,
) -> tuple[int, int]:
    """Return ``(valid_pixel_count, water_pixel_count)`` given a mask."""
    valid_pixels = int(np.count_nonzero(valid))
    if valid_pixels == 0:
        raise ValueError(
            "No valid raster pixels remain inside the boundary; "
            "cannot calculate water area."
        )
    water_pixels = int(np.count_nonzero(valid & (data >= threshold)))
    return valid_pixels, water_pixels


def calculate_water_area(
    water_path: str | Path,
    boundary_path: str | Path,
    water_threshold: float = DEFAULT_WATER_THRESHOLD,
) -> dict:
    """Return water-coverage statistics inside the boundary.

    Parameters
    ----------
    water_path:
        Path to the JRC ``occurrence`` raster
        (``data/water/jrc_water.tif``), values 0-100.
    boundary_path:
        Path to the boundary vector file (GeoJSON, etc.).
    water_threshold:
        Occurrence percentage at or above which a pixel counts as water.

    Returns
    -------
    dict
        ``water_pixels`` (int), ``valid_pixels`` (int),
        ``water_percentage`` (float, 0-100) and ``water_area_km2`` (float).

    Raises
    ------
    FileNotFoundError
        If either file is missing.
    ValueError
        If no valid pixels remain inside the boundary.
    """
    water_path = Path(water_path)
    boundary_path = Path(boundary_path)

    if not water_path.exists():
        raise FileNotFoundError(f"Water raster not found: {water_path}")
    if not boundary_path.exists():
        raise FileNotFoundError(f"Boundary file not found: {boundary_path}")

    clipped, _, meta = clip_raster_to_boundary(water_path, boundary_path)

    data = clipped[0].astype(np.float32)

    valid = np.isfinite(data)
    nodata = meta.get("nodata")
    if nodata is not None:
        valid &= data != nodata

    valid_pixels, water_pixels = _classify_water(data, valid, water_threshold)

    water_percentage = (
        (water_pixels / valid_pixels) * 100.0 if valid_pixels else 0.0
    )
    pixel_area_m2 = _pixel_area_m2(meta)
    water_area_km2 = water_pixels * pixel_area_m2 / 1_000_000.0

    print(
        "JRC Global Surface Water v1.4 represents historical surface-water "
        "occurrence through 2021; this is a historical/reference metric, not "
        "a June 2026 observation."
    )

    return {
        "water_pixels": water_pixels,
        "valid_pixels": valid_pixels,
        "water_percentage": float(water_percentage),
        "water_area_km2": float(water_area_km2),
    }