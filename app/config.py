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
    return SENTINEL2_DIR / month / district_id


def chirps_path(district_id: str, month: str) -> Path:
    return CHIRPS_DIR / month / district_id


def jrc_water_path(district_id: str) -> Path:
    return JRC_WATER_DIR / district_id


# Named helpers used by the service adapters (Member A ↔ Member B boundary).
def get_sentinel_path(district_id: str, month: str) -> Path:
    return sentinel2_path(district_id, month)


def get_chirps_path(district_id: str, month: str) -> Path:
    return chirps_path(district_id, month)


def get_water_path(district_id: str) -> Path:
    return jrc_water_path(district_id)