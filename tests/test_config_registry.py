"""Tests for the district configuration registry."""

import os

import pytest

from app.config import DATA_DIR, RAINFALL_METRIC, SUPPORTED_DISTRICTS, get_district_config
from app.exceptions import DistrictNotFoundError
from app.services.boundary_service import get_district_config_or_raise


def test_kamrup_is_registered():
    assert "kamrup" in SUPPORTED_DISTRICTS


def test_registry_entry_has_valid_shape():
    cfg = SUPPORTED_DISTRICTS["kamrup"]
    assert cfg["display_name"] == "Kamrup"
    assert cfg["state"] == "Assam"
    assert cfg["boundary_path"].endswith("kamrup.geojson")


def test_boundary_path_points_into_data_directory():
    cfg = SUPPORTED_DISTRICTS["kamrup"]
    assert os.path.normpath(cfg["boundary_path"]).startswith(os.path.normpath(str(DATA_DIR)))


def test_rainfall_metric_is_singleton():
    assert RAINFALL_METRIC == "total_mm"


def test_unknown_district_rejected():
    assert get_district_config("nonexistent") is None


def test_service_helper_raises_for_unknown_district():
    with pytest.raises(DistrictNotFoundError):
        get_district_config_or_raise("nonexistent")


def test_registry_lookup_is_keyed_lookup_not_branching():
    # The registry must be a plain mapping lookup; every key must resolve
    # through the same code path without district-specific branches.
    for district_id in SUPPORTED_DISTRICTS:
        assert get_district_config(district_id) is not None


def test_no_hardcoded_district_branches_in_api_services_cache():
    """Production modules must not contain district-specific conditionals."""
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    scanned_dirs = ["app/api", "app/services", "app/cache", "app/processing"]
    banned = ['dist == "', 'district == "', 'district_id == "', 'month == "']

    findings = []
    for base in scanned_dirs:
        for path in (repo_root / base).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in banned:
                if pattern in text:
                    findings.append(f"{path}: contains {pattern!r}")
    assert findings == [], f"district/month-specific branches found:\n" + "\n".join(findings)


def test_empty_boundary_raises_data_not_found(tmp_path, monkeypatch):
    """A registry entry pointing to an empty FeatureCollection is data-missing."""
    import json

    from app import config as config_module
    from app.exceptions import DataNotFoundError
    from app.services import boundary_service

    empty_geojson = tmp_path / "empty.geojson"
    empty_geojson.write_text(json.dumps({"type": "FeatureCollection", "features": []}))

    monkeypatch.setitem(
        config_module.SUPPORTED_DISTRICTS,
        "placeholder",
        {
            "display_name": "Placeholder",
            "state": "XX",
            "boundary_path": str(empty_geojson),
        },
    )

    with pytest.raises(DataNotFoundError):
        boundary_service.get_district_boundary("placeholder")