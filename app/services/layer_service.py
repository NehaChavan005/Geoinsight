"""Layer rendering service.

Builds the PNG overlay payload for the ``/api/v1/layers/{layer_type}``
endpoint.  Raster loading/clipping is delegated to Member A through
``processing_adapter.load_layer``; this service only normalizes the returned
array into a base64 PNG plus geographic bounds for a Leaflet ``ImageOverlay``.
No geospatial calculations are performed here.
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

from app.config import (
    get_chirps_path,
    get_sentinel_path,
    get_water_path,
    sentinel2_band_files,
)
from app.exceptions import DataNotFoundError
from app.services import processing_adapter
from app.services.boundary_service import (
    get_district_config_or_raise,
    get_district_geometry,
)

logger = logging.getLogger(__name__)

ALLOWED_LAYER_TYPES = ("ndvi", "water", "rainfall")

COLORMAPS = {
    "ndvi": "RdYlGn",
    "water": "Blues",
    "rainfall": "Blues",
}


def _resolve_raster_dir(layer_type: str, district_id: str, month: str) -> Path:
    if layer_type == "ndvi":
        red, nir = sentinel2_band_files(district_id, month)
        if not red.is_file() or not nir.is_file():
            raise DataNotFoundError("Sentinel-2", district_id, month)
        data_dir = get_sentinel_path(district_id, month)
    elif layer_type == "rainfall":
        data_dir = get_chirps_path(district_id, month)
        if not data_dir.exists() or not list(data_dir.glob("*.tif")):
            raise DataNotFoundError("CHIRPS", district_id, month)
    elif layer_type == "water":
        data_dir = get_water_path(district_id)
        if not data_dir.exists() or not list(data_dir.glob("*.tif")):
            raise DataNotFoundError("JRC Global Surface Water", district_id)
    else:
        raise DataNotFoundError(layer_type, district_id, month)
    return data_dir


def _render_band_to_png(arr, colormap: str | None = None) -> bytes:
    """Render a 2-D array to a PNG byte blob (matplotlib, with a pure-PNG fallback)."""
    import numpy as np

    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        vmin, vmax = 0.0, 1.0
    else:
        vmin, vmax = float(finite.min()), float(finite.max())
    if vmax == vmin:
        vmax = vmin + 1e-6

    norm = np.clip((arr - vmin) / (vmax - vmin), 0.0, 1.0)

    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import cm
        import matplotlib.pyplot as plt

        cmap = cm.get_cmap(colormap) if colormap else cm.viridis
        rgba = cmap(norm)
        with io.BytesIO() as buf:
            plt.imsave(buf, rgba, format="png")
            buf.seek(0)
            return buf.read()
    except ImportError:
        pass

    gray = (norm * 255).astype(np.uint8)

    def _chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
        import zlib

        block = chunk_type + chunk_data
        return len(chunk_data).to_bytes(4, "big") + block + (
            (zlib.crc32(block) & 0xFFFFFFFF).to_bytes(4, "big")
        )

    import zlib

    with io.BytesIO() as buf:
        h, w = gray.shape
        buf.write(b"\x89PNG\r\n\x1a\n")
        ihdr = w.to_bytes(4, "big") + h.to_bytes(4, "big") + b"\x08\x00\x00\x00\x00"
        buf.write(_chunk(b"IHDR", ihdr))
        raw = b"".join(b"\x00" + gray[y, :].tobytes() for y in range(h))
        buf.write(_chunk(b"IDAT", zlib.compress(raw)))
        buf.write(_chunk(b"IEND", b""))
        buf.seek(0)
        return buf.read()


def get_layer_payload(layer_type: str, district_id: str, month: str) -> dict:
    """Return ``{"layer_type", "image", "bounds"}`` for a raster overlay."""
    get_district_config_or_raise(district_id)
    geom = get_district_geometry(district_id)
    data_dir = _resolve_raster_dir(layer_type, district_id, month)

    try:
        array, bounds = processing_adapter.load_layer(layer_type, geom, data_dir)
    except Exception as exc:
        logger.exception("Layer load failed for %s/%s/%s", layer_type, district_id, month)
        raise exc

    png = _render_band_to_png(array, colormap=COLORMAPS.get(layer_type))
    encoded = base64.b64encode(png).decode("ascii")

    return {
        "layer_type": layer_type,
        "image": f"data:image/png;base64,{encoded}",
        "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
    }