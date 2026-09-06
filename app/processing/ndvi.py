"""Sentinel-2 NDVI calculation utilities.

Workflow
--------
1. Validate the B4 (Red) and B8 (NIR) paths and the boundary path.
2. Clip both rasters to the boundary with the shared clipping helper.
3. Verify the clipped grids share a CRS and a compatible shape/transform.
4. Compute ``NDVI = (NIR - Red) / (NIR + Red)`` with numpy.
5. Drop nodata, non-finite and out-of-range values, then average.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from app.processing.clipping import clip_raster_to_boundary

# Any NDVI value outside this range is treated as invalid.
NDVI_VALID_RANGE = (-1.0, 1.0)


def validate_raster_path(path: str | Path, label: str) -> Path:
    """Return the path if the raster file exists, else raise."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{label} raster not found: {path}")
    return path


def calculate_ndvi_array(
    red: NDArray[np.floating] | NDArray[np.integer],
    nir: NDArray[np.floating] | NDArray[np.integer],
) -> NDArray[np.float32]:
    """Compute the NDVI array from Red and NIR arrays.

    Parameters
    ----------
    red:
        Red reflectance values (e.g. Sentinel-2 B4).
    nir:
        Near-infrared reflectance values (e.g. Sentinel-2 B8).

    Returns
    -------
    numpy.ndarray
        NDVI per pixel as ``float32``.  Pixels where the denominator is
        zero or non-finite are set to NaN.
    """
    red = np.asarray(red, dtype=np.float32)
    nir = np.asarray(nir, dtype=np.float32)

    denominator = nir + red
    ndvi = np.full(denominator.shape, np.nan, dtype=np.float32)

    valid = np.isfinite(denominator) & (denominator != 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi[valid] = (nir[valid] - red[valid]) / denominator[valid]

    return ndvi


def calculate_ndvi(
    b4_path: str | Path,
    b8_path: str | Path,
    boundary_path: str | Path,
) -> float:
    """Return the mean NDVI inside the boundary.

    Reads the B4 (Red) and B8 (NIR) rasters, clips both to the boundary,
    verifies their grids are compatible, computes per-pixel NDVI and
    returns the mean of the valid pixels as a plain Python ``float``.

    Parameters
    ----------
    b4_path:
        Path to the Sentinel-2 B4 raster.
    b8_path:
        Path to the Sentinel-2 B8 raster.
    boundary_path:
        Path to the boundary vector file (GeoJSON, etc.).

    Returns
    -------
    float
        Mean NDVI across valid pixels inside the boundary.

    Raises
    ------
    FileNotFoundError
        If any input file is missing.
    ValueError
        If the rasters are not geographically compatible, or if no valid
        NDVI pixels remain inside the boundary.
    """
    b4_path = validate_raster_path(b4_path, "B4")
    b8_path = validate_raster_path(b8_path, "B8")

    boundary_path = Path(boundary_path)
    if not boundary_path.exists():
        raise FileNotFoundError(f"Boundary file not found: {boundary_path}")

    red_clipped, _, red_meta = clip_raster_to_boundary(b4_path, boundary_path)
    nir_clipped, _, nir_meta = clip_raster_to_boundary(b8_path, boundary_path)

    if red_meta["crs"] != nir_meta["crs"]:
        raise ValueError(
            "B4 and B8 rasters have different CRS values: "
            f"{red_meta['crs']} vs {nir_meta['crs']}."
        )

    if red_clipped.shape != nir_clipped.shape:
        raise ValueError(
            "B4 and B8 rasters are not grid-compatible after clipping: "
            f"B4 shape={red_clipped.shape} vs B8 shape={nir_clipped.shape}."
        )

    if red_meta["transform"] != nir_meta["transform"]:
        raise ValueError(
            "B4 and B8 rasters have different transforms after clipping; "
            "the grids are not aligned."
        )

    red = red_clipped[0].astype(np.float32)
    nir = nir_clipped[0].astype(np.float32)

    valid = np.isfinite(red) & np.isfinite(nir)

    red_nodata = red_meta.get("nodata")
    nir_nodata = nir_meta.get("nodata")
    if red_nodata is not None:
        valid &= red != red_nodata
    if nir_nodata is not None:
        valid &= nir != nir_nodata

    ndvi = calculate_ndvi_array(red, nir)

    ndvi_valid = ndvi[valid]
    ndvi_valid = ndvi_valid[
        np.isfinite(ndvi_valid)
        & (ndvi_valid >= NDVI_VALID_RANGE[0])
        & (ndvi_valid <= NDVI_VALID_RANGE[1])
    ]

    if ndvi_valid.size == 0:
        raise ValueError(
            "No valid NDVI pixels remain inside the boundary after "
            "masking nodata and out-of-range values."
        )

    return float(np.mean(ndvi_valid))