"""Application configuration registry and constants.

Member B's runtime configuration: the district registry, data-dir layout and
the single rainfall-metric constant.  Data directories are overridable via
environment variables so deployments can point at mounted volumes without
code changes.

``app/processing/`` (Member A's territory) is resolved purely from these
paths; no raster dataset logic lives here.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("GEOINSIGHT_DATA_DIR", str(BASE_DIR / "data")))
CACHE_DB_PATH = Path(
    os.environ.get("GEOINSIGHT_CACHE_DB", str(DATA_DIR / "cache.sqlite3"))
)

BOUNDARIES_DIR = DATA_DIR / "boundaries"
SENTINEL2_DIR = DATA_DIR / "sentinel2"
CHIRPS_DIR = DATA_DIR / "chirps"
JRC_WATER_DIR = DATA_DIR / "jrc_water"

# Member A's actual on-disk dataset layout (large rasters kept out of git).
RAINFALL_DATA_DIR = DATA_DIR / "rainfall"
WATER_DATA_DIR = DATA_DIR / "water"

# District-scope dataset rasters as extracted by Member A.  These are the exact
# files the processing adapter uses for a district-level metric/layer; the state
# rasters (``*_assam.tif``) remain untouched in the same folders.
CHIRPS_DISTRICT_RASTER = RAINFALL_DATA_DIR / "chirps_june2026.tif"
JRC_DISTRICT_RASTER = WATER_DATA_DIR / "jrc_water.tif"

# Known (district, month) -> district-scope raster lookups.  Plain data-driven
# mappings: path resolution carries no district/month branches.
CHIRPS_RASTERS: dict[tuple[str, str], Path] = {
    ("kamrup", "2026-06"): CHIRPS_DISTRICT_RASTER,
}
JRC_RASTERS: dict[str, Path] = {
    "kamrup": JRC_DISTRICT_RASTER,
}

# Sentinel-2 dataset registry: known (district, month) -> (B4, B8) band raster.
# Member A's GEE exports for a supported combination land in ``data/sentinel2/``
# with the canonical names ``sentinel2_B04_june2026.tif`` /
# ``sentinel2_B08_june2026.tif`` (see ``app/processing/gee_export.py``).  The
# pair is registered here so services and the adapter resolve it without
# duplicating the large TIFFs into a per-month folder.
SENTINEL2_DISTRICT_RASTER_B4 = SENTINEL2_DIR / "sentinel2_B04_june2026.tif"
SENTINEL2_DISTRICT_RASTER_B8 = SENTINEL2_DIR / "sentinel2_B08_june2026.tif"

SENTINEL2_RASTERS: dict[tuple[str, str], tuple[Path, Path]] = {
    ("kamrup", "2026-06"): (
        SENTINEL2_DISTRICT_RASTER_B4,
        SENTINEL2_DISTRICT_RASTER_B8,
    ),
}

# Band filenames accepted inside a Sentinel-2 dataset folder (red, nir): the
# Member A export names first, then the legacy ``B4.tif``/``B8.tif`` layout.
SENTINEL2_BAND_NAME_PAIRS = (
    ("sentinel2_B04_june2026.tif", "sentinel2_B08_june2026.tif"),
    ("B4.tif", "B8.tif"),
)

RAINFALL_METRIC = "total_mm"

SUPPORTED_DISTRICTS: dict[str, dict] = {
    "kamrup": {
        "display_name": "Kamrup",
        "state": "Assam",
        "boundary_path": str(BOUNDARIES_DIR / "kamrup.geojson"),
    },
}


def get_district_config(district_id: str) -> dict | None:
    try:
        return SUPPORTED_DISTRICTS[district_id]
    except KeyError:
        return None


def sentinel2_path(district_id: str, month: str) -> Path:
    bands = SENTINEL2_RASTERS.get((district_id, month))
    if bands is not None:
        return bands[0].parent
    return SENTINEL2_DIR / month / district_id


def sentinel2_band_files(district_id: str, month: str) -> tuple[Path, Path]:
    """Return the expected (red B4, nir B8) band files for a district/month.

    Uses the district-scope Sentinel-2 registry for known combinations and
    otherwise falls back to the legacy ``data/sentinel2/{month}/{district}/``
    layout with ``B4.tif``/``B8.tif`` names.
    """
    bands = SENTINEL2_RASTERS.get((district_id, month))
    if bands is not None:
        return bands
    data_dir = sentinel2_path(district_id, month)
    return data_dir / "B4.tif", data_dir / "B8.tif"


def chirps_path(district_id: str, month: str) -> Path:
    raster = CHIRPS_RASTERS.get((district_id, month))
    if raster is not None:
        return raster.parent
    return CHIRPS_DIR / month / district_id


def jrc_water_path(district_id: str) -> Path:
    raster = JRC_RASTERS.get(district_id)
    if raster is not None:
        return raster.parent
    return JRC_WATER_DIR / district_id


# Named helpers used by the service adapters (Member A ↔ Member B boundary).
def get_sentinel_path(district_id: str, month: str) -> Path:
    return sentinel2_path(district_id, month)


def get_chirps_path(district_id: str, month: str) -> Path:
    return chirps_path(district_id, month)


def get_water_path(district_id: str) -> Path:
    return jrc_water_path(district_id)