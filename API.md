# GeoInsight API Reference

Base URL: `http://127.0.0.1:8000`

All endpoints serve standardized JSON. Errors always use:

```json
{ "error": { "code": "...", "message": "..." } }
```

Interactive docs: `/docs` (Swagger), `/redoc` (ReDoc), `/openapi.json`.

> All example requests below use the seeded `kamrup` district and June 2026 —
> **example values, not the only supported input.** Any registered district and
> any valid `YYYY-MM` month are accepted.

---

## Conventions

- **district**: lowercase id from the config registry (`GET /api/v1/districts`).
- **month**: `YYYY-MM`, e.g. `2026-06`, `2025-12`, `2027-01`.
- **rainfall metric**: always `total_mm` (monthly total rainfall). Defined once
  in `app/config.py::RAINFALL_METRIC`.

---

## `GET /healthz`

Liveness check. Does not depend on any geospatial data.

**Response 200**

```json
{ "status": "ok" }
```

---

## `GET /api/v1/districts`

Lists every district in the config registry.

**Response 200**

```json
{
  "districts": [
    { "id": "kamrup", "display_name": "Kamrup", "state": "Assam" }
  ]
}
```

---

## `GET /api/v1/districts/{district_id}/boundary`

Returns the district boundary as raw GeoJSON (a `Feature`), suitable for a
Leaflet `GeoJSON` layer.

**Response 200**

```json
{
  "type": "Feature",
  "properties": { "district": "Kamrup" },
  "geometry": { "type": "Polygon", "coordinates": [ ... ] }
}
```

**Errors**

| Status | Code | When |
|--------|------|------|
| 404 | `DISTRICT_NOT_FOUND` | Unknown district id |
| 503 | `DATA_NOT_FOUND` | Boundary file absent or empty |

---

## `GET /api/v1/environment?district={id}&month={YYYY-MM}`

Main endpoint: computes (or returns cached) all three indicators. If an
individual dataset is missing, its field is `null` and the response still
returns HTTP 200 with the issue listed in `warnings`.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `district` | string | Lowercase district id, e.g. `kamrup` |
| `month` | string | `YYYY-MM`, e.g. `2026-06` |

**Response 200 (complete data)**

```json
{
  "district": "Kamrup",
  "state": "Assam",
  "month": "2026-06",
  "vegetation": { "average_ndvi": 0.58, "source": "Sentinel-2", "pixel_count": 184532 },
  "rainfall": { "metric": "total_mm", "value_mm": 421.0, "source": "CHIRPS" },
  "surface_water": { "coverage_percent": 4.7, "area_km2": 37.2, "source": "JRC Global Surface Water" },
  "metadata": {
    "district_area_km2": 792.0,
    "generated_at": "2026-09-06T10:00:00Z",
    "processing_time_ms": 842,
    "cached": false
  },
  "warnings": []
}
```

Value fields containing numbers (`0.58`, `421`, `4.7`, `792.0`) are
**illustrative examples only** — they always come from Member A's real raster
computations (or the cache of one). While Member A's processing functions are
unwired, every indicator returns `null` and each warning ends with
`"(Geospatial processing is not connected yet.)"`.

**Response 200 (partial/no data)**

```json
{
  "district": "Kamrup",
  "state": "Assam",
  "month": "2026-06",
  "vegetation": null,
  "rainfall": null,
  "surface_water": null,
  "metadata": { "district_area_km2": null, "generated_at": "...", "processing_time_ms": 43, "cached": false },
  "warnings": [
    "Sentinel-2 dataset is unavailable for this district/month. (Geospatial processing is not connected yet.)",
    "CHIRPS rainfall dataset is unavailable for this district/month. (Geospatial processing is not connected yet.)",
    "JRC Global Surface Water data is unavailable for the requested district. (Geospatial processing is not connected yet.)"
  ]
}
```

**Errors**

