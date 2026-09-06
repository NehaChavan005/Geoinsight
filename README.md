# GeoInsight

Geospatial Intelligence API and web application for Indian districts. Given a
district and a month (`YYYY-MM`), GeoInsight computes and visualizes three
environmental indicators:

| Indicator | Dataset | Reported as |
|-----------|---------|-------------|
| Vegetation health | Sentinel-2 (B8/NIR, B4/RED) | Average **NDVI** |
| Rainfall | CHIRPS | **Monthly total in mm** |
| Surface water | JRC Global Surface Water | **% of district area** and **area in km²** |

The system exposes results via a REST API and renders them on an interactive
web map (district boundary, NDVI and surface-water layers).

> **Generic by design.** `kamrup` (Assam) and `2026-06` are seeded **example**
> values for demos and tests. The API is **not** restricted to them — every
> district and month is a runtime parameter resolved through the configuration
> registry in `app/config.py`. Adding a new district requires **only** one
> registry entry plus its data files; no application code changes.

> **Team separation.** The repository is split between **Member A** (geospatial
> processing, data) and **Member B** (API, services, caching, frontend).
> Member B never imports or writes raster/geospatial algorithms directly;
> all processing flows through a single adapter seam.

---

## Repository layout

```
geoinsight/
├── requirements.txt
├── README.md
├── API.md                          # full API reference
├── architecture.md                 # Mermaid data-flow diagram
├── app/                            # FastAPI backend (Member B)
│   ├── main.py                     # app factory, CORS, error handlers
│   ├── config.py                   # district registry + env-configurable paths
│   ├── exceptions.py               # domain exception hierarchy
│   ├── api/v1/                     # districts, environment, layers, insight routers
│   ├── services/                   # thin service layer + processing_adapter
│   │   ├── processing_adapter.py   # ← Member A integration seam
│   │   ├── boundary_service.py     # district boundary + area
│   │   ├── ndvi_service.py         # adapter → Member A
│   │   ├── rainfall_service.py     # adapter → Member A
│   │   ├── water_service.py        # adapter → Member A
│   │   ├── layer_service.py        # PNG rendering (no geospatial calc)
│   │   ├── environment_service.py  # orchestration + partial-failure handling
│   │   └── insight_service.py      # Ollama + template fallback
│   ├── models/schemas.py           # Pydantic v2 response contract
│   └── cache/cache_manager.py      # SQLite cache keyed by (district, month)
├── app/processing/                 # Member A territory — NOT modified by Member B
├── data/
│   ├── boundaries/{district_id}.geojson
│   ├── sentinel2/{YYYY-MM}/{district_id}/*.tif
│   ├── chirps/{YYYY-MM}/{district_id}/*.tif
│   └── jrc_water/{district_id}/*.tif
├── frontend/                       # React/Leaflet web app
└── tests/                          # pytest (mocks all geospatial services)
```

---

## Integrating Member A Processing

**This section describes how Member A's functions are connected to the API.**

Member A owns `app/processing/`. Member B never calls processing functions
directly from API routes or services. Instead, all processing calls flow
through **`app/services/processing_adapter.py`** — the single integration seam.

### Expected Member A function signatures

Add these four functions to `app/process  ing/__init__.py`:

```python
# app/processing/__init__.py  (Member A writes this)

from app.config import RAINFALL_METRIC

def calculate_ndvi(boundary_geom, raster_dir) -> dict:
    """
    boundary_geom : shapely geometry, EPSG:4326
    raster_dir    : pathlib.Path to data/sentinel2/{YYYY-MM}/{district}/
    returns       : {"average_ndvi": float, "pixel_count": int, "source": "Sentinel-2"}
    """

def calculate_rainfall(boundary_geom, raster_dir) -> dict:
    """
    raster_dir : pathlib.Path to data/chirps/{YYYY-MM}/{district}/
    returns    : {"metric": RAINFALL_METRIC, "value_mm": float, "source": "CHIRPS"}
    """

def calculate_water(boundary_geom, raster_dir, district_area_km2) -> dict:
    """
    raster_dir       : pathlib.Path to data/jrc_water/{district}/
    district_area_km2: float (from boundary_service.get_district_area_km2)
    returns          : {"coverage_percent": float, "area_km2": float,
                        "source": "JRC Global Surface Water"}
    """

def load_layer_raster(layer_type, boundary_geom, raster_dir) -> tuple:
    """
    layer_type : "ndvi" | "water" | "rainfall"
    returns    : (2-D numpy.ndarray, bounds) where bounds has
                 .left, .right, .top, .bottom attributes
    """
```

### How the adapter wires them

```
API Route (app/api/v1/*)
    ↓
app/services/ndvi_service.py    (thin adapter)
    ↓
app/services/processing_adapter.py   ← calls getattr("app.processing", "calculate_ndvi")
    ↓
app/processing/__init__.py      (Member A's implementation)
```

Until Member A adds the functions, `processing_adapter` raises
`ProcessingNotConnectedError` and every indicator returns `null` with a
warning — no values are ever fabricated.

### Wiring checklist

1. Member A implements the four functions above in `app/processing/__init__.py`.
2. Member A places raster files in the correct `data/` subdirectories.
3. Member A adds the boundary GeoJSON to `data/boundaries/`.
4. Member B adds the district to `SUPPORTED_DISTRICTS` in `app/config.py`.
5. No changes are needed in API routers, cache, or the response contract.

---

## Backend setup

### Prerequisites

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# or: source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Run

