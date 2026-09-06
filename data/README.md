# GeoInsight Data

Member A — Geospatial Data & Processing. Assam, India — all 33 districts
(the original Kamrup analysis is kept as a regression check).

## Directory layout

```
data/
├── assam_district_results.json # 33-district final results (NDVI/rainfall/water)
├── boundaries/
│   ├── kamrup.geojson          # original test-case boundary (regression)
│   ├── assam_state.geojson     # Assam outline (GEE GAUL level 1)
│   └── assam/
│       ├── assam_districts.geojson    # all 33 Assam districts (GeoBoundaries v5)
│       └── <District>.geojson         # one single-feature file per district
├── sentinel2/
│   ├── sentinel2_B04_june2026.tif     # Kamrup-bbox test-case B4 composite
│   └── sentinel2_B08_june2026.tif     # Kamrup-bbox test-case B8 composite
├── rainfall/
│   ├── chirps_june2026.tif            # CHIRPS June 2026, Kamrup bbox (regression)
│   └── chirps_june2026_assam.tif      # CHIRPS June 2026, all Assam
└── water/
    ├── jrc_water.tif                  # JRC occurrence, Kamrup bbox (regression)
    └── jrc_water_assam.tif            # JRC occurrence, all Assam
```

The raster files are produced by the Earth Engine pipeline
(`app/processing/gee_export.py`, Drive folder `GeoInsight` -> local
`data/<group>/`). No placeholder or fake TIFFs are committed.

## 1. Boundaries

- Assam outline: GEE `FAO/GAUL/2015/level1` (`assam_state.geojson`).
- District boundaries: GeoBoundaries v5 (`lgdirectory.gov.in` source) India ADM2,
  33 modern Assam districts, EPSG:4326 (`data/boundaries/assam/`).
- Kamrup test case: original GeoBoundaries ADM2 feature
  (`data/boundaries/kamrup.geojson`).

## 2. Sentinel-2 (NDVI)

- Dataset: `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2 L2A Surface Reflectance)
- Bands: B4 (Red, 10 m), B8 (NIR, 10 m)
- Period: 2026-06-01 to 2026-06-30
- Processing: cloudy-pixel filtering, QA60 cloud/cirrus masking, June median
  composite at 10 m
- NDVI formula: `(B8 - B4) / (B8 + B4)`
- Metric: NDVI = mean district NDVI from Sentinel-2 (June 2026).

## 3. Rainfall (CHIRPS)

- Dataset: `UCSB-CHG/CHIRPS/DAILY`
- Period: 2026-06-01 to 2026-06-30
- Metric: Rainfall = district-average (zonal MEAN) June accumulated rainfall in
  mm. The raster holds the sum of the daily `precipitation` bands; the
  district figure is the mean of those monthly-total pixels.
- Note: it is NOT a pixel-count sum, and not an average daily figure.

## 4. Water (JRC Global Surface Water)

- Dataset: `JRC/GSW1_4/GlobalSurfaceWater`
- Band: `occurrence` (0-100); threshold >= 50 % counts a pixel as water
  (configurable)
- Resolution: 30 m
- Metrics: water pixel count, water area in km², and water coverage %
  (water pixels / valid pixels).
- IMPORTANT: JRC Global Surface Water v1.4 is historical surface-water
  occurrence through 2021; the water metric is a historical/reference coverage,
  NOT a June 2026 observation. Only Sentinel-2 NDVI is a June 2026 measurement.

## 5. Processing stack

- `rasterio` / `rasterio.mask` — reading and clipping rasters
- `rasterstats` — zonal statistics over the boundary (zonal MEAN for rainfall)
- `geopandas` — boundary loading and CRS handling
- `numpy` — numerical array operations (NDVI, water classification)
- `earthengine-api` — state-wide Sentinel-2 NDVI reduction per district

## 6. Assam-wide district analysis

The processing is district-agnostic: `app/processing/district_analysis.py`
iterates every boundary in `data/boundaries/assam/assam_districts.geojson` and
computes per-district mean NDVI (GEE), June 2026 rainfall (zonal mean, mm),
and water pixels / area / coverage % from the state-wide rasters. Output:
`data/assam_district_results.json` (one row per district).

```bash
python app/processing/district_analysis.py
```

The original Kamrup results are reused only as a regression check
(`validate_member_a.py`; NDVI 0.2635, rainfall 273.68 mm, water area
133.48 km²). Small differences vs. the Assam-wide Kamrup row are expected
because the boundary source/scope and raster extents differ.

## Acquisition commands

```bash
# one-time auth (browser flow), never stored in the repo
python -c "import ee; ee.Authenticate()"

# launch Kamrup-bbox exports (Sentinel-2 + CHIRPS + JRC) to Drive/GeoInsight
python app/processing/gee_export.py all
```

Then download the GeoTIFFs from Google Drive into the matching `data/<group>/`
folder.

## Validation

```bash
python app/processing/validate_member_a.py      # Kamrup regression check
python app/processing/district_analysis.py      # full Assam-wide report (+results)
```