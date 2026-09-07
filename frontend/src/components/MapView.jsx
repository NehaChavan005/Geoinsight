import { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, ImageOverlay, useMap } from 'react-leaflet';
import { motion } from 'framer-motion';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../styles/MapView.css';
import { getDistrictId, fetchBoundary, fetchLayer } from '../services/apiClient';

// Re-fits the map viewport whenever the selected district boundary changes.
function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && map) map.fitBounds(bounds, { padding: [20, 20] });
  }, [map, bounds]);
  return null;
}

function Legend({ isLightMode }) {
  const subText = isLightMode ? 'text-slate-500' : 'text-slate-400';
  const overlayGlass = isLightMode
    ? 'bg-white/80 backdrop-blur-xl border border-sky-100 shadow-[0_8px_30px_rgba(14,165,233,0.15)]'
    : 'bg-slate-900/80 backdrop-blur-xl border border-white/10 shadow-[0_8px_30px_rgba(0,0,0,0.5)]';

  return (
    <div className={`absolute bottom-4 right-4 z-[1000] p-4 rounded-xl flex flex-col gap-4 pointer-events-none ${overlayGlass}`}>
      <h4 className={`text-[10px] font-bold uppercase tracking-widest border-b border-current pb-2 opacity-60 ${isLightMode ? 'text-slate-800' : 'text-white'}`}>
        NDVI / Water Scale
      </h4>

      <div className="flex items-center gap-4">
        <div className="w-3 h-24 rounded-full bg-gradient-to-t from-yellow-900 via-emerald-500 to-green-300 shadow-inner" />
        <div className={`flex flex-col justify-between h-24 text-xs font-medium ${subText}`}>
          <span>High NDVI</span>
          <span>Moderate</span>
          <span>Barren</span>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <div className="w-4 h-4 rounded-md bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
        <span className={`text-xs font-semibold ${isLightMode ? 'text-slate-800' : 'text-white'}`}>Surface Water</span>
      </div>
    </div>
  );
}

function LayersBox({ isLightMode, layers, loading, errors, onToggle }) {
  const subText = isLightMode ? 'text-slate-500' : 'text-slate-400';
  const overlayGlass = isLightMode
    ? 'bg-white/80 backdrop-blur-xl border border-sky-100 shadow-[0_8px_30px_rgba(14,165,233,0.15)]'
    : 'bg-slate-900/80 backdrop-blur-xl border border-white/10 shadow-[0_8px_30px_rgba(0,0,0,0.5)]';

  const failedKeys = Object.keys(errors).filter((k) => errors[k]);

  return (
    <div className={`absolute top-4 left-4 z-[1000] p-4 rounded-xl flex flex-col gap-3 min-w-[172px] pointer-events-auto ${overlayGlass}`}>
      <h4 className={`text-xs font-bold uppercase tracking-widest mb-1 flex items-center gap-2 ${isLightMode ? 'text-slate-800' : 'text-white'}`}>
        Map Layers
      </h4>
      <div className="flex flex-col gap-2">
        {Object.keys(layers).map((layer) => (
          <label
            key={layer}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <input
              type="checkbox"
              checked={layers[layer]}
              onChange={() => onToggle(layer)}
              disabled={loading[layer]}
              className={`w-4 h-4 rounded border accent-cyan-500 cursor-pointer transition-colors ${
                isLightMode ? 'bg-sky-50 border-sky-200' : 'bg-slate-800 border-slate-600'
              }`}
            />
            <span className={`text-sm font-medium transition-colors group-hover:text-cyan-500 ${layers[layer] ? (isLightMode ? 'text-slate-800' : 'text-white') : subText}`}>
              {layer}
              {loading[layer] && (
                <span className="ml-2 w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin inline-block align-middle" />
              )}
            </span>
          </label>
        ))}
      </div>
      {failedKeys.length > 0 && (
        <p className={`text-[10px] leading-snug ${isLightMode ? 'text-rose-600' : 'text-rose-300'}`}>
          Could not load {failedKeys.join(', ')}. Check the backend and toggle again.
        </p>
      )}
    </div>
  );
}

const LAYER_KEYS = { NDVI: 'ndvi', 'Surface Water': 'water', Rainfall: 'rainfall' };

