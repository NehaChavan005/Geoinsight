"""Shared zonal statistics helpers built on rasterstats."""

from pathlib import Path

import geopandas as gpd
import rasterio
from rasterstats import zonal_stats


def _load_reprojected_boundary(
    raster_path: str | Path, boundary_path: str | Path
) -> gpd.GeoDataFrame:
    """Read the boundary and reproject it to the raster's CRS.

    Raises
    ------
    FileNotFoundError
        If either file does not exist.
    ValueError
        If the boundary contains no features.
    """
    raster_path = Path(raster_path)
    boundary_path = Path(boundary_path)

    if not raster_path.exists():
        raise FileNotFoundError(f"Raster file not found: {raster_path}")
    if not boundary_path.exists():
        raise FileNotFoundError(f"Boundary file not found: {boundary_path}")

    boundary_gdf = gpd.read_file(boundary_path)
    if boundary_gdf.empty:
        raise ValueError(
            f"Boundary file contains no features: {boundary_path}"
        )

    with rasterio.open(raster_path) as src:
        raster_crs = src.crs

    if boundary_gdf.crs is not None and raster_crs is not None:
        boundary_gdf = boundary_gdf.to_crs(raster_crs)

    return boundary_gdf


def _single_zonal_stats(
    raster_path: str | Path, boundary_path: str | Path, stats: list[str]
) -> dict:
    """Compute the requested zonal stats over the boundary.

    Assigns exactly one feature so a single result dictionary is returned.
    """
    boundary_gdf = _load_reprojected_boundary(raster_path, boundary_path)
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


def zonal_mean(raster_path: str | Path, boundary_path: str | Path) -> float:
    """Return the mean of valid raster pixels inside the boundary.

    Nodata pixels are excluded by rasterstats.  Raises a clear error if
    no valid pixels are available (empty result or missing ``mean``).

    Parameters
    ----------
    raster_path:
        Path to the input raster file.
    boundary_path:
        Path to the boundary vector file (GeoJSON, etc.).

    Returns
    -------
    float
        Mean raster value within the boundary.

    Raises
    ------
    ValueError
        If no valid pixels are available inside the boundary.
    """
    stats = _single_zonal_stats(raster_path, boundary_path, ["mean"])
    mean = stats.get("mean")
    if mean is None:
        raise ValueError(
            "No valid pixels available inside the boundary; "
            "cannot compute zonal mean."
        )
    return float(mean)


def zonal_sum(raster_path: str | Path, boundary_path: str | Path) -> float:
    """Return the sum of valid raster pixel values inside the boundary.

    Nodata pixels are excluded by rasterstats.  Raises a clear error if
    no valid pixels are available (empty result or missing ``sum``).

    Parameters
    ----------
    raster_path:
        Path to the input raster file.
    boundary_path:
        Path to the boundary vector file (GeoJSON, etc.).

    Returns
    -------
    float
        Sum of valid raster pixel values within the boundary.

    Raises
    ------
    ValueError
        If no valid pixels are available inside the boundary.
    """
    stats = _single_zonal_stats(raster_path, boundary_path, ["sum"])
    total = stats.get("sum")
    if total is None:
        raise ValueError(
            "No valid pixels available inside the boundary; "
            "cannot compute zonal sum."
        )
    return float(total)


def zonal_pixel_count(raster_path: str | Path, boundary_path: str | Path) -> int:
    """Return the count of valid raster pixels inside the boundary.

    Nodata pixels are excluded by rasterstats.  Returns an integer count.

    Parameters
    ----------
    raster_path:
        Path to the input raster file.
    boundary_path:
        Path to the boundary vector file (GeoJSON, etc.).

    Returns
    -------
    int
        Number of valid raster pixels within the boundary.

    Raises
    ------
    ValueError
        If no valid pixels are available inside the boundary.
    """
    stats = _single_zonal_stats(raster_path, boundary_path, ["count"])
    count = stats.get("count")
    if count is None:
        raise ValueError(
            "No valid pixels available inside the boundary; "
            "cannot count pixels."
        )
    return int(count)