| Status | Code | When |
|--------|------|------|
| 404 | `DISTRICT_NOT_FOUND` | Unknown district |
| 422 | `INVALID_MONTH_FORMAT` | Month is not `YYYY-MM` |

Other status codes (e.g. `503 DATA_NOT_FOUND`, `503 PROCESSING_NOT_CONNECTED`)
are only used for genuine request-level failures; missing **individual
datasets never fail** the `/environment` request.

---

## `GET /api/v1/layers/{layer_type}?district={id}&month={YYYY-MM}`

Returns a raster overlay as a base64 PNG plus geographic bounds, ready for a
Leaflet `ImageOverlay`. `layer_type` is one of `ndvi`, `water`, `rainfall`.
`month` is optional for `water` (JRC data is not monthly).

**Response 200**

```json
{
  "layer_type": "ndvi",
  "image": "data:image/png;base64,iVBORw0KGgo...",
  "bounds": [[25.90, 90.60], [26.30, 91.40]]
}
```

**Errors**

| Status | Code | When |
|--------|------|------|
| 404 | `DISTRICT_NOT_FOUND` | Unknown district id |
| 422 | `INVALID_LAYER_TYPE` | `layer_type` not one of ndvi/water/rainfall |
| 503 | `DATA_NOT_FOUND` | The raster for that district/month is missing |
| 503 | `PROCESSING_NOT_CONNECTED` | Member A's layer loading function is not wired |

---

## `GET /api/v1/insight?district={id}&month={YYYY-MM}`

Returns a short, data-grounded environmental summary. Reuses the same cached
environment data as `/environment`; uses a local Ollama model, with a
deterministic template fallback when Ollama is unavailable.

**Response 200**

```json
{
  "district": "Kamrup",
  "month": "2026-06",
  "insight": "Environmental summary for Kamrup (Assam), 2026-06: average vegetation index (NDVI) of 0.58 ..."
}
```

**Errors**

| Status | Code | When |
|--------|------|------|
| 404 | `DISTRICT_NOT_FOUND` | Unknown district |
| 422 | `INVALID_MONTH_FORMAT` | Month is not `YYYY-MM` |

---

## Error codes

| Code | HTTP | Meaning |
|------|------|---------|
| `DISTRICT_NOT_FOUND` | 404 | District id is not in the registry |
| `INVALID_MONTH_FORMAT` | 422 | Month is not `YYYY-MM` |
| `INVALID_LAYER_TYPE` | 422 | `layer_type` not in ndvi/water/rainfall |
| `DATA_NOT_FOUND` | 503 | Underlying dataset file missing or empty |
| `PROCESSING_NOT_CONNECTED` | 503 | Member A's geospatial processing functions are not yet wired |
| `PROCESSING_ERROR` | 503 | Unexpected failure inside the processing layer |
| `HTTP_ERROR` | varies | Fallback for unhandled HTTPException details |

Response shape for every error:

```json
{ "error": { "code": "...", "message": "..." } }
```

---

## Environment configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEOINSIGHT_DATA_DIR` | `./data` | Root data directory |
| `GEOINSIGHT_CACHE_DB` | `{DATA_DIR}/cache.sqlite3` | SQLite cache path |
| `GEOINSIGHT_CORS_ORIGINS` | (localhost:3000, :5173) | Extra comma-separated CORS origins |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama base URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model for insight generation |

---

## Example requests

```bash
curl "http://127.0.0.1:8000/healthz"
curl "http://127.0.0.1:8000/api/v1/districts"
curl "http://127.0.0.1:8000/api/v1/environment?district=kamrup&month=2026-06"
curl "http://127.0.0.1:8000/api/v1/districts/kamrup/boundary"
curl "http://127.0.0.1:8000/api/v1/layers/water?district=kamrup&month=2026-06"
curl "http://127.0.0.1:8000/api/v1/insight?district=kamrup&month=2026-06"
```