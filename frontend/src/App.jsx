import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { AnimatePresence } from 'framer-motion';
import FreshEarthBackground from './components/FreshEarthBackground';
import IntroScreen from './components/IntroScreen';
import DashboardUI from './components/DashboardUI';

export default function App() {
  const [appState, setAppState] = useState('intro');
  const [isLightMode, setIsLightMode] = useState(false);

  const handleStartSequence = () => {
    setAppState('zooming');

    setTimeout(() => {
      setAppState('dashboard');
    }, 1500);
  };

  const toggleTheme = () => setIsLightMode(!isLightMode);

  const bgTheme = isLightMode
    ? 'bg-gradient-to-br from-sky-50 via-slate-100 to-sky-100'
    : 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-900/60 via-slate-900 to-[#080f1e]';

  return (
    <div
      className={`relative min-h-screen w-full transition-colors duration-700 font-sans ${bgTheme} ${
        isLightMode ? 'text-slate-800' : 'text-slate-100'
      }`}
    >
      {/* 3D Background Layer (Fixed to viewport, behind everything) */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
          <FreshEarthBackground appState={appState} isLightMode={isLightMode} />
        </Canvas>
      </div>

      {/* HTML UI Layer (scrolls naturally with the document) */}
      <div className="relative z-10 pointer-events-none">
        <AnimatePresence mode="wait">
          {appState === 'intro' && (
            <IntroScreen key="intro" onStart={handleStartSequence} isLightMode={isLightMode} />
          )}

          {appState === 'dashboard' && (
            <DashboardUI key="dashboard" isLightMode={isLightMode} toggleTheme={toggleTheme} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
