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
import { fetchEnvironmentData } from '../services/apiClient';

export default function DashboardUI({ isLightMode, toggleTheme }) {
  const [district, setDistrict] = useState('Kamrup');
  const [month, setMonth] = useState('2026-06');
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [particles, setParticles] = useState(false);
  const mapRef = useRef(null);

  const handleGenerate = async () => {
    setIsLoading(true);
    const result = await fetchEnvironmentData(district, month);
    setData(result);
    setIsLoading(false);
    setParticles(true);
    setTimeout(() => setParticles(false), 2200);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, delay: 0.2 }}
      className="relative z-10 flex items-start min-h-screen gap-6 p-4 md:p-6 pointer-events-auto"
    >
      <ParticleFlow active={particles} originRef={mapRef} />

      {/* Left sidebar */}
      <Sidebar isLightMode={isLightMode} />

      {/* Center content */}
      <div className="flex-1 min-w-0 flex flex-col gap-6">
        <TopNav theme={isLightMode ? 'light' : 'dark'} onToggleTheme={toggleTheme} isLightMode={isLightMode} />

        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
          {/* Left: control, stats, map, bottom */}
          <div className="xl:col-span-3 flex flex-col gap-6 min-w-0">
            <ControlBar
              district={district}
              setDistrict={setDistrict}
              month={month}
              setMonth={setMonth}
              onGenerate={handleGenerate}
              isLoading={isLoading}
              isLightMode={isLightMode}
            />

            <AnimatePresence mode="wait">
              {data && (
                <motion.div
                  key={`stats-${district}-${month}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <StatsRow data={data} isLightMode={isLightMode} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Map card */}
            <GlassCard
              className="p-2 w-full h-[450px] max-h-[450px] overflow-hidden"
              delay={0.35}
              animateBorder
              isLightMode={isLightMode}
            >
              <MapView data={data} mapRef={mapRef} isLightMode={isLightMode} />
            </GlassCard>

            <AnimatePresence mode="wait">
              {data && (
                <motion.div
                  key={`bottom-${district}-${month}`}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 30 }}
                >
                  <BottomSection data={data} loading={isLoading} isLightMode={isLightMode} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right: intelligence panel */}
          <div className="xl:col-span-2 min-w-0">
            <IntelligencePanel data={data} loading={isLoading} isLightMode={isLightMode} />
          </div>
        </div>
      </div>
    </motion.div>
  );
}