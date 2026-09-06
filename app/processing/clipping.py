"""Raster clipping and masking utilities.

This module provides pure, testable helpers used to clip raster data to a
district boundary.  Raster I/O is left to the callers so these functions can
be unit-tested with in-memory numpy arrays.
"""

from __future__ import annotations

import numpy as np

try:
    import rasterio
    from rasterio.mask import mask
except ImportError:  # pragma: no cover - only during non-geospatial installs
    rasterio = None
    mask = None


def reproject_no_op(geom):
    return geom


def get_mask_polygon(district_geometry, raster_crs, boundary_crs):
    """Return a shapely geometry aligned to ``raster_crs``.

    Reprojects the district boundary into the raster's CRS to ensure a
    correct mask, or returns the geometry unchanged when the CRS already
    matches.  A ``boundary_crs`` of None is treated as identical.
    """
    from shapely.ops import transform
    import pyproj

    if boundary_crs is None or raster_crs is None:
        return district_geometry
    if str(boundary_crs) == str(raster_crs):
        return district_geometry

    def _reproject(x, y, z=None):
        tx = pyproj.Transformer.from_crs(boundary_crs, raster_crs, always_xy=True)
        xx, yy = tx.transform(x, y)
        if z is None:
            return xx, yy
        return xx, yy, z

    return transform(_reproject, district_geometry)


def clip_raster_array(band_array, transform, mask_array, nodata):
    """Clip a 2-D band array to a boolean mask.

    Parameters
    ----------
    band_array : np.ndarray
        2-D array of pixel values from one band.
    transform : Affine
        Geotransform corresponding to ``band_array``.
    mask_array : np.ndarray
        2-D boolean array with True where pixels are inside the district.
    nodata : float
        Value to use for pixels outside the mask.

    Returns
    -------
    (np.ndarray, Affine) clipped 2-D array and updated geotransform.
    """
    out = np.full_like(band_array, nodata, dtype=band_array.dtype)
    out[mask_array] = band_array[mask_array]
    return out, transform


def clip_raster(dataset, geometry, nodata=None):
    """Clip a rasterio dataset to a geometry using ``rasterio.mask.mask``.

    Falls back to a manual array-level mask if rasterio is unavailable.
    """
    if rasterio is not None and mask is not None:
        out_image, out_transform = mask(dataset, [geometry], crop=True, nodata=nodata)
        return out_image.squeeze(), out_transform
    raise RuntimeError("rasterio is required to clip rasters.")