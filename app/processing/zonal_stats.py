"""Zonal statistics helpers for raster processing and backend tests.

Provides:
- File-based zonal statistics using rasterstats.
- Pure NumPy helpers for unit testing and array-level calculations.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# Optional geospatial dependencies for file-based statistics.
try:
    import geopandas as gpd
    import rasterio
    from rasterstats import zonal_stats
except ImportError:  # pragma: no cover
    gpd = None
    rasterio = None
    zonal_stats = None


# ---------------------------------------------------------------------------
# Pure NumPy helpers
# ---------------------------------------------------------------------------

def pixel_count_valid(arr, nodata=None, mask=None):
    """Count valid (non-nodata, finite) pixels in a 2-D array."""
    valid = np.isfinite(arr)

    if nodata is not None:
        valid &= arr != nodata

    if mask is not None:
        valid &= mask

    return int(valid.sum())


def compute_mean(arr, nodata=None, mask=None):
    """Return mean of valid pixels, or None when no valid pixels exist."""
    valid_arr = np.where(
        np.isfinite(arr),
        arr,
        np.nan,
    )

    if nodata is not None:
        valid_arr = np.where(
            arr == nodata,
            np.nan,
            valid_arr,
        )

    if mask is not None:
        valid_arr = np.where(
            mask,
            valid_arr,
            np.nan,
        )

    vals = valid_arr[~np.isnan(valid_arr)]

    if vals.size == 0:
        return None

    return float(np.mean(vals))


def compute_sum(arr, nodata=None, mask=None):
    """Return sum of valid pixels, or None when no valid pixels exist."""
    valid_arr = np.where(
        np.isfinite(arr),
        arr,
        np.nan,
    )

    if nodata is not None:
        valid_arr = np.where(
            arr == nodata,
            np.nan,
            valid_arr,
        )

    if mask is not None:
        valid_arr = np.where(
            mask,
            valid_arr,
            np.nan,
        )

    vals = valid_arr[~np.isnan(valid_arr)]

    if vals.size == 0:
        return None

    return float(np.sum(vals))


def pixel_area_km2(res_m=10.0):
    """Return area in km² covered by one square pixel."""
    res_km = res_m / 1000.0
    return res_km * res_km


def water_coverage_stats(
    count_water_pixels,
    total_water_pixels,
    total_area_km2,
    res_m=10.0,
):
    """Convert water pixel counts to coverage percentage and area."""
    area_km2 = count_water_pixels * pixel_area_km2(res_m)

    if total_area_km2 is None or total_area_km2 <= 0:
        coverage_percent = 0.0
    else:
        coverage_percent = (
            area_km2 / total_area_km2
        ) * 100.0

    return coverage_percent, area_km2


# ---------------------------------------------------------------------------
# File-based zonal statistics
# ---------------------------------------------------------------------------

def _load_reprojected_boundary(
    raster_path: str | Path,
    boundary_path: str | Path,
):
    """Read boundary and reproject it to the raster CRS."""
    if gpd is None or rasterio is None:
        raise RuntimeError(
            "geopandas and rasterio are required for file-based "
            "zonal statistics."
        )

    raster_path = Path(raster_path)
    boundary_path = Path(boundary_path)

    if not raster_path.exists():
        raise FileNotFoundError(
            f"Raster file not found: {raster_path}"
        )

    if not boundary_path.exists():
        raise FileNotFoundError(
            f"Boundary file not found: {boundary_path}"
        )

    boundary_gdf = gpd.read_file(boundary_path)

    if boundary_gdf.empty:
        raise ValueError(
            f"Boundary file contains no features: {boundary_path}"
        )

    with rasterio.open(raster_path) as src:
        raster_crs = src.crs

    if (
        boundary_gdf.crs is not None
        and raster_crs is not None
    ):
        boundary_gdf = boundary_gdf.to_crs(raster_crs)

    return boundary_gdf


def _single_zonal_stats(
    raster_path: str | Path,
    boundary_path: str | Path,
    stats: list[str],
) -> dict:
    """Compute requested zonal statistics for one boundary feature."""
    if zonal_stats is None:
        raise RuntimeError(
            "rasterstats is required for file-based zonal statistics."
        )

    boundary_gdf = _load_reprojected_boundary(
        raster_path,
        boundary_path,
    )

    if len(boundary_gdf) != 1:
        raise ValueError(
            "Expected exactly one boundary feature, "
            f"found {len(boundary_gdf)}."
        )

    results = zonal_stats(
        boundary_gdf,
        raster_path,
        stats=stats,
        nodata=None,
        all_touched=False,
        raster_out=False,
    )

    return results[0]


def zonal_mean(
    raster_path: str | Path,
    boundary_path: str | Path,
) -> float:
    """Return mean valid raster value inside the boundary."""
    stats = _single_zonal_stats(
        raster_path,
        boundary_path,
        ["mean"],
    )

    mean = stats.get("mean")

    if mean is None:
        raise ValueError(
            "No valid pixels available inside the boundary; "
            "cannot compute zonal mean."
        )

    return float(mean)


def zonal_sum(
    raster_path: str | Path,
    boundary_path: str | Path,
) -> float:
    """Return sum of valid raster values inside the boundary."""
    stats = _single_zonal_stats(
        raster_path,
        boundary_path,
        ["sum"],
    )

    total = stats.get("sum")

    if total is None:
        raise ValueError(
            "No valid pixels available inside the boundary; "
            "cannot compute zonal sum."
        )

    return float(total)


def zonal_pixel_count(
    raster_path: str | Path,
    boundary_path: str | Path,
) -> int:
    """Return count of valid raster pixels inside the boundary."""
    stats = _single_zonal_stats(
        raster_path,
        boundary_path,
        ["count"],
    )

    count = stats.get("count")

    if count is None:
        raise ValueError(
            "No valid pixels available inside the boundary; "
            "cannot count pixels."
        )

    return int(count)