"""Member A validation script for the GeoInsight processing pipeline.

Run from the project root::

    python app/processing/validate_member_a.py

It looks for the acquired rasters under ``data/`` and, for every input file
that is present, runs the matching processing function and prints the
numerical result.  Missing files are reported as ``[MISSING] <file>`` and
never fabricated.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.processing.clipping import clip_raster_to_boundary  # noqa: E402
from app.processing.ndvi import (  # noqa: E402
    NDVI_VALID_RANGE,
    calculate_ndvi,
    calculate_ndvi_array,
)
from app.processing.rainfall import calculate_monthly_rainfall  # noqa: E402
from app.processing.water import calculate_water_area  # noqa: E402

REQUIRED_FILES = {
    "boundary": DATA_DIR / "boundaries" / "kamrup.geojson",
    "sentinel2_b4": DATA_DIR / "sentinel2" / "sentinel2_B04_june2026.tif",
    "sentinel2_b8": DATA_DIR / "sentinel2" / "sentinel2_B08_june2026.tif",
    "rainfall": DATA_DIR / "rainfall" / "chirps_june2026.tif",
    "water": DATA_DIR / "water" / "jrc_water.tif",
}


def check_files() -> list[str]:
    """Print ``[MISSING]`` lines and return the keys that are present."""
    present = []
    for label, path in REQUIRED_FILES.items():
        if path.exists():
            present.append(label)
        else:
            print(f"[MISSING] {path}")
    return present


def _fmt(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}"


RASTERS_TO_DESCRIBE = {
    "Sentinel-2 B4": REQUIRED_FILES["sentinel2_b4"],
    "Sentinel-2 B8": REQUIRED_FILES["sentinel2_b8"],
    "CHIRPS June 2026 rainfall": REQUIRED_FILES["rainfall"],
    "JRC water": REQUIRED_FILES["water"],
}


def describe_rasters() -> None:
    """Print CRS, dimensions and dtype of every real input GeoTIFF."""
    print("Raster sources (real GeoTIFF files used):")
    for label, path in RASTERS_TO_DESCRIBE.items():
        if not path.exists():
            continue
        with rasterio.open(path) as src:
            print(
                f"  {label}: {path.name} | CRS={src.crs} | "
                f"size={src.width}x{src.height} | bands={src.count} | "
                f"dtype={src.dtypes[0]}"
            )
    print()


def ndvi_valid_pixel_count() -> int | None:
    """Re-check the number of NDVI pixels actually averaged (0-1 range)."""
    b4 = REQUIRED_FILES["sentinel2_b4"]
    b8 = REQUIRED_FILES["sentinel2_b8"]
    bound = REQUIRED_FILES["boundary"]
    if not (b4.exists() and b8.exists() and bound.exists()):
        return None

    red_clipped, _, red_meta = clip_raster_to_boundary(b4, bound)
    nir_clipped, _, nir_meta = clip_raster_to_boundary(b8, bound)

    red = red_clipped[0].astype(np.float32)
    nir = nir_clipped[0].astype(np.float32)

    valid = np.isfinite(red) & np.isfinite(nir)
    red_nodata = red_meta.get("nodata")
    nir_nodata = nir_meta.get("nodata")
    if red_nodata is not None:
        valid &= red != red_nodata
    if nir_nodata is not None:
        valid &= nir != nir_nodata

    ndvi = calculate_ndvi_array(red, nir)[valid]
    ndvi = ndvi[
        np.isfinite(ndvi)
        & (ndvi >= NDVI_VALID_RANGE[0])
        & (ndvi <= NDVI_VALID_RANGE[1])
    ]
    return int(ndvi.size)


def main() -> None:
    present = check_files()

    print("=" * 40)
    print("GEOINSIGHT - MEMBER A VALIDATION")
    print("=" * 40)
    print("District: Kamrup")
    print("State: Assam")
    print("Period: June 2026")
    print()

    all_present = "boundary" in present and len(present) == len(REQUIRED_FILES)

    if not all_present:
        print(
            "Some required datasets are missing (see [MISSING] lines above); "
            "no values were fabricated. Running the tasks whose inputs exist."
        )
        print()

    mean_ndvi = None
    total_rainfall = None
    water_result = None

    if "sentinel2_b4" in present and "sentinel2_b8" in present:
        mean_ndvi = calculate_ndvi(
            REQUIRED_FILES["sentinel2_b4"],
            REQUIRED_FILES["sentinel2_b8"],
            REQUIRED_FILES["boundary"],
        )
        print("NDVI:")
        print(f"Mean NDVI: {_fmt(mean_ndvi, 4)}")
        print()
    elif "sentinel2_b4" in present or "sentinel2_b8" in present:
        missing = (
            "sentinel2_B08_june2026.tif"
            if "sentinel2_b4" in present
            else "sentinel2_B04_june2026.tif"
        )
        print(f"[MISSING] {REQUIRED_FILES['sentinel2_b4'].parent / missing}")
        print("NDVI: skipped (one or both Sentinel-2 rasters missing)")
        print()

    if "rainfall" in present:
        total_rainfall = calculate_monthly_rainfall(
            REQUIRED_FILES["rainfall"],
            REQUIRED_FILES["boundary"],
        )
        print("Rainfall:")
        print(f"June 2026 total rainfall: {_fmt(total_rainfall, 2)} mm")
        print()
    else:
        print("Rainfall: skipped (CHIRPS raster missing)")
        print()

    if "water" in present:
        water_result = calculate_water_area(
            REQUIRED_FILES["water"],
            REQUIRED_FILES["boundary"],
        )
        print("Water:")
        print(f"Water pixels: {water_result['water_pixels']}")
        print(f"Valid pixels: {water_result['valid_pixels']}")
        print(f"Water percentage: {_fmt(water_result['water_percentage'], 2)} %")
        print(f"Water area: {_fmt(water_result['water_area_km2'], 2)} km2")
        print()
    else:
        print("Water: skipped (JRC raster missing)")
        print()

    describe_rasters()

    if mean_ndvi is not None:
        print(f"NDVI valid pixels averaged: {ndvi_valid_pixel_count()}")
        print()

    print("=" * 40)
    print("Kamrup \u2014 June 2026")
    print("-------------------")
    print(
        f"Mean NDVI: {_fmt(mean_ndvi, 4)}"
        if mean_ndvi is not None
        else "Mean NDVI: n/a"
    )
    print(
        f"Total Rainfall: {_fmt(total_rainfall, 2)} mm"
        if total_rainfall is not None
        else "Total Rainfall: n/a"
    )
    print(
        f"Water Pixels (>=50% occurrence): {water_result['water_pixels']}"
        if water_result is not None
        else "Water Pixels (>=50% occurrence): n/a"
    )
    print(
        f"Water Area: {_fmt(water_result['water_area_km2'], 2)} km\u00b2"
        if water_result is not None
        else "Water Area: n/a"
    )
    print("=" * 40)

    print()
    print("Validation:")
    for label, value in (
        ("Mean NDVI", mean_ndvi),
        ("Total Rainfall (mm)", total_rainfall),
        ("Water area (km2)", water_result["water_area_km2"] if water_result else None),
    ):
        ok = value is not None and np.isfinite(value)
        print(f"  {label}: {'OK (finite)' if ok else 'INVALID'}")
    print(
        "Inputs: real GeoTIFF files acquired from Google Earth Engine "
        "(data/sentinel2, data/rainfall, data/water); no synthetic data."
    )
    print(
        "Note: JRC Global Surface Water v1.4 is a historical/reference "
        "coverage (1984-2021), not a June 2026 observation."
    )


if __name__ == "__main__":
    main()