export default function MapView({ data, district, month, mapRef, isLightMode, fill = false }) {
  const [layers, setLayers] = useState({
    Boundary: true,
    'Surface Water': false,
    NDVI: false,
    Rainfall: false,
  });
  const [assamGeo, setAssamGeo] = useState(null);
  const [boundaryGeo, setBoundaryGeo] = useState(null);
  const [overlays, setOverlays] = useState({ ndvi: null, water: null, rainfall: null });
  const [overlayLoading, setOverlayLoading] = useState({ ndvi: false, water: false, rainfall: false });
  const [overlayErrors, setOverlayErrors] = useState({ ndvi: null, water: null, rainfall: null });

  useEffect(() => {
    fetch('/assam_districts.geojson')
      .then((response) => response.json())
      .then((result) => setAssamGeo(result))
      .catch((error) => console.error('Error loading Assam map data:', error));
  }, []);

  // Real district boundary straight from the backend.
  useEffect(() => {
    let cancelled = false;
    setBoundaryGeo(null);
    setOverlays({ ndvi: null, water: null, rainfall: null });
    setOverlayErrors({ ndvi: null, water: null, rainfall: null });
    getDistrictId(district)
      .then((districtId) => fetchBoundary(districtId))
      .then((feature) => {
        if (!cancelled) setBoundaryGeo(feature);
      })
      .catch((error) => {
        if (!cancelled) console.error('Boundary load failed:', error);
      });
    return () => {
      cancelled = true;
    };
  }, [district]);

  const boundaryBounds = useMemo(() => {
    if (!boundaryGeo) return null;
    try {
      return L.geoJSON(boundaryGeo).getBounds();
    } catch {
      return null;
    }
  }, [boundaryGeo]);

  // Lazily loads a raster layer PNG from the backend when toggled on.
  const loadLayer = async (layerType) => {
    setOverlayLoading((prev) => ({ ...prev, [layerType]: true }));
    try {
      const districtId = await getDistrictId(district);
      const payload = await fetchLayer(layerType, districtId, month);
      setOverlays((prev) => ({ ...prev, [layerType]: payload }));
      setOverlayErrors((prev) => ({ ...prev, [layerType]: null }));
    } catch (error) {
      console.error(`Layer ${layerType} failed:`, error);
      setOverlayErrors((prev) => ({ ...prev, [layerType]: error.message || 'request failed' }));
    } finally {
      setOverlayLoading((prev) => ({ ...prev, [layerType]: false }));
    }
  };

  const toggleLayer = (name) => {
    setLayers((prev) => ({ ...prev, [name]: !prev[name] }));
    const layerType = LAYER_KEYS[name];
    if (layerType && !overlays[layerType] && !overlayLoading[layerType]) {
      loadLayer(layerType);
    }
  };

  const tileUrl = isLightMode
    ? 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'
    : 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';

  const assamStyle = {
    color: isLightMode ? '#0ea5e9' : '#06b6d4',
    weight: 1,
    fillColor: isLightMode ? '#38bdf8' : '#06b6d4',
    fillOpacity: isLightMode ? 0.08 : 0.05,
    dashArray: '4, 4',
  };

  const districtStyle = {
    color: isLightMode ? '#e11d48' : '#f43f5e',
    weight: 3,
    fillColor: isLightMode ? '#e11d48' : '#f43f5e',
    fillOpacity: 0.08,
    className: 'boundary-glow',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.7, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className={`relative w-full overflow-hidden rounded-2xl pointer-events-auto ${fill ? 'h-full max-h-none' : 'h-[434px] max-h-[434px]'}`}
      ref={mapRef}
    >
      <MapContainer
        center={[26.15, 91.38]}
        zoom={9}
        data-testid="map"
        style={{ height: '100%', width: '100%', background: isLightMode ? '#f8fafc' : '#0f172a' }}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer url={tileUrl} key={isLightMode ? 'tile-light' : 'tile-dark'} />
        <FitBounds bounds={boundaryBounds} />

        {/* Real raster overlays from the backend, clipped to the district */}
        {layers.NDVI && overlays.ndvi && (
          <ImageOverlay url={overlays.ndvi.image} bounds={overlays.ndvi.bounds} opacity={0.75} />
        )}
        {layers['Surface Water'] && overlays.water && (
          <ImageOverlay url={overlays.water.image} bounds={overlays.water.bounds} opacity={0.55} />
        )}
        {layers.Rainfall && overlays.rainfall && (
          <ImageOverlay url={overlays.rainfall.image} bounds={overlays.rainfall.bounds} opacity={0.6} />
        )}

        {/* State context boundaries */}
        {layers.Boundary && assamGeo && (
          <GeoJSON
            key={isLightMode ? 'assam-light' : 'assam-dark'}
            data={assamGeo}
            pathOptions={assamStyle}
          />
        )}

        {/* Real district boundary from the backend, highlighted on top */}
        {layers.Boundary && boundaryGeo && (
          <GeoJSON
            key={isLightMode ? 'boundary-light' : 'boundary-dark'}
            data={boundaryGeo}
            pathOptions={districtStyle}
            onEachFeature={(feature, layer) => layer.bindPopup(buildPopup(feature, isLightMode))}
          />
        )}
      </MapContainer>

      <LayersBox
        isLightMode={isLightMode}
        layers={layers}
        loading={overlayLoading}
        errors={overlayErrors}
        onToggle={toggleLayer}
      />
      <Legend isLightMode={isLightMode} />
    </motion.div>
  );
}

function buildPopup(feature, isLightMode) {
  const props = feature.properties || {};
  const textColor = isLightMode ? '#0f172a' : '#e0f2fe';
  const mutedColor = isLightMode ? '#64748b' : '#bae6fd';
  const name = props.district || props.name || 'Region';
  return `
    <div class="custom-popup">
      <h4 style="font-weight:bold;color:${textColor};margin-bottom:4px;">${name}</h4>
      <p style="font-size:12px;color:${mutedColor};">Kamrup district boundary.</p>
    </div>
  `;
}