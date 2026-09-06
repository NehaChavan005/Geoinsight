"""CHIRPS monthly rainfall calculation.

Metric
------
June 2026 rainfall depth (mm) = zonal MEAN of the CHIRPS June monthly-total
pixels (sum of daily ``precipitation`` values) across the district boundary.

The exported raster (e.g. ``data/rainfall/chirps_june2026.tif`` for Kamrup or
``data/rainfall/chirps_june2026_assam.tif`` for the state-wide Assam run)
already holds the sum of the daily ``precipitation`` bands for
2026-06-01 .. 2026-06-30, i.e. the June monthly total in mm per pixel.  The
district rainfall-depth figure is therefore the ZONAL MEAN of those
monthly-total pixels, obtained with the shared ``zonal_mean`` helper.
Summing the pixels would return mm times the pixel count (area), which is
not a rainfall-depth indicator.
"""

from __future__ import annotations

from pathlib import Path

from app.processing.zonal_stats import zonal_mean

MONTHLY_RAINFALL_DEFINITION = (
    "June 2026 rainfall depth (mm) = mean of the CHIRPS June monthly-total "
    "pixels (sum of daily precipitation values) across the district boundary."
)


def calculate_monthly_rainfall(
    rainfall_path: str | Path,
    boundary_path: str | Path,
) -> float:
    """Return mean June 2026 rainfall (mm) inside the boundary.

    Parameters
    ----------
    rainfall_path:
        Path to the CHIRPS June 2026 sum raster
        (``data/rainfall/chirps_june2026.tif``), where each pixel already
        holds the June monthly total in mm.
    boundary_path:
        Path to the boundary vector file (GeoJSON, etc.).

    Returns
    -------
    float
        Mean monthly rainfall in millimetres over the boundary.

    Raises
    ------
    FileNotFoundError
        If either file is missing.
    ValueError
        If no valid pixels are available inside the boundary.
    """
    rainfall_path = Path(rainfall_path)
    boundary_path = Path(boundary_path)

    if not rainfall_path.exists():
        raise FileNotFoundError(f"Rainfall raster not found: {rainfall_path}")
    if not boundary_path.exists():
        raise FileNotFoundError(f"Boundary file not found: {boundary_path}")

    mean_mm = zonal_mean(rainfall_path, boundary_path)

    print(MONTHLY_RAINFALL_DEFINITION)

    return float(mean_mm)