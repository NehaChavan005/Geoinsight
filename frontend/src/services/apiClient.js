// Change this to your backend's URL when deployed (e.g., http://localhost:8000)
const API_BASE_URL = 'http://localhost:8000';

/**
 * Fetches geospatial environmental data for a given district and month.
 * @param {string} district - e.g., "Kamrup"
 * @param {string} month - e.g., "2026-06"
 * @returns {Promise<object>} The `data` payload: { stats, ai_insight, metadata }
 */
export async function fetchEnvironmentData(district, month) {
  try {
    const params = new URLSearchParams({ district, month });
    const response = await fetch(`${API_BASE_URL}/api/v1/environment?${params}`);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    const json = await response.json();
    if (json.status === 'success' && json.data) {
      return json.data;
    }
    throw new Error('API Error: invalid payload');
  } catch (error) {
    console.warn('Backend not reachable. Falling back to mock data.', error);

    // Fallback Mock Data for UI Testing (matches /api/v1/environment contract)
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          stats: {
            average_ndvi: (0.4 + Math.random() * 0.3).toFixed(2),
            total_rainfall_mm: Math.floor(300 + Math.random() * 200),
            surface_water_coverage_pct: (4.0 + Math.random() * 2).toFixed(1),
            surface_water_area_km2: (35 + Math.random() * 10).toFixed(1),
          },
          ai_insight: {
            summary: `${district} recorded moderate to high vegetation health during ${month}, with substantial rainfall indicating active monsoon conditions. Surface water levels remain stable.`,
          },
          metadata: {
            districts_analyzed: '1 / 35',
            raster_scenes: '12',
            processing: 'GPU · CUDA',
            latency_seconds: '1.2',
          },
        });
      }, 1500);
    });
  }
}