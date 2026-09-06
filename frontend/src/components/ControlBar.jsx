import { motion } from 'framer-motion';
import { MapPin, Zap } from 'lucide-react';
import MonthPicker from './MonthPicker';

export default function ControlBar({
  district,
  setDistrict,
  month,
  setMonth,
  onGenerate,
  isLoading,
  isLightMode,
}) {
  const glassPanel = isLightMode
    ? 'bg-gradient-to-br from-white/90 to-sky-50/70 backdrop-blur-xl border border-sky-100 rounded-2xl shadow-[0_8px_30px_rgba(14,165,233,0.05)]'
    : 'bg-slate-900/70 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.5),_inset_0_1px_0_rgba(255,255,255,0.1)]';

  const secondaryText = isLightMode ? 'text-slate-500' : 'text-sky-200/60';
  const primaryText = isLightMode ? 'text-slate-800' : 'text-white';
  const divider = isLightMode ? 'bg-slate-200' : 'bg-white/10';

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
      className={`relative z-[99999] overflow-visible rounded-2xl p-3.5 flex flex-col sm:flex-row items-stretch sm:items-center gap-3 ${glassPanel}`}
    >
      <div className="flex items-center gap-2.5 flex-1 min-w-[160px]">
        <MapPin size={18} className="text-cyan-600 dark:text-cyan-300 shrink-0" />
        <div className="flex-1">
          <label className={`block text-[10px] uppercase tracking-widest mb-0.5 ${secondaryText}`}>Select District</label>
          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className={`w-full bg-transparent text-sm font-medium outline-none cursor-pointer appearance-none ${primaryText} [color-scheme:dark]`}
          >
            <option value="Kamrup" className="bg-slate-950 text-white">Kamrup, Assam</option>
            <option value="Kamrup Metro" className="bg-slate-950 text-white">Kamrup Metro</option>
          </select>
        </div>
      </div>

      <div className={`hidden sm:block w-px self-stretch ${divider}`} />

      <MonthPicker isLightMode={isLightMode} value={month} onChange={setMonth} />

      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={() => onGenerate()}
        disabled={isLoading}
        className={`relative flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
          isLightMode
            ? 'bg-cyan-500 hover:bg-cyan-600 text-white shadow-[0_4px_15px_rgba(6,182,212,0.3)]'
            : 'glass-button text-white shadow-[0_0_15px_rgba(6,182,212,0.4)]'
        }`}
      >
        <Zap size={16} className={isLoading ? 'animate-pulse' : ''} />
        {isLoading ? 'Generating…' : 'Generate Report'}
        {isLoading && (
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        )}
      </motion.button>
    </motion.div>
  );
}
