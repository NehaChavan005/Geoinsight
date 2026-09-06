"""Google Earth Engine acquisition for GeoInsight Member-A datasets.

Downloads the real remote-sensing rasters used by the Member-A pipeline:

* Sentinel-2 (COPERNICUS/S2_SR_HARMONIZED) B4/B8 -> data/sentinel2/
* CHIRPS daily rainfall (UCSB-CHG/CHIRPS/DAILY)  -> data/rainfall/
* JRC Global Surface Water 1.4 (JRC/GSW1_4/GlobalSurfaceWater) -> data/water/

The exports are launched through ``ee.batch.Export.image.toDrive``.  After a
Drive "GeoInsight" export finishes, move the GeoTIFFs into the matching
``data/<group>/`` folder shown above.

No credentials, tokens, project IDs or service-account keys are stored here.
Earth Engine authentication is interactive (one-time browser flow):
``ee.Authenticate()`` (or CLI command ``earthengine authenticate``).

Usage
-----
::

    python app/processing/gee_export.py all
    python app/processing/gee_export.py sentinel2
    python app/processing/gee_export.py rainfall
    python app/processing/gee_export.py water

How the Sentinel-2 June composite is made
------------------------------------------
1. Load ``data/boundaries/kamrup.geojson`` and convert it to an ``ee.Geometry``.
2. Search ``COPERNICUS/S2_SR_HARMONIZED`` between 2026-06-01 and 2026-06-30
   intersecting Kamrup.
3. Start from a ``CLOUDY_PIXEL_PERCENTAGE < 50`` filter and relax the
   threshold (80, then 100) only if too few scenes survive.
4. Mask cloud and cirrus pixels with the QA60 bit mask.
5. Select B4 and B8 (10 m bands) over every masked scene.
6. Build a median composite over the month and export B4 and B8 separately
   at 10 m scale.

Bench fact (not a June 2026 observation)
----------------------------------------
JRC Global Surface Water v1.4 represents historical surface-water occurrence
through 2021; the resulting water raster is a historical/reference coverage,
NOT a June 2026 measurement.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import ee

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
BOUNDARY_PATH = DATA_DIR / "boundaries" / "kamrup.geojson"

# Environment variables that can supply the Google Cloud project for Earth
# Engine.  The project is never hardcoded in this file; it is read at runtime
# so each user can point the pipeline at their own project.
PROJECT_ENV_VARS = (
    "EARTHENGINE_PROJECT",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_QUOTA_PROJECT",
)

SENTINEL2_DIR = DATA_DIR / "sentinel2"
RAINFALL_DIR = DATA_DIR / "rainfall"
WATER_DIR = DATA_DIR / "water"

JUNE_2026_START = "2026-06-01"
JUNE_2026_END = "2026-06-30"

SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
CHIRPS_COLLECTION = "UCSB-CHG/CHIRPS/DAILY"
JRC_IMAGE = "JRC/GSW1_4/GlobalSurfaceWater"

DRIVE_FOLDER = "GeoInsight"
MAX_PIXELS = 1e10


def _detect_project() -> str | None:
    """Return the Google Cloud project for Earth Engine, if one is set.

    Looks up, in order, the ``EARTHENGINE_PROJECT``, ``GOOGLE_CLOUD_PROJECT``
    and ``GOOGLE_CLOUD_QUOTA_PROJECT`` environment variables.  Returns ``None``
    when none of them is defined (or when they are blank) so the caller can
    raise a clear, actionable error instead of guessing a project.
    """
    for name in PROJECT_ENV_VARS:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def initialize_ee() -> str:
    """Initialise Earth Engine, giving a clear message on failure.

    The Google Cloud project is supplied through an environment variable
    (``EARTHENGINE_PROJECT``, ``GOOGLE_CLOUD_PROJECT`` or
    ``GOOGLE_CLOUD_QUOTA_PROJECT``) and passed to ``ee.Initialize(project=...)``.
    It is never hardcoded or stored in this file.  If no project is set the
    function fails with an explicit message instead of falling back to a fake
    project.

    Raises
    ------
    RuntimeError
        If no project is configured or Earth Engine cannot be initialized.

    Returns
    -------
    str
        The Google Cloud project that Earth Engine was initialized with.
    """
    project = _detect_project()
    if project is None:
        raise RuntimeError(
            "Earth Engine needs a Google Cloud project, but none was found.\n"
            "Set one of the following environment variables and retry:\n"
            f"    {'  or  '.join(PROJECT_ENV_VARS)}\n"
            "To see your available project IDs, run:\n"
            '    gcloud config get-value project\n'
            "or list all of them with:\n"
            '    gcloud projects list\n'
            "then set e.g.:\n"
            "    setx EARTHENGINE_PROJECT \"<your-project-id>\"\n"
            "and open a NEW terminal so the change takes effect."
        )

    try:
        ee.Initialize(project=project)
    except Exception as exc:  # noqa: BLE001 - surface a helpful message
        print(
            "Earth Engine could not be initialized automatically.\n"
            "Authenticate once in your browser with:\n"
            '    python -c "import ee; ee.Authenticate()"\n'
            "or, from the command line:\n"
            "    earthengine authenticate\n"
            f"using project '{project}', then re-run this script."
        )
        raise RuntimeError("Earth Engine authentication required.") from exc

    return project


def load_boundary_geometry(boundary_path: str | Path = BOUNDARY_PATH) -> ee.Geometry:
    """Convert the Kamrup GeoJSON feature into an ``ee.Geometry``.

    Parameters
    ----------
    boundary_path:
        Path to the boundary GeoJSON (CRS EPSG:4326 / CRS84).

    Returns
    -------
    ee.Geometry
        The first feature's geometry (Polygon).
    """
    boundary_path = Path(boundary_path)
    if not boundary_path.exists():
        raise FileNotFoundError(f"Boundary file not found: {boundary_path}")

    with boundary_path.open(encoding="utf-8") as handle:
        geojson = json.load(handle)

    features = geojson.get("features", [])
    if not features:
        raise ValueError(f"Boundary file has no features: {boundary_path}")

    geometry = features[0]["geometry"]
    if geometry["type"] != "Polygon":
        raise ValueError(
            f"Boundary geometry must be a Polygon, got {geometry['type']}."
        )

    return ee.Geometry(geometry)


def _apply_s2_cloud_mask(image: ee.Image) -> ee.Image:
    """Mask cloud and cirrus pixels in a Sentinel-2 SR image via QA60."""
    qa = image.select("QA60")
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11
    cloud_mask = (
        qa.bitwiseAnd(cloud_bit_mask).eq(0).And(
            qa.bitwiseAnd(cirrus_bit_mask).eq(0)
        )
    )
    return image.updateMask(cloud_mask)


def build_sentinel2_composite(
    geometry: ee.Geometry,
    start: str = JUNE_2026_START,
    end: str = JUNE_2026_END,
) -> tuple[ee.Image, dict]:
    """Build the June 2026 B4/B8 median composite for the AOI.

    Returns the composite image together with a small log dictionary
    (scene count, usable scene count, bands present, cloud statistics).

    The cloud filter starts at ``CLOUDY_PIXEL_PERCENTAGE < 50`` and is
    relaxed (80, then 100) only if too few scenes survive.
    """
    collection = ee.ImageCollection(SENTINEL2_COLLECTION).filterBounds(geometry)

    scene_count = int(collection.size().getInfo())

    used_threshold = None
    usable = None
    for threshold in (50, 80, 100):
        candidate = collection.filterDate(start, end).filter(
            ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", threshold)
        )
        usable = candidate
        used_threshold = threshold
        if int(candidate.size().getInfo()) > 0:
            break

    usable_count = int(usable.size().getInfo())

    bands = ee.Image(usable.first()).bandNames().getInfo() if usable_count else []

    info_dump = {
        "scene_count_in_period": scene_count,
        "usable_scene_count": usable_count,
        "cloud_threshold_used_pct": used_threshold,
        "bands_available": bands,
    }
    print(
        f"Scene count in {start}..{end}: {scene_count}\n"
        f"Usable scenes after CLOUDY_PIXEL_PERCENTAGE < {used_threshold}: "
        f"{usable_count}"
    )

    if usable_count == 0:
        print(
            "No usable Sentinel-2 scenes for the period. "
            "The composite cannot be built."
        )
        return ee.Image(), info_dump

    includes_b4 = "B4" in bands
    includes_b8 = "B8" in bands
    print(
        f"Bands on first usable scene: {bands}\n"
        f"B4 present: {includes_b4} | B8 present: {includes_b8}"
    )

    cloud_report = (
        usable.limit(5)
        .map(
            lambda img: ee.Feature(
                None,
                {
                    "id": img.id(),
                    "cloud_pct": img.get("CLOUDY_PIXEL_PERCENTAGE"),
                },
            )
        )
        .getInfo()
    )
    print("Sample scene cloud percentages:")
    for feature in cloud_report["features"]:
        print(
            f"  {feature['properties']['id']}: "
            f"{feature['properties']['cloud_pct']} %"
        )

    masked = usable.map(_apply_s2_cloud_mask).select(["B4", "B8"])
    composite = masked.median().rename(["B4", "B8"])
    info_dump["bands_exported"] = ["B4", "B8"]
    return composite, info_dump


def export_sentinel2(geometry: ee.Geometry, start: str, end: str) -> list:
    """Launch the Sentinel-2 B4/B8 June 2026 composite export tasks."""
    composite, _info = build_sentinel2_composite(geometry, start, end)

    region = geometry.bounds()

    tasks = []
    band_targets = {
        "B4": SENTINEL2_DIR / "sentinel2_B04_june2026.tif",
        "B8": SENTINEL2_DIR / "sentinel2_B08_june2026.tif",
    }
    for band, target in band_targets.items():
        task = ee.batch.Export.image.toDrive(
            image=composite.select(band),
            description=f"GeoInsight_{band}_June2026",
            folder=DRIVE_FOLDER,
            fileNamePrefix=f"GeoInsight_{band}_June2026",
            scale=10,
            region=region,
            maxPixels=MAX_PIXELS,
        )
        task.start()
        tasks.append(task)
        print(
            f"Export task started for {band} -> Drive/{DRIVE_FOLDER}/\n"
            f"  intended local path: {target}\n"
            "  download the GeoTIFF from Drive and place it there."
        )
    return tasks


def export_chirps(geometry: ee.Geometry) -> ee.batch.Task:
    """Launch the June 2026 CHIRPS total-rainfall export task.

    The exported image is the SUM of daily ``precipitation`` pixels across
    the month, i.e. total June 2026 rainfall in mm.
    """
    daily = (
        ee.ImageCollection(CHIRPS_COLLECTION)
        .filterBounds(geometry)
        .filterDate(JUNE_2026_START, JUNE_2026_END)
        .select("precipitation")
    )

    total = daily.sum().rename("precipitation")

    count = int(daily.size().getInfo())
    print(
        f"CHIRPS daily images in June 2026: {count}\n"
        "Metric: TOTAL MONTHLY RAINFALL (mm) = sum of daily precipitation."
    )

    target = RAINFALL_DIR / "chirps_june2026.tif"
    task = ee.batch.Export.image.toDrive(
        image=total,
        description="GeoInsight_CHIRPS_June2026",
        folder=DRIVE_FOLDER,
        fileNamePrefix="GeoInsight_CHIRPS_June2026",
        scale=5566,
        region=geometry.bounds(),
        maxPixels=MAX_PIXELS,
    )
    task.start()
    print(
        f"Export task started for CHIRPS June 2026 -> Drive/{DRIVE_FOLDER}/\n"
        f"  intended local path: {target}"
    )
    return task


def export_jrc_water(geometry: ee.Geometry) -> ee.batch.Task:
    """Launch the JRC Global Surface Water occurrence export task.

    The exported band is ``occurrence`` (0-100); pixels ``>= 50`` are
    treated as water by the processing pipeline.  This is a historical
    surface-water coverage (dataset spans 1984-2021), NOT a June 2026
    observation.
    """
    occurrence = ee.Image(JRC_IMAGE).select("occurrence")
    print(
        "JRC/GSW1_4/GlobalSurfaceWater: historical surface-water occurrence "
        "through 2021; export is a reference coverage, not a June 2026 "
        "observation."
    )

    target = WATER_DIR / "jrc_water.tif"
    task = ee.batch.Export.image.toDrive(
        image=occurrence,
        description="GeoInsight_JRC_Water",
        folder=DRIVE_FOLDER,
        fileNamePrefix="GeoInsight_JRC_Water",
        scale=30,
        region=geometry.bounds(),
        maxPixels=MAX_PIXELS,
    )
    task.start()
    print(
        f"Export task started for JRC water -> Drive/{DRIVE_FOLDER}/\n"
        f"  intended local path: {target}"
    )
    return task


def main() -> None:
    """Run the requested GEE exports from the command line."""
    if len(sys.argv) != 2 or sys.argv[1] not in {"all", "sentinel2", "rainfall", "water"}:
        print(
            "Usage:\n"
            "  python app/processing/gee_export.py all\n"
            "  python app/processing/gee_export.py sentinel2\n"
            "  python app/processing/gee_export.py rainfall\n"
            "  python app/processing/gee_export.py water"
        )
        sys.exit(1)

    target = sys.argv[1]

    print("Initializing Earth Engine (no credentials stored locally).")
    project = initialize_ee()

    print(f"Loading boundary: {BOUNDARY_PATH}")
    geometry = load_boundary_geometry(BOUNDARY_PATH)

    if target in {"all", "sentinel2"}:
        export_sentinel2(geometry, JUNE_2026_START, JUNE_2026_END)
    if target in {"all", "rainfall"}:
        export_chirps(geometry)
    if target in {"all", "water"}:
        export_jrc_water(geometry)

    print(
        "\nAll export tasks started. Track them with:\n"
        f"    python -c \"import ee; ee.Initialize(project='{project}'); "
        "[print(t.id, t.state) for t in ee.batch.Task.list()]\""
    )


if __name__ == "__main__":
    main()