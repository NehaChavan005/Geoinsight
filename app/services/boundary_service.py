"""District geometry loading and area calculation service."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import get_district_config
from app.exceptions import DataNotFoundError, DistrictNotFoundError


def get_district_config_or_raise(district_id: str) -> dict:
    config = get_district_config(district_id)
    if config is None:
        raise DistrictNotFoundError(district_id)
    return config


def _load_feature_collection(district_id: str) -> dict:
    config = get_district_config_or_raise(district_id)
    boundary_path = Path(config["boundary_path"])
    if not boundary_path.exists():
        raise DataNotFoundError("Boundary", district_id)
    with open(boundary_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_district_boundary(district_id: str) -> dict:
    """Return the district boundary as a Leaflet-friendly FeatureCollection.

    If the file is a bare geometry (``Point`` / ``Polygon`` / …), it is
    wrapped in a Feature with the district display name as a property.
    """
    fc = _load_feature_collection(district_id)
    config = get_district_config_or_raise(district_id)
    if fc.get("type") == "FeatureCollection":
        features = fc.get("features") or []
        if not features:
            raise DataNotFoundError("Boundary", district_id)
        return {
            "type": "Feature",
            "properties": {"district": config["display_name"]},
            "geometry": features[0]["geometry"],
        }
    return {
        "type": "Feature",
        "properties": {"district": config["display_name"]},
        "geometry": fc["geometry"],
    }


def get_district_geometry(district_id: str):
    """Return the district boundary as a shapely geometry (EPSG:4326).

    This is the geometry handed to Member A's processing functions.
    Raises ``DataNotFoundError`` for an empty/placeholder boundary.
    """
    from shapely.geometry import shape

    boundary = get_district_boundary(district_id)
    geom = shape(boundary["geometry"])
    if geom.is_empty:
        raise DataNotFoundError("Boundary", district_id)
    return geom


def get_district_area_km2(district_id: str) -> float:
    """Compute district area in km² using an equal-area projection.

    ``Albers Equal Area`` (ESRI:102025) is used when possible so the area is
    meaningful across India; falls back to WGS84 lon/lat degrees otherwise.
    """
    geom = get_district_geometry(district_id)
    try:
        from pyproj import CRS, Transformer

        transformer = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(102025), always_xy=True)
        projected = transformer.transform(geom)
        return float(projected.area) / 1_000_000.0
    except Exception:
        return float(geom.area)