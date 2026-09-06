"""Shared zonal statistics helpers.

Pure functions operating on numpy arrays.  These make no I/O and are
unit-testable without real raster files.
"""

from __future__ import annotations

import numpy as np


def pixel_count_valid(arr, nodata=None, mask=None):
    """Count valid (non-nodata, finite) pixels in a 2-D array."""
    valid = np.isfinite(arr)
    if nodata is not None:
        valid &= arr != nodata
    if mask is not None:
        valid &= mask
    return int(valid.sum())


def compute_mean(arr, nodata=None, mask=None):
    """Mean of valid pixels. Returns None when no valid pixels exist."""
    valid_arr = np.where(np.isfinite(arr), arr, np.nan)
    if nodata is not None:
        valid_arr = np.where(arr == nodata, np.nan, valid_arr)
    if mask is not None:
        valid_arr = np.where(mask, valid_arr, np.nan)
    vals = valid_arr[~np.isnan(valid_arr)]
    if vals.size == 0:
        return None
    return float(np.mean(vals))


def compute_sum(arr, nodata=None, mask=None):
    """Sum of valid pixels. Returns None when no valid pixels exist."""
    valid_arr = np.where(np.isfinite(arr), arr, np.nan)
    if nodata is not None:
        valid_arr = np.where(arr == nodata, np.nan, valid_arr)
    if mask is not None:
        valid_arr = np.where(mask, valid_arr, np.nan)
    vals = valid_arr[~np.isnan(valid_arr)]
    if vals.size == 0:
        return None
    return float(np.sum(vals))


def pixel_area_km2(res_m=10.0):
    """Area in km² covered by a single square pixel of ``res_m`` resolution."""
    res_km = res_m / 1000.0
    return res_km * res_km


def water_coverage_stats(count_water_pixels, total_water_pixels, total_area_km2, res_m=10.0):
    """Convert water pixel counts to coverage stats.

    Returns ``(coverage_percent, area_km2)`` computed from real pixel counts
    only.  Raises ``ValueError`` when the inputs are inconsistent.
    """
    area_km2 = count_water_pixels * pixel_area_km2(res_m)
    if total_area_km2 is None or total_area_km2 <= 0:
        coverage_percent = 0.0
    else:
        coverage_percent = (area_km2 / total_area_km2) * 100.0
    return coverage_percent, area_km2