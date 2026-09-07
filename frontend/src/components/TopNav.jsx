import { motion } from 'framer-motion';
import { Satellite, ChevronDown } from 'lucide-react';

export default function TopNav({ theme, onToggleTheme, isLightMode }) {
  const glassPanel = isLightMode
    ? 'bg-gradient-to-br from-white/95 to-sky-50/80 backdrop-blur-xl border border-sky-100 rounded-2xl shadow-[0_4px_20px_rgba(14,165,233,0.08)]'
    : 'bg-slate-900/70 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_0_25px_rgba(6,182,212,0.15),_inset_0_1px_0_rgba(255,255,255,0.1)]';

  const iconBg = isLightMode
    ? 'bg-white border border-sky-100 shadow-sm'
    : 'bg-slate-800/50 border border-white/10';

  const primaryText = isLightMode ? 'text-slate-800' : 'text-white';
  const secondaryText = isLightMode ? 'text-slate-500' : 'text-sky-200/80';

  return (
    <motion.header
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`relative z-[100] flex items-center justify-between gap-4 rounded-2xl px-5 py-3 ${glassPanel}`}
    >
      <div className="flex items-center gap-3 min-w-0">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-cyan-600 dark:text-cyan-400 shrink-0 ${iconBg}`}>
          <Satellite size={22} />
        </div>
        <div className="min-w-0">
          <div className="flex items-baseline gap-2">
            <h1 className={`text-lg font-bold tracking-tight truncate ${primaryText}`}>GeoInsight</h1>
            <span className={`text-[10px] uppercase tracking-widest hidden md:inline ${secondaryText}`}>v1.0</span>
          </div>
          <p className={`text-xs truncate ${secondaryText}`}>Geospatial Intelligence Platform · Kamrup District</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className={`hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-cyan-600 dark:text-cyan-400 ${iconBg}`}>
          <span className="relative flex h-2 w-2">
            <span className="live-dot absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-70" />
            <span className="live-dot relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
          </span>
          Live Data
        </div>

        <motion.button
          whileTap={{ scale: 0.9 }}
          onClick={onToggleTheme}
          className={`w-10 h-10 rounded-full flex items-center justify-center transition-all hover:scale-105 active:scale-95 ${iconBg}`}
          aria-label="Toggle theme"
          title="Toggle Theme"
        >
          {theme === 'light' ? (
            <svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-slate-300 hover:text-cyan-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          )}
        </motion.button>

        <button className={`flex items-center gap-2 rounded-xl p-1.5 pr-2 transition-colors ${iconBg}`}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400/30 to-emerald-400/30 flex items-center justify-center font-bold text-sm">
            A
          </div>
          <div className="hidden md:block text-left leading-tight">
            <p className={`text-xs font-semibold ${primaryText}`}>Analyst MR</p>
            <p className={`text-[10px] ${secondaryText}`}>Field Ops</p>
          </div>
          <ChevronDown size={15} className={secondaryText} />
        </button>
      </div>
    </motion.header>
  );
}
