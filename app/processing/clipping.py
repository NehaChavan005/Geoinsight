"""Raster clipping and masking utilities."""

from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from numpy.typing import NDArray


def clip_raster_to_boundary(
    raster_path: str | Path,
    boundary_path: str | Path,
    output_path: Optional[str | Path] = None,
) -> tuple[NDArray, rasterio.transform.Affine, dict]:
    """Clip a raster to a vector boundary and optionally save the result.

    Opens *raster_path*, reprojects *boundary_path* to the raster's CRS,
    masks the raster to the boundary footprint, and returns the clipped
    array together with its updated transform and metadata dictionary.

    Parameters
    ----------
    raster_path:
        Path to the input raster file (GeoTIFF or any rasterio-supported
        format).
    boundary_path:
        Path to a vector file (GeoJSON, Shapefile, etc.) that defines the
        clipping region.  Must contain at least one geometry.
    output_path:
        If provided the clipped raster is written to this path.  Parent
        directories are created automatically.

    Returns
    -------
    clipped_data : numpy.ndarray
        The masked raster array with the boundary footprint applied.
    clipped_transform : rasterio.transform.Affine
        Affine transform of the cropped output.
    metadata : dict
        Updated raster metadata (crs, dtype, nodata, shape, etc.).

    Raises
    ------
    FileNotFoundError
        If either *raster_path* or *boundary_path* does not exist.
    ValueError
        If the boundary file contains no features.
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

        boundary_reprojected = boundary_gdf.to_crs(raster_crs)
        geometries = boundary_reprojected.geometry.tolist()

        clipped_data, clipped_transform = mask(
            src,
            geometries,
            crop=True,
            nodata=src.nodata,
        )

        metadata = src.meta.copy()
        metadata.update(
            {
                "driver": "GTiff",
                "height": clipped_data.shape[1],
                "width": clipped_data.shape[2],
                "transform": clipped_transform,
                "crs": raster_crs,
            }
        )

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(output_path, "w", **metadata) as dst:
            dst.write(clipped_data)

    return clipped_data, clipped_transform, metadata
