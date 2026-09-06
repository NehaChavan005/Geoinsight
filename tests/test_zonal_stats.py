"""Tests for the zonal statistics helpers (pure numpy functions)."""

import numpy as np
import pytest

from app.processing.zonal_stats import (
    compute_mean,
    compute_sum,
    pixel_area_km2,
    pixel_count_valid,
    water_coverage_stats,
)


def test_pixel_count_valid_counts_finite_non_nodata():
    arr = np.array([[1.0, np.nan], [2.0, -9999.0]])
    assert pixel_count_valid(arr, nodata=-9999.0) == 2


def test_pixel_count_valid_respects_mask():
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])
    mask = np.array([[True, True], [False, True]])
    assert pixel_count_valid(arr, nodata=None, mask=mask) == 3


def test_compute_mean_ignores_nodata_and_nan():
    arr = np.array([[1.0, np.nan], [2.0, 5.0]])
    assert compute_mean(arr, nodata=-9999.0) == pytest.approx((1.0 + 2.0 + 5.0) / 3.0)


def test_compute_mean_empty_returns_none():
    arr = np.array([[np.nan, np.nan], [np.nan, np.nan]])
    assert compute_mean(arr, nodata=None) is None


def test_compute_sum_sums_valid_pixels():
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])
    assert compute_sum(arr) == pytest.approx(10.0)


def test_compute_sum_empty_returns_none():
    arr = np.array([[np.nan]])
    assert compute_sum(arr) is None


def test_pixel_area_km2_10m():
    assert pixel_area_km2(10.0) == pytest.approx(0.0001)


def test_water_coverage_stats():
    coverage, area = water_coverage_stats(
        count_water_pixels=100,
        total_water_pixels=10000,
        total_area_km2=1.0,
        res_m=10.0,
    )
    assert area == pytest.approx(100 * 0.0001)
    assert coverage == pytest.approx(area / 1.0 * 100.0)


def test_compute_mean_with_mask():
    arr = np.array([[1.0, 99.0], [98.0, 4.0]])
    mask = np.array([[True, False], [False, True]])
    assert compute_mean(arr, nodata=None, mask=mask) == pytest.approx(2.5)