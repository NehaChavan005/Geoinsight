/**
 * Returns a color based on NDVI value (-1 to 1)
 */
export const getNdviColor = (ndviValue) => {
  if (ndviValue < 0.1) return '#e5e7eb'; // Barren / Rock / Snow (Gray)
  if (ndviValue < 0.2) return '#fde047'; // Sparse Vegetation (Yellow)
  if (ndviValue < 0.4) return '#a3e635'; // Moderate Vegetation (Light Green)
  if (ndviValue < 0.6) return '#22c55e'; // Dense Vegetation (Green)
  return '#14532d'; // Very Dense Forest (Dark Green)
};

/**
 * Returns a color based on Water Occurrence percentage (0 to 100)
 */
export const getWaterColor = (occurrence) => {
  if (occurrence < 10) return '#bae6fd'; // Light blue
  if (occurrence < 50) return '#38bdf8'; // Mid blue
  if (occurrence < 80) return '#0284c7'; // Deep blue
  return '#082f49'; // Permanent water (Navy)
};


