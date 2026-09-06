import { useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { motion } from 'framer-motion';
import 'leaflet/dist/leaflet.css';
import '../styles/MapView.css';

const kamrupBoundary = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'Kamrup' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [90.7, 25.9],
            [91.3, 25.8],
            [91.9, 26.0],
            [92.0, 26.4],
            [91.5, 26.8],
            [90.7, 26.6],
            [90.7, 25.9],
          ],
        ],
      },
    },
  ],
};

const waterRegions = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'Brahmaputra' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [90.95, 26.35],
            [91.2, 26.25],
            [91.5, 26.3],
            [91.8, 26.28],
            [91.9, 26.38],
            [91.55, 26.45],
            [91.2, 26.42],
            [90.95, 26.35],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { name: 'Deepor Beel' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [91.45, 26.12],
            [91.5, 26.1],
            [91.55, 26.13],
            [91.52, 26.16],
            [91.46, 26.15],
            [91.45, 26.12],
          ],
        ],
      },
    },
  ],
};

const vegetationRegions = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'Vegetation' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [91.0, 26.55],
            [91.3, 26.6],
            [91.5, 26.65],
            [91.6, 26.72],
            [91.35, 26.78],
            [91.05, 26.72],
            [91.0, 26.55],
          ],
        ],
      },
    },
  ],
};

function WaterRippleLayer({ isLightMode }) {
  return (
    <>
      <GeoJSON
        data={waterRegions}
        pathOptions={{
          color: 'rgba(56,189,248,0.0)',
          weight: 0,
          fillColor: '#38bdf8',
          fillOpacity: 0.4,
          className: 'water-ripple',
        }}
        key={isLightMode ? 'water-light' : 'water-dark'}
      />
      <div className="water-ripple-waves" />
    </>
  );
}

function GrassWindLayer({ isLightMode }) {
  return (
    <GeoJSON
      data={vegetationRegions}
      pathOptions={{
        color: 'rgba(34,197,94,0.0)',
        weight: 0,
        fillColor: '#22c55e',
        fillOpacity: 0.45,
        className: 'grass-wind',
      }}
      key={isLightMode ? 'grass-light' : 'grass-dark'}
    />
  );
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

function LayersBox({ isLightMode, layers, onToggle }) {
  const subText = isLightMode ? 'text-slate-500' : 'text-slate-400';
  const overlayGlass = isLightMode
    ? 'bg-white/80 backdrop-blur-xl border border-sky-100 shadow-[0_8px_30px_rgba(14,165,233,0.15)]'
    : 'bg-slate-900/80 backdrop-blur-xl border border-white/10 shadow-[0_8px_30px_rgba(0,0,0,0.5)]';

  return (
    <div className={`absolute top-4 left-4 z-[1000] p-4 rounded-xl flex flex-col gap-3 min-w-[160px] pointer-events-auto ${overlayGlass}`}>
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
              className={`w-4 h-4 rounded border accent-cyan-500 cursor-pointer transition-colors ${
                isLightMode ? 'bg-sky-50 border-sky-200' : 'bg-slate-800 border-slate-600'
              }`}
            />
            <span className={`text-sm font-medium transition-colors group-hover:text-cyan-500 ${layers[layer] ? (isLightMode ? 'text-slate-800' : 'text-white') : subText}`}>
              {layer}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}

export default function MapView({ data, mapRef, isLightMode }) {
  const center = [26.35, 91.6];
  const [layers, setLayers] = useState({
    Boundary: true,
    'Surface Water': true,
    NDVI: true,
    Rainfall: false,
  });

  const toggleLayer = (name) => {
    setLayers((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const tileUrl = isLightMode
    ? 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'
    : 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';

  const boundaryStyle = {
    color: isLightMode ? '#0284c7' : '#06b6d4',
    weight: 3,
    fillColor: isLightMode ? '#38bdf8' : '#06b6d4',
    fillOpacity: isLightMode ? 0.15 : 0.1,
    className: 'boundary-glow',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.7, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="relative w-full h-[434px] max-h-[434px] overflow-hidden rounded-2xl pointer-events-auto"
      ref={mapRef}
    >
      <MapContainer
        center={center}
        zoom={9}
        data-testid="map"
        style={{ height: '100%', width: '100%', background: isLightMode ? '#f8fafc' : '#0f172a' }}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer url={tileUrl} key={isLightMode ? 'tile-light' : 'tile-dark'} />
        {layers.Boundary && (
          <GeoJSON
            key={isLightMode ? 'boundary-light' : 'boundary-dark'}
            data={kamrupBoundary}
            pathOptions={boundaryStyle}
            onEachFeature={(feature, layer) => layer.bindPopup(buildPopup(feature, isLightMode))}
          />
        )}
        {data && layers['Surface Water'] && <WaterRippleLayer isLightMode={isLightMode} />}
        {data && layers.NDVI && <GrassWindLayer isLightMode={isLightMode} />}
      </MapContainer>

      <LayersBox isLightMode={isLightMode} layers={layers} onToggle={toggleLayer} />
      <Legend isLightMode={isLightMode} />
    </motion.div>
  );
}

function buildPopup(feature, isLightMode) {
  const props = feature.properties;
  const textColor = isLightMode ? '#0f172a' : '#e0f2fe';
  const mutedColor = isLightMode ? '#64748b' : '#bae6fd';
  return `
    <div class="custom-popup">
      <h4 style="font-weight:bold;color:${textColor};margin-bottom:4px;">${props.name || 'Region'}</h4>
      <p style="font-size:12px;color:${mutedColor};">Data available for this sector.</p>
    </div>
  `;
}
