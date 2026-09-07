"""Tests for the /environment endpoint (and related endpoints) via TestClient.

All geospatial services are mocked so no real satellite raster files are
required.  Example indicator values below are TEST fixtures only.
"""

import pytest
from fastapi.testclient import TestClient

from app.cache.cache_manager import CacheManager
from app.exceptions import DataNotFoundError
from app.main import app

EXAMPLE_INDICATORS = {
    "ndvi": {"average_ndvi": 0.58, "pixel_count": 184532, "source": "Sentinel-2"},
    "rainfall": {"metric": "total_mm", "value_mm": 421.0, "source": "CHIRPS"},
    "water": {"coverage_percent": 4.7, "area_km2": 37.2, "source": "JRC Global Surface Water"},
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_cache = CacheManager(db_path=tmp_path / "test_cache.sqlite3")
    monkeypatch.setattr("app.cache.cache_manager.cache_manager", test_cache)
    return TestClient(app)


@pytest.fixture(autouse=True)
def _mock_services(monkeypatch):
    """Mock underlying services for the whole module."""

    def fake_ndvi(district_id, month):
        return dict(EXAMPLE_INDICATORS["ndvi"])

    def fake_rainfall(district_id, month):
        return dict(EXAMPLE_INDICATORS["rainfall"])

    def fake_water(district_id):
        return dict(EXAMPLE_INDICATORS["water"])

    def fake_area(district_id):
        return 792.0

    monkeypatch.setattr(
        "app.services.environment_service.ndvi_service.calculate_ndvi", fake_ndvi
    )
    monkeypatch.setattr(
        "app.services.environment_service.rainfall_service.calculate_rainfall", fake_rainfall
    )
    monkeypatch.setattr(
        "app.services.environment_service.water_service.calculate_water_coverage", fake_water
    )
    monkeypatch.setattr(
        "app.services.environment_service.boundary_service.get_district_area_km2", fake_area
    )


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_districts_list(client):
    resp = client.get("/api/v1/districts")
    assert resp.status_code == 200
    data = resp.json()
    ids = [d["id"] for d in data["districts"]]
    assert "kamrup" in ids
    kamrup = next(d for d in data["districts"] if d["id"] == "kamrup")
    assert kamrup["display_name"] == "Kamrup"
    assert kamrup["state"] == "Assam"


def test_environment_success_structure(client):
    resp = client.get("/api/v1/environment?district=kamrup&month=2026-06&")
    assert resp.status_code == 200
    data = resp.json()

    assert data["district"] == "Kamrup"
    assert data["state"] == "Assam"
    assert data["month"] == "2026-06"

    assert data["vegetation"]["average_ndvi"] == 0.58
    assert data["vegetation"]["pixel_count"] == 184532
    assert data["vegetation"]["source"] == "Sentinel-2"

    assert data["rainfall"]["metric"] == "total_mm"
    assert data["rainfall"]["value_mm"] == 421.0
    assert data["rainfall"]["source"] == "CHIRPS"

    assert data["surface_water"]["coverage_percent"] == 4.7
    assert data["surface_water"]["area_km2"] == 37.2
    assert data["surface_water"]["source"] == "JRC Global Surface Water"

    assert data["metadata"]["district_area_km2"] == 792.0
    assert data["metadata"]["cached"] is False
    assert data["metadata"]["processing_time_ms"] >= 0
    assert data["metadata"]["generated_at"].endswith("Z")
    assert data["warnings"] == []


def test_environment_invalid_district(client):
    resp = client.get("/api/v1/environment?district=nope&month=2026-06")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "DISTRICT_NOT_FOUND"


def test_environment_invalid_month_format(client):
    for bad in ["2026", "06-2026", "June-2026", "2026/06", "abc"]:
        resp = client.get(f"/api/v1/environment?district=kamrup&month={bad}")
        assert resp.status_code == 422, bad
        assert resp.json()["error"]["code"] == "INVALID_MONTH_FORMAT"


def test_environment_cache_miss_then_hit(client, monkeypatch):
    calls = {"count": 0}

    def counting_ndvi(district_id, month):
        calls["count"] += 1
        return dict(EXAMPLE_INDICATORS["ndvi"])

    monkeypatch.setattr(
        "app.services.environment_service.ndvi_service.calculate_ndvi", counting_ndvi
    )

    first = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    assert first.json()["metadata"]["cached"] is False
    assert calls["count"] == 1

    second = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    assert second.json()["metadata"]["cached"] is True
    assert calls["count"] == 1

    other = client.get("/api/v1/environment?district=kamrup&month=2025-12")
    assert other.json()["metadata"]["cached"] is False
    assert calls["count"] == 2


def test_environment_partial_data_failure(client, monkeypatch):
    def missing_ndvi(district_id, month):
        raise DataNotFoundError("Sentinel-2", district_id, month)

    monkeypatch.setattr(
        "app.services.environment_service.ndvi_service.calculate_ndvi", missing_ndvi
    )

    resp = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    assert resp.status_code == 200
    data = resp.json()
    assert data["vegetation"] is None
    assert data["rainfall"]["value_mm"] == 421.0
    assert data["surface_water"]["coverage_percent"] == 4.7
    assert any("Sentinel-2" in w for w in data["warnings"])


def test_environment_all_datasets_missing_still_200(client, monkeypatch):
    def missing_ndvi(district_id, month):
        raise DataNotFoundError("Sentinel-2", district_id, month)

    def missing_rain(district_id, month):
        raise DataNotFoundError("CHIRPS", district_id, month)

    def missing_water(district_id):
        raise DataNotFoundError("JRC Global Surface Water", district_id)

    monkeypatch.setattr(
        "app.services.environment_service.ndvi_service.calculate_ndvi", missing_ndvi
    )
    monkeypatch.setattr(
        "app.services.environment_service.rainfall_service.calculate_rainfall", missing_rain
    )
    monkeypatch.setattr(
        "app.services.environment_service.water_service.calculate_water_coverage", missing_water
    )

    resp = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    assert resp.status_code == 200
    data = resp.json()
    assert data["vegetation"] is None
    assert data["rainfall"] is None
    assert data["surface_water"] is None
    assert len(data["warnings"]) == 3


def test_layer_endpoint_missing_data_returns_503(client):
    # 2000-01 has no Sentinel-2 raster for Kamrup, so the layer must report
    # DATA_NOT_FOUND regardless of which real datasets exist on disk.
    resp = client.get("/api/v1/layers/ndvi?district=kamrup&month=2000-01")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "DATA_NOT_FOUND"


def test_layer_endpoint_invalid_type(client):
    resp = client.get("/api/v1/layers/hillshade?district=kamrup&month=2026-06")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_LAYER_TYPE"


def test_boundary_area_missing_does_not_fail_request(client, monkeypatch):
    def missing_area(district_id):
        raise DataNotFoundError("Boundary", district_id)

    monkeypatch.setattr(
        "app.services.environment_service.boundary_service.get_district_area_km2", missing_area
    )
    resp = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["district_area_km2"] is None
    assert data["vegetation"]["average_ndvi"] == 0.58


def test_boundary_endpoint(client, monkeypatch):
    fake_geojson = {
        "type": "Feature",
        "properties": {"district": "Kamrup"},
        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    }
    monkeypatch.setattr(
        "app.api.v1.districts.get_district_boundary", lambda district_id: fake_geojson
    )
    resp = client.get("/api/v1/districts/kamrup/boundary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "Feature"
    assert body["geometry"]["type"] == "Polygon"


def test_boundary_endpoint_unknown_district(client, monkeypatch):
    def boom(district_id):
        from app.exceptions import DistrictNotFoundError

        raise DistrictNotFoundError(district_id)

    monkeypatch.setattr("app.api.v1.districts.get_district_boundary", boom)
    resp = client.get("/api/v1/districts/xyz/boundary")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "DISTRICT_NOT_FOUND"


def test_insight_endpoint_uses_template_fallback(client, monkeypatch):
    # Ollama is unreachable in tests, so the fallback executes.
    resp = client.get("/api/v1/insight?district=kamrup&month=2026-06")
    assert resp.status_code == 200
    data = resp.json()
    assert data["district"] == "Kamrup"
    assert data["month"] == "2026-06"
    assert "0.58" in data["insight"]
    assert "421" in data["insight"]
    assert "4.7" in data["insight"]


def test_environment_service_exception_is_standardized_error(client, monkeypatch):
    from app.exceptions import InvalidMonthError

    def broken_ndvi(district_id, month):
        raise InvalidMonthError(month)

    monkeypatch.setattr(
        "app.services.environment_service.ndvi_service.calculate_ndvi", broken_ndvi
    )
    resp = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_MONTH_FORMAT"


def test_response_matches_standard_schema_contract(client):
    resp = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    data = resp.json()
    assert set(data.keys()) == {
        "district",
        "state",
        "month",
        "vegetation",
        "rainfall",
        "surface_water",
        "metadata",
        "warnings",
    }
    assert set(data["metadata"].keys()) == {
        "district_area_km2",
        "generated_at",
        "processing_time_ms",
        "cached",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Member A integration boundary tests
# ──────────────────────────────────────────────────────────────────────────────

def test_processing_not_connected_returns_200_with_null_and_warning(client, monkeypatch):
    """When Member A functions are not wired, /environment returns 200 with nulls + not-connected warnings."""
    from app.exceptions import ProcessingNotConnectedError

    def not_connected_ndvi(district_id, month):
        raise ProcessingNotConnectedError("app.processing.calculate_ndvi")

    def not_connected_rain(district_id, month):
        raise ProcessingNotConnectedError("app.processing.calculate_rainfall")

    def not_connected_water(district_id):
        raise ProcessingNotConnectedError("app.processing.calculate_water")

    monkeypatch.setattr("app.services.environment_service.ndvi_service.calculate_ndvi", not_connected_ndvi)
    monkeypatch.setattr("app.services.environment_service.rainfall_service.calculate_rainfall", not_connected_rain)
    monkeypatch.setattr("app.services.environment_service.water_service.calculate_water_coverage", not_connected_water)

    resp = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    assert resp.status_code == 200
    data = resp.json()
    assert data["vegetation"] is None
    assert data["rainfall"] is None
    assert data["surface_water"] is None
    assert len(data["warnings"]) == 3
    assert any("not connected" in w for w in data["warnings"])


def test_layer_not_connected_returns_503(client, monkeypatch, tmp_path):
    """When Member A's load_layer_raster is not wired, /layers returns 503 PROCESSING_NOT_CONNECTED."""
    from app.exceptions import ProcessingNotConnectedError

    # Create a fake district with a dummy raster dir so DataNotFoundError doesn't fire first.
    import json
    fake_boundary = tmp_path / "fake.geojson"
    fake_boundary.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}}]
    }), encoding="utf-8")

    import app.config as cfg
    monkeypatch.setitem(cfg.SUPPORTED_DISTRICTS, "fake", {
        "display_name": "Fake", "state": "XX", "boundary_path": str(fake_boundary),
    })

    sentinel_dir = tmp_path / "sentinel" / "2026-06" / "fake"
    sentinel_dir.mkdir(parents=True)
    (sentinel_dir / "B4.tif").touch()
    (sentinel_dir / "B8.tif").touch()
    monkeypatch.setattr(cfg, "sentinel2_path", lambda d, m: tmp_path / "sentinel" / m / d)

    monkeypatch.setattr(
        "app.services.layer_service.processing_adapter.load_layer",
        lambda *a, **kw: (_ for _ in ()).throw(
            ProcessingNotConnectedError("app.processing.load_layer_raster")
        ),
    )

    resp = client.get("/api/v1/layers/ndvi?district=fake&month=2026-06")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "PROCESSING_NOT_CONNECTED"


def test_adapter_forwards_to_wired_member_a_function(monkeypatch):
    """When a Member A function IS wired, the adapter forwards calls."""
    import app.processing as proc_mod

    def fake_calculate_ndvi(boundary_geom, raster_dir):
        return {"average_ndvi": 0.99, "pixel_count": 42, "source": "Sentinel-2"}

    monkeypatch.setattr(proc_mod, "calculate_ndvi", fake_calculate_ndvi, raising=False)

    from app.services import processing_adapter
    result = processing_adapter.call_ndvi("fake_geom", "/tmp/raster")
    assert result["average_ndvi"] == 0.99
    assert result["pixel_count"] == 42


def test_adapter_missing_data_raises_data_not_found():
    """Wired Member A adapters surface missing datasets, never fabricate values."""
    from app.exceptions import DataNotFoundError
    from app.services import processing_adapter

    with pytest.raises(DataNotFoundError):
        processing_adapter.call_ndvi("geom", "/nonexistent")
    with pytest.raises(DataNotFoundError):
        processing_adapter.call_rainfall("geom", "/nonexistent")
    with pytest.raises(DataNotFoundError):
        processing_adapter.call_water("geom", "/nonexistent")


def test_cache_different_keys_isolation(client, monkeypatch):
    """Different month values produce different cache entries; no cross-contamination."""
    values = {"2026-06": 0.58, "2025-12": 0.81}

    def ndvi_for_month(district_id, month):
        v = values.get(month, 0.0)
        return {"average_ndvi": v, "pixel_count": 100, "source": "Sentinel-2"}

    monkeypatch.setattr(
        "app.services.environment_service.ndvi_service.calculate_ndvi", ndvi_for_month
    )

    a = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    b = client.get("/api/v1/environment?district=kamrup&month=2025-12")

    assert a.json()["vegetation"]["average_ndvi"] == 0.58
    assert b.json()["vegetation"]["average_ndvi"] == 0.81

    a2 = client.get("/api/v1/environment?district=kamrup&month=2026-06")
    b2 = client.get("/api/v1/environment?district=kamrup&month=2025-12")
    assert a2.json()["metadata"]["cached"] is True
    assert b2.json()["metadata"]["cached"] is True
    assert a2.json()["vegetation"]["average_ndvi"] == 0.58
    assert b2.json()["vegetation"]["average_ndvi"] == 0.81


def test_rainfall_metric_matches_config_constant():
    from app.config import RAINFALL_METRIC
    from app.models.schemas import RainfallResult

    assert RainfallResult().metric == RAINFALL_METRIC
    assert RAINFALL_METRIC == "total_mm"