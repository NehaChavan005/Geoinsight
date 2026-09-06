// Change this to your backend's URL when deployed (e.g., http://localhost:8000)
const API_BASE_URL = ''; 

/**
 * Fetches geospatial environmental data for a given district and month.
 * @param {string} district - e.g., "Kamrup"
 * @param {string} month - e.g., "2026-06"
 */
export async function fetchEnvironmentData(district, month) {
  try {
    const params = new URLSearchParams({ district, month });
    const response = await fetch(`${API_BASE_URL}/api/v1/environment?${params}`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.warn("Backend not reachable. Falling back to mock data.", error);
    
    // Fallback Mock Data for UI Testing
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          district: district,
          month: month,
          vegetation: { average_ndvi: (0.4 + Math.random() * 0.3).toFixed(2) },
          rainfall: { value_mm: Math.floor(300 + Math.random() * 200) },
          surface_water: { 
            coverage_percent: (4.0 + Math.random() * 2).toFixed(1), 
            area_km2: (35 + Math.random() * 10).toFixed(1) 
          },
          insight: `${district} recorded moderate to high vegetation health during ${month}, with substantial rainfall indicating active monsoon conditions. Surface water levels remain stable.`
        });
      }, 1500);
    });
  }
}
