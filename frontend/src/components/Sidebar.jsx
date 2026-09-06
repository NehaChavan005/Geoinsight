import { motion } from 'framer-motion';
import { LayoutDashboard, Map, FileJson, Info } from 'lucide-react';
import AnimatedHills from './AnimatedHills';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, active: true },
  { label: 'Map', icon: Map, active: false },
  { label: 'API Docs', icon: FileJson, active: false },
  { label: 'About', icon: Info, active: false },
];

export default function Sidebar({ isLightMode }) {
  const glassPanel = isLightMode
    ? 'bg-gradient-to-br from-white/90 to-sky-50/70 backdrop-blur-xl border border-sky-100 rounded-2xl shadow-[0_8px_30px_rgba(14,165,233,0.05)]'
    : 'bg-slate-900/70 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.5),_inset_0_1px_0_rgba(255,255,255,0.1)]';

  const primaryText = isLightMode ? 'text-white' : 'text-white';
  const secondaryText = isLightMode ? 'text-slate-600' : 'text-sky-200/80';
  const borderCls = isLightMode ? 'border-sky-200' : 'border-white/10';

  return (
    <motion.aside
      initial={{ x: -80, opacity: 0, rotateY: -12 }}
      animate={{ x: 0, opacity: 1, rotateY: 0 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className={`hidden lg:flex flex-col justify-between w-56 shrink-0 rounded-2xl overflow-hidden sticky top-6 h-[calc(100vh-3rem)] ${glassPanel}`}
      style={{ transformPerspective: 1000 }}
    >
      <div className="flex items-center gap-2 px-5 pt-5 pb-4">
        <div className="w-9 h-9 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center shadow-[0_0_10px_rgba(6,182,212,0.3)]">
          <span className={`font-black ${isLightMode ? 'text-cyan-700' : 'text-cyan-300'}`}>G</span>
        </div>
        <span className={`font-bold tracking-wide ${primaryText}`}>GeoInsight</span>
      </div>

      <div className={`border-t mb-3 mx-4 ${isLightMode ? 'border-sky-100' : 'border-white/10'}`} />

      <nav className="flex flex-col gap-1.5 px-3 flex-1">
        {NAV_ITEMS.map((item, i) => {
          const Icon = item.icon;
          return (
            <motion.button
              key={item.label}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 + i * 0.08 }}
              className={`nav-item group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${secondaryText} hover:text-white transition-colors relative`}
            >
              {item.active && (
                <motion.span
                  layoutId="nav-active"
                  className={`absolute inset-0 rounded-xl ${isLightMode ? 'bg-cyan-500/10 border border-cyan-500/20' : 'bg-cyan-500/10 border border-cyan-500/20 shadow-[inset_0_0_10px_rgba(6,182,212,0.1)]'}`}
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
              <Icon
                size={18}
                className={`relative z-10 transition-transform group-hover:scale-110 ${isLightMode ? 'text-cyan-600 group-hover:text-cyan-700' : 'text-cyan-300 group-hover:text-cyan-200'}`}
              />
              <span className={`relative z-10 ${item.active ? (isLightMode ? 'text-cyan-700' : 'text-cyan-300') : ''}`}>{item.label}</span>
            </motion.button>
          );
        })}
      </nav>

      <div className="relative">
        <div
          className={`absolute inset-0 bg-gradient-to-t to-transparent ${
            isLightMode ? 'from-cyan-100/40' : 'from-cyan-900/20 opacity-50'
          }`}
        />
        <AnimatedHills isLightMode={isLightMode} />
      </div>
    </motion.aside>
  );
}
