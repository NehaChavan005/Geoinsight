"""Raster clipping and masking utilities.

Provides both file-based raster clipping utilities used by the geospatial
processing pipeline and array-level helpers used by the backend/tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
from numpy.typing import NDArray

try:
    import rasterio
    from rasterio.mask import mask
except ImportError:  # pragma: no cover
    rasterio = None
    mask = None


def reproject_no_op(geom):
    """Return geometry unchanged."""
    return geom


def get_mask_polygon(district_geometry, raster_crs, boundary_crs):
    """Return district geometry aligned to the raster CRS."""
    from shapely.ops import transform
    import pyproj

    if boundary_crs is None or raster_crs is None:
        return district_geometry

    if str(boundary_crs) == str(raster_crs):
        return district_geometry

    transformer = pyproj.Transformer.from_crs(
        boundary_crs,
        raster_crs,
        always_xy=True,
    )

    def _reproject(x, y, z=None):
        xx, yy = transformer.transform(x, y)
        if z is None:
            return xx, yy
        return xx, yy, z

    return transform(_reproject, district_geometry)


def clip_raster_array(band_array, transform, mask_array, nodata):
    """Clip a 2-D band array using a boolean mask."""
    out = np.full_like(
        band_array,
        nodata,
        dtype=band_array.dtype,
    )
    out[mask_array] = band_array[mask_array]

    return out, transform


def clip_raster(dataset, geometry, nodata=None):
    """Clip an open rasterio dataset to a geometry."""
    if rasterio is None or mask is None:
        raise RuntimeError("rasterio is required to clip rasters.")

    out_image, out_transform = mask(
        dataset,
        [geometry],
        crop=True,
        nodata=nodata,
    )

    return out_image.squeeze(), out_transform


def clip_raster_to_boundary(
    raster_path: str | Path,
    boundary_path: str | Path,
    output_path: Optional[str | Path] = None,
) -> tuple[NDArray, "rasterio.transform.Affine", dict]:
    """Clip a raster to a vector boundary.

    Opens the raster and boundary files, reprojects the boundary to the
    raster CRS, clips the raster, and optionally writes the result.
    """

    if rasterio is None or mask is None:
        raise RuntimeError("rasterio is required to clip rasters.")

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
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with rasterio.open(
            output_path,
            "w",
            **metadata,
        ) as dst:
            dst.write(clipped_data)

    return clipped_data, clipped_transform, metadata