```bash
# Development (auto-reload)
uvicorn app.main:app --reload

# Production (see deployment section)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API docs

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

### Run tests

```bash
pytest -q
```

Tests mock all geospatial services and use synthetic data — no real satellite
raster files are required.

---

## Environment configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEOINSIGHT_DATA_DIR` | `./data` | Root data directory (boundaries, rasters) |
| `GEOINSIGHT_CACHE_DB` | `{DATA_DIR}/cache.sqlite3` | SQLite cache path |
| `GEOINSIGHT_CORS_ORIGINS` | (see below) | Extra comma-separated CORS origins |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model to use for insight generation |

Default CORS origins (always allowed): `localhost`, `localhost:3000`,
`127.0.0.1`, `127.0.0.1:3000`, `localhost:5173`, `127.0.0.1:5173`.
Add production origins via `GEOINSIGHT_CORS_ORIGINS=https://app.example.com`.

---

## Rainfall metric

The rainfall statistic is the **monthly total in mm**, defined in exactly one
place:

```python
# app/config.py
RAINFALL_METRIC = "total_mm"
```

The `RainfallResult` schema and Member A's `calculate_rainfall` function both
reference this constant.  The `metric` field in every `/environment` response
is always `"total_mm"`.

CHIRPS rasters are expected as **monthly composites** (per-pixel total for the
month).  Member A's processing function is responsible for the sum; this
service layer does not decide an alternative metric.

---

## Example curl commands

> These are **example/demo requests** using the seeded Kamrup configuration and
> June 2026. The API is not restricted to these values.

```bash
# List supported districts
curl "http://127.0.0.1:8000/api/v1/districts"

# Environmental indicators (will return null + warnings until Member A is wired)
curl "http://127.0.0.1:8000/api/v1/environment?district=kamrup&month=2026-06"

# District boundary (GeoJSON)
curl "http://127.0.0.1:8000/api/v1/districts/kamrup/boundary"

# Raster layer as a base64 PNG + bounds
curl "http://127.0.0.1:8000/api/v1/layers/ndvi?district=kamrup&month=2026-06"

# AI insight (Ollama or template fallback)
curl "http://127.0.0.1:8000/api/v1/insight?district=kamrup&month=2026-06"

# Health check
curl "http://127.0.0.1:8000/healthz"
```

---

## API reference

See [`API.md`](API.md) for full endpoint documentation (params, schemas,
errors, example responses).

---

## Response contract

`GET /api/v1/environment` returns a stable contract even when a dataset is
missing or processing is not connected:

```json
{
  "district": "Kamrup",
  "state": "Assam",
  "month": "2026-06",
  "vegetation": null,
  "rainfall": null,
  "surface_water": null,
  "metadata": {
    "district_area_km2": null,
    "generated_at": "2026-09-06T14:00:00Z",
    "processing_time_ms": 42,
    "cached": false
  },
  "warnings": [
    "Sentinel-2 dataset is unavailable for this district/month. (Geospatial processing is not connected yet.)",
    "CHIRPS rainfall dataset is unavailable for this district/month. (Geospatial processing is not connected yet.)",
    "JRC Global Surface Water data is unavailable for the requested district. (Geospatial processing is not connected yet.)"
  ]
}
```

Once Member A's functions are connected and raster files are present, all
indicator fields will contain real computed values.  The numeric examples in
the JSON schema docs (e.g. `0.58`, `421`, `4.7`) are **illustrative only**.

---

## Caching

Computed `/environment` results are stored in a SQLite cache keyed by
`(district_id, month)`.  A second request for the same key skips
recomputation and returns `"cached": true` in the metadata.

Cache database location: `{GEOINSIGHT_DATA_DIR}/cache.sqlite3`
(override with `GEOINSIGHT_CACHE_DB`).

---

## Adding a new district

No code changes are required outside of configuration and data files:

1. **Add the boundary file** — `data/boundaries/{district_id}.geojson`
   (a GeoJSON FeatureCollection or Feature).
2. **Add a registry entry** in `app/config.py`:

   ```python
   SUPPORTED_DISTRICTS["new_district"] = {
       "display_name": "...",
       "state": "...",
       "boundary_path": "data/boundaries/new_district.geojson",
   }
   ```

3. **Add the dataset files** for the months you want (see layout above):
   - `data/sentinel2/{YYYY-MM}/new_district/B4.tif` and `B8.tif`
   - `data/chirps/{YYYY-MM}/new_district/*.tif`
   - `data/jrc_water/new_district/*.tif`

No changes are needed in API routers, cache, service orchestration, schemas,
or the frontend API contract.

---

## AI insight

`GET /api/v1/insight` generates a short environmental summary. It calls a
local Ollama model (`llama3.2:3b` by default) over HTTP with a strictly
template-constrained prompt that only allows the model to restate the computed
indicator values — no invented statistics, trends, or facts.

If Ollama is unreachable or errors, a **deterministic template-based fallback**
summarizes the same numbers, so the demo never breaks on a machine without
Ollama.

---

## Deployment

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Ensure `GEOINSIGHT_DATA_DIR` points at a directory with the required data
files.  Use `GEOINSIGHT_CORS_ORIGINS` to add your production frontend
origin.

---

## Frontend

The `frontend/` directory contains the React + Leaflet app. It consumes the
endpoints above: `/districts` populates the dropdown, `/environment` renders
the stats panel, `/districts/{id}/boundary` draws the boundary, `/layers/{type}`
draws overlays, and `/insight` shows the insight card.