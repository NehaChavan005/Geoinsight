// GeoInsight API client — talks to the FastAPI backend.
//
// Dev default targets the local backend. On deployment set VITE_API_BASE_URL
// to the backend's public URL (no trailing slash).

const API_BASE_URL = (import.meta.env && import.meta.env.VITE_API_BASE_URL) || 'http://localhost:8000';

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    let code = null;
    try {
      const payload = await response.json();
      if (payload && payload.error) {
        code = payload.error.code;
        message = payload.error.message || `HTTP ${response.status}`;
      } else if (Array.isArray(payload && payload.detail)) {
        message = payload.detail.map((d) => d.msg).join('; ');
      } else if (payload && payload.detail) {
        message = payload.detail;
      }
    } catch { /* non-JSON error body */ }
    const error = new Error(message);
    error.status = response.status;
    error.code = code;
    throw error;
  }
  return response.json();
}

let districtsCache = null;

/**
 * List of supported districts: [{ id, display_name, state }].
 */
export async function fetchDistricts(force = false) {
  if (districtsCache && !force) return districtsCache;
  const json = await request('/api/v1/districts');
  districtsCache = Array.isArray(json.districts) ? json.districts : [];
  return districtsCache;
}

/**
 * Resolves a district display name (e.g. "Kamrup") to the backend id
 * (e.g. "kamrup") used in every API path/query.
 */
export async function getDistrictId(displayName) {
  try {
    const districts = await fetchDistricts();
    const match = districts.find((d) => d.display_name === displayName);
    if (match) return match.id;
  } catch { /* fall through to slug */ }
  return String(displayName).trim().toLowerCase();
}

/**
 * Raw GeoJSON Feature for a district boundary.
 */
export async function fetchBoundary(districtId) {
  return request(`/api/v1/districts/${encodeURIComponent(districtId)}/boundary`);
}

/**
 * Environment indicators for a district + YYYY-MM month.
 * Returns the full EnvironmentResponse payload:
 * { district, state, month, vegetation, rainfall, surface_water, metadata, warnings }
 */
export async function fetchEnvironmentData(districtId, month) {
  return request(
    `/api/v1/environment?district=${encodeURIComponent(districtId)}&month=${encodeURIComponent(month)}`,
  );
}

/**
 * Raster layer as a PNG overlay:
 * { layer_type, image: "data:image/png;base64,...", bounds: [[lat,lon],[lat,lon]] }
 * layerType must be one of: ndvi, rainfall, water.
 */
export async function fetchLayer(layerType, districtId, month) {
  return request(
    `/api/v1/layers/${encodeURIComponent(layerType)}?district=${encodeURIComponent(districtId)}&month=${encodeURIComponent(month)}`,
  );
}

/**
 * Natural-language insight:
 * { district, month, insight }
 */
export async function fetchInsight(districtId, month) {
  return request(
    `/api/v1/insight?district=${encodeURIComponent(districtId)}&month=${encodeURIComponent(month)}`,
  );
}