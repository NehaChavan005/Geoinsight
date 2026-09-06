"""LLM insight generation service.

Calls a local Ollama model (e.g. ``llama3.2:3b``) with a strictly
template-constrained prompt that only allows the model to restate the
provided indicator values.  When Ollama is unreachable, errors, or returns
empty output, a deterministic template-based summary is used instead so the
demo never breaks on a machine without Ollama.

The generated text never invents statistics, trends, or claims not present
in the actual computed indicators.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://127.0.0.1:11434",
)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

_PROMPT_TEMPLATE = """You are an environmental analyst producing a short insight for a district report.
Use ONLY the numbers provided below. Do not invent, estimate, or claim any statistic, trend, or fact that is not present in these numbers.
If a field is null or unavailable, say it is unavailable. Keep the summary to 2-3 sentences and do not mention any other district, city, or time period.

District: {district}
State: {state}
Month: {month}
Average NDVI: {ndvi_value} (Sentinel-2, valid pixels: {pixel_count})
Rainfall: {rainfall_value} mm monthly total (CHIRPS, metric: total_mm)
Surface water: {water_percent}% of district area, {water_area_km2} km2 (JRC Global Surface Water)

Write the insight now:
"""


def _format_number(value, digits=2) -> str:
    if value is None:
        return "unavailable"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _build_prompt(district: str, state: str, month: str, indicators: dict) -> str:
    veg = indicators.get("vegetation") or {}
    rain = indicators.get("rainfall") or {}
    water = indicators.get("surface_water") or {}

    return _PROMPT_TEMPLATE.format(
        district=district,
        state=state,
        month=month,
        ndvi_value=_format_number(veg.get("average_ndvi")),
        pixel_count=veg.get("pixel_count", "unavailable"),
        rainfall_value=_format_number(rain.get("value_mm")),
        water_percent=_format_number(water.get("coverage_percent")),
        water_area_km2=_format_number(water.get("area_km2")),
    )


def _call_ollama(prompt: str, timeout_seconds: float = 10.0) -> str:
    payload = json.dumps(
        {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.0}}
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data.get("response") or "").strip()


def _fallback_insight(district: str, state: str, month: str, indicators: dict) -> str:
    veg = indicators.get("vegetation") or {}
    rain = indicators.get("rainfall") or {}
    water = indicators.get("surface_water") or {}

    parts = []
    if veg.get("average_ndvi") is not None:
        parts.append(
            f"average vegetation index (NDVI) of {_format_number(veg['average_ndvi'])} "
            f"(from {veg.get('pixel_count')} valid Sentinel-2 pixels)"
        )
    else:
        parts.append("vegetation health data unavailable")
    if rain.get("value_mm") is not None:
        parts.append(f"total rainfall of {_format_number(rain['value_mm'])} mm for the month")
    else:
        parts.append("rainfall data unavailable")
    if water.get("coverage_percent") is not None:
        parts.append(
            f"surface water covering {_format_number(water['coverage_percent'])}% "
            f"of the district ({_format_number(water['area_km2'])} km²)"
        )
    else:
        parts.append("surface water data unavailable")

    return (
        f"Environmental summary for {district} ({state}), {month}: {'; '.join(parts)}. "
        "These figures reflect the computed raster data for the selected month."
    )


def generate_insight(district: str, state: str, month: str, indicators: dict) -> dict:
    """Generate a data-grounded insight and return ``{"model", "fallback", "insight"}``."""
    prompt = _build_prompt(district, state, month, indicators)
    try:
        text = _call_ollama(prompt)
        if not text:
            raise RuntimeError("empty LLM response")
        logger.info("LLM insight generated via %s", OLLAMA_MODEL)
        return {"model": OLLAMA_MODEL, "fallback": False, "insight": text}
    except Exception as exc:
        logger.warning("Ollama unavailable (%s); using template fallback", exc)
        return {
            "model": "template",
            "fallback": True,
            "insight": _fallback_insight(district, state, month, indicators),
        }