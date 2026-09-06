"""Generic Assam-wide district analysis for the Member-A pipeline.

This module replaces the Kamrup-only workflow with a data-driven analysis
that iterates EVERY Assam district boundary and independently computes:

* Mean NDVI          - June 2026 Sentinel-2 composite (GEE, 10 m)
* June 2026 rainfall - zonal MEAN of the state-wide CHIRPS monthly-sum
                       raster (mm), via :func:`app.processing.rainfall`
* Water              - JRC occurrence >= 50 % pixels, area (km\u00b2) and
                       coverage %, via :func:`app.processing.water`

District boundaries come from ``data/boundaries/assam/assam_districts.geojson``
(GeoBoundaries v5 / lgdirectory.gov.in, 33 districts, EPSG:4326).  The pipeline
has no per-district hardcoding and loops whatever districts the boundary file
contains.

Sentinel-2 is processed server-side in Earth Engine because a state-wide
10 m raster export is intractable (~3e9 pixels per band); the composite and
NDVI arithmetic are identical to the one used for the Kamrup offline rasters.
CHIRPS and JRC are processed locally from the state-wide GeoTIFFs:
``data/rainfall/chirps_june2026_assam.tif`` and ``data/water/jrc_water_assam.tif``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import ee  # noqa: E402

from app.processing.gee_export import (  # noqa: E402
    JUNE_2026_END,
    JUNE_2026_START,
    SENTINEL2_COLLECTION,
    _apply_s2_cloud_mask,
    initialize_ee,
)
from app.processing.rainfall import calculate_monthly_rainfall  # noqa: E402
from app.processing.water import calculate_water_area  # noqa: E402

ASSAM_DISTRICTS_FILE = DATA_DIR / "boundaries" / "assam" / "assam_districts.geojson"
ASSAM_STATE_FILE = DATA_DIR / "boundaries" / "assam_state.geojson"
ASSAM_BOUNDARIES_DIR = ASSAM_DISTRICTS_FILE.parent
STATE_CHIRPS_RASTER = DATA_DIR / "rainfall" / "chirps_june2026_assam.tif"
STATE_JRC_RASTER = DATA_DIR / "water" / "jrc_water_assam.tif"

NDVI_SCALE_M = 10


def list_district_names() -> list[str]:
    """Return the name of every district in the Assam boundary file."""
    with open(ASSAM_DISTRICTS_FILE, encoding="utf-8") as handle:
        data = json.load(handle)
    names = [f["properties"].get("Name") or f["properties"].get("name") for f in data["features"]]
    if any(name is None for name in names):
        raise ValueError("Assam district features are missing a 'Name' property.")
    return names


def district_boundary_path(district_file: Path) -> Path:
    """Return the single-feature GeoJSON path for a district.

    The per-district files are stored next to ``assam_districts.geojson`` with
    the district name (spaces replaced by underscores).
    """
    return ASSAM_BOUNDARIES_DIR / district_file


def build_state_sentinel2_composite() -> ee.Image:
    """Build the June 2026 monthly median B4/B8 composite for all Assam."""
    with open(ASSAM_STATE_FILE, encoding="utf-8") as handle:
        state_geom = json.load(handle)["features"][0]["geometry"]
    geometry = ee.Geometry(state_geom)

    collection = ee.ImageCollection(SENTINEL2_COLLECTION).filterBounds(geometry)

    scenes = collection.filterDate(JUNE_2026_START, JUNE_2026_END)
    masked = scenes.map(_apply_s2_cloud_mask).select(["B4", "B8"])
    composite = masked.median().rename(["B4", "B8"])
    return composite


def district_mean_ndvi(composite: ee.Image, geometry: ee.Geometry) -> float | None:
    """Return the mean NDVI of the composite inside a district (10 m)."""
    ndvi = composite.normalizedDifference(["B8", "B4"]).rename("NDVI")
    value = (
        ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=NDVI_SCALE_M,
            bestEffort=True,
            maxPixels=1e11,
        )
        .get("NDVI")
        .getInfo()
    )
    if value is None:
        return None
    return float(value)


def _district_geometry(geometry: str | dict) -> ee.Geometry:
    if isinstance(geometry, dict):
        return ee.Geometry(geometry)
    with open(geometry, encoding="utf-8") as handle:
        feature = json.load(handle)["features"][0]
    return ee.Geometry(feature["geometry"])


def analyze_district(
    name: str,
    boundary_path: Path,
    composite: ee.Image,
) -> dict:
    """Compute the three environmental indicators for a single district."""
    geometry = _district_geometry(boundary_path)

    ndvi = district_mean_ndvi(composite, geometry)
    rainfall_mm = calculate_monthly_rainfall(STATE_CHIRPS_RASTER, boundary_path)
    water = calculate_water_area(STATE_JRC_RASTER, boundary_path)

    return {
        "district": name,
        "ndvi": ndvi,
        "rainfall_mm": rainfall_mm,
        "water_pixels": water["water_pixels"],
        "water_percentage": water["water_percentage"],
        "water_area_km2": water["water_area_km2"],
    }


def save_results(results: list[dict], output_path: Path) -> None:
    """Write the per-district results as JSON."""
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)


def print_report(results: list[dict]) -> None:
    """Print the final Assam-wide report and verify no district is skipped."""
    names = list_district_names()
    reported = {r["district"] for r in results}
    missing = [n for n in names if n not in reported]
    duplicate = len(results) - len(reported)

    print("=" * 92)
    print("ASSAM-WIDE DISTRICT ANALYSIS - JUNE 2026 (33 districts)")
    print("=" * 92)
    print(
        f"{'District':<26}{'NDVI':>10}{'Rainfall(mm)':>14}"
        f"{'WaterPx':>12}{'WaterArea(km2)':>14}{'Water%':>8}"
    )
    print("-" * 100)
    for row in sorted(results, key=lambda r: r["district"]):
        ndvi = "n/a" if row["ndvi"] is None else f"{row['ndvi']:.4f}"
        rainfall = "n/a" if row["rainfall_mm"] is None else f"{row['rainfall_mm']:.2f}"
        water_px = "n/a" if row["water_pixels"] is None else f"{row['water_pixels']:,d}"
        water_area = "n/a" if row["water_area_km2"] is None else f"{row['water_area_km2']:.2f}"
        water_pct = "n/a" if row["water_percentage"] is None else f"{row['water_percentage']:.2f}"
        print(
            f"{row['district']:<26}{ndvi:>10}{rainfall:>14}"
            f"{water_px:>12}{water_area:>14}{water_pct:>8}"
        )
    print("-" * 100)
    print(
        f"Districts in boundary file: {len(names)} | "
        f"processed: {len(results)} | duplicates: {duplicate}"
    )
    if missing:
        print("SKIPPED DISTRICTS:", ", ".join(sorted(missing)))
    else:
        print("Verification: NO district was skipped (all names reported).")


def main() -> None:
    """Run the full analysis and print the report."""
    print("Initializing Earth Engine.")
    project = initialize_ee()

    names = list_district_names()
    print(f"Assam districts to process: {len(names)}")

    print("Building June 2026 Sentinel-2 composite for all Assam (GEE).")
    composite = build_state_sentinel2_composite()

    out_file = DATA_DIR / "assam_district_results.json"
    resume = {}
    if out_file.exists():
        try:
            with open(out_file, encoding="utf-8") as handle:
                resume = {r["district"]: r for r in json.load(handle)}
            print(f"Resuming: {len(resume)} districts already computed.")
        except (json.JSONDecodeError, KeyError, TypeError):
            resume = {}

    results = []
    for i, name in enumerate(names, start=1):
        cached = resume.get(name)
        if cached and "error" not in cached and "water_percentage" in cached:
            print(f"[{i}/{len(names)}] {name}: using cached result.")
            results.append(cached)
            continue
        boundary_path = district_boundary_path(Path(name.replace(" ", "_") + ".geojson"))
        if not boundary_path.exists():
            raise FileNotFoundError(
                f"District boundary file missing for '{name}': {boundary_path}"
            )
        print(f"[{i}/{len(names)}] Processing {name} ...", flush=True)
        try:
            row = analyze_district(name, boundary_path, composite)
        except Exception as exc:  # noqa: BLE001 - keep going, record the error
            print(f"  !! {name} FAILED: {exc}", flush=True)
            row = {
                "district": name,
                "ndvi": None,
                "rainfall_mm": None,
                "water_pixels": None,
                "water_percentage": None,
                "water_area_km2": None,
                "error": str(exc),
            }
        results.append(row)
        print(f"  -> {row}", flush=True)
        save_results(results, out_file)

    print(f"\nResults written to {out_file}")

    print_report(results)

    print(f"\n(Initialized with Earth Engine project '{project}'.)")


if __name__ == "__main__":
    main()