import { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import TopNav from './TopNav';
import ControlBar from './ControlBar';
import StatsRow from './StatsRow';
import MapView from './MapView';
import BottomSection from './BottomSection';
import IntelligencePanel from './IntelligencePanel';
import ParticleFlow from './ParticleFlow';
import GlassCard from './GlassCard';
import { fetchEnvironmentData, fetchInsight, getDistrictId } from '../services/apiClient';

export default function DashboardUI({ isLightMode, toggleTheme }) {
  const [activeView, setActiveView] = useState('dashboard'); // 'dashboard' | 'map'
  const isMapView = activeView === 'map';
  const [district, setDistrict] = useState('Kamrup');
  const [month, setMonth] = useState('2026-06');
  const [data, setData] = useState(null);
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [particles, setParticles] = useState(false);
  const mapRef = useRef(null);

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);
    setParticles(true);
    setTimeout(() => setParticles(false), 2200);
    try {
      const districtId = await getDistrictId(district);
      const [env, ai] = await Promise.all([
        fetchEnvironmentData(districtId, month),
        fetchInsight(districtId, month),
      ]);
      setData(env);
      setInsight(ai);
    } catch (err) {
      console.error('GeoInsight API request failed:', err);
      setError(err && err.message ? err.message : 'Request failed');
    } finally {
      setIsLoading(false);
    }
  };

  const errorBanner = error ? (
    <div
      className={`rounded-xl px-4 py-3 text-sm flex items-center justify-between gap-3 ${
        isLightMode
          ? 'bg-rose-50 border border-rose-300 text-rose-700'
          : 'bg-rose-500/15 border border-rose-400/40 text-rose-200'
      }`}
      role="alert"
    >
      <span className="truncate">API error: {error}</span>
      <button
        onClick={handleGenerate}
        className="shrink-0 px-3 py-1 text-xs font-bold rounded-lg bg-rose-500 text-white hover:bg-rose-600 cursor-pointer transition-colors"
      >
        Retry
      </button>
    </div>
  ) : null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, delay: 0.2 }}
      className="relative z-10 flex items-start min-h-screen gap-6 p-4 md:p-6 pointer-events-auto"
    >
      <ParticleFlow active={particles} originRef={mapRef} />

      {/* Left sidebar */}
      <Sidebar
        isLightMode={isLightMode}
        activeView={activeView}
        onNavigate={setActiveView}
      />

      {/* Center content */}
      <div className="flex-1 min-w-0 flex flex-col gap-6">
        <TopNav theme={isLightMode ? 'light' : 'dark'} onToggleTheme={toggleTheme} isLightMode={isLightMode} />

        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
          {/* Left: control, stats, map, bottom */}
          <div className={`flex flex-col gap-6 min-w-0 ${isMapView ? 'xl:col-span-5' : 'xl:col-span-3'}`}>
            {errorBanner}

            <ControlBar
              district={district}
              setDistrict={setDistrict}
              month={month}
              setMonth={setMonth}
              onGenerate={handleGenerate}
              isLoading={isLoading}
              isLightMode={isLightMode}
            />

            {!isMapView && data && (
              <AnimatePresence mode="wait">
                <motion.div
                  key={`stats-${district}-${month}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <StatsRow data={data} isLightMode={isLightMode} />
                </motion.div>
              </AnimatePresence>
            )}

            {/* Map card — expands to fill the screen in map view */}
            <GlassCard
              className={
                isMapView
                  ? 'p-2 w-full h-[calc(100vh-14rem)] max-h-[calc(100vh-14rem)] overflow-hidden transition-all duration-500'
                  : 'p-2 w-full h-[450px] max-h-[450px] overflow-hidden transition-all duration-500'
              }
              delay={0.35}
              animateBorder
              isLightMode={isLightMode}
            >
              <MapView data={data} district={district} month={month} mapRef={mapRef} isLightMode={isLightMode} fill={isMapView} />
            </GlassCard>

            {!isMapView && data && (
              <AnimatePresence mode="wait">
                <motion.div
                  key={`bottom-${district}-${month}`}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 30 }}
                >
                  <BottomSection data={data} loading={isLoading} isLightMode={isLightMode} />
                </motion.div>
              </AnimatePresence>
            )}
          </div>

          {/* Right: intelligence panel (dashboard view only) */}
          {!isMapView && (
            <div className="xl:col-span-2 min-w-0">
              <IntelligencePanel data={data} insight={insight} loading={isLoading} isLightMode={isLightMode} />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}