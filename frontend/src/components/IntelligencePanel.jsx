import { motion } from 'framer-motion';
import { Leaf, Cpu, ChevronRight } from 'lucide-react';
import GlassCard from './GlassCard';

const THUMBNAILS = [
  { label: 'NDVI', bg: 'linear-gradient(135deg,#064e3b,#34d399,#1e293b)' },
  { label: 'Surface Water', bg: 'linear-gradient(135deg,#0c4a6e,#38bdf8,#1e293b)' },
  { label: 'Rainfall', bg: 'linear-gradient(135deg,#1e3a8a,#60a5fa,#1e293b)' },
];

const QUICK_STATS = (data) => [
  { label: 'District', value: data?.district || '—' },
  {
    label: 'District Area',
    value:
      data?.metadata?.district_area_km2 != null
        ? `${Number(data.metadata.district_area_km2).toFixed(2)} km²`
        : '—',
  },
  {
    label: 'Processing',
    value:
      data?.metadata?.processing_time_ms != null
        ? `${data.metadata.processing_time_ms} ms`
        : '—',
  },
  { label: 'Cached', value: data?.metadata?.cached ? 'Yes' : 'No' },
];

export default function IntelligencePanel({ data, insight, loading, isLightMode }) {
  const insightText =
    insight?.insight ||
    'Select a district and month, then Generate Report to receive a natural-language environmental summary powered by Llama 3.2.';

  const primaryText = isLightMode ? 'text-slate-800' : 'text-white';
  const secondaryText = isLightMode ? 'text-slate-500' : 'text-sky-200/80';

  const interactiveCard = isLightMode
    ? 'bg-white/60 border border-sky-100 rounded-xl px-3 py-2.5 transition-all duration-300 hover:bg-white hover:shadow-md hover:border-sky-200'
    : 'bg-slate-800/50 border border-white/5 rounded-xl px-3 py-2.5 transition-all duration-300 hover:bg-slate-800/80 hover:border-cyan-500/40 hover:shadow-[0_0_15px_rgba(6,182,212,0.2)]';

  const iconBox = isLightMode
    ? 'bg-white border border-sky-100 shadow-sm'
    : 'bg-slate-800/50 border border-white/10';

  return (
    <div className="flex flex-col gap-4">
      <GlassCard
        className={`p-0 overflow-hidden ${
          isLightMode
            ? 'bg-gradient-to-br from-white/95 to-emerald-50/80 border-emerald-100 shadow-[0_4px_20px_rgba(16,185,129,0.1)]'
            : 'border-cyan-500/20 shadow-[0_0_25px_rgba(6,182,212,0.15),_inset_0_1px_0_rgba(255,255,255,0.1)]'
        }`}
        delay={0.5}
        animateBorder
        isLightMode={isLightMode}
      >
        <div className="p-5" data-target="insight">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${iconBox}`}>
                <Leaf size={18} className="text-emerald-500" />
              </div>
              <div>
                <p className={`text-sm font-bold ${primaryText}`}>AI Environmental Insight</p>
                <p className={`text-[10px] flex items-center gap-1 ${secondaryText}`}>
                  <Cpu size={10} className="text-cyan-500" /> Powered by Llama 3.2
                </p>
              </div>
            </div>
            {loading ? (
              <span className="flex items-center gap-1 text-[10px] text-cyan-500">
                <span className="w-3 h-3 border border-white/20 border-t-white rounded-full animate-spin" />
                Analyzing
              </span>
            ) : (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/15 text-emerald-600 border border-emerald-400/30">
                Live
              </span>
            )}
          </div>
          <p className={`text-sm leading-relaxed min-h-[72px] ${isLightMode ? 'text-slate-600' : 'text-sky-200/80'}`}>{insightText}</p>
        </div>
      </GlassCard>

      <GlassCard className="p-4" delay={0.65} isLightMode={isLightMode}>
        <h3 className={`text-sm font-semibold mb-3 ${primaryText}`}>Quick Stats</h3>
        <div className="grid grid-cols-2 gap-2.5">
          {QUICK_STATS(data).map((s) => (
            <div key={s.label} className={interactiveCard}>
              <p className={`text-[10px] uppercase tracking-wider ${secondaryText}`}>{s.label}</p>
              <p className={`text-sm font-semibold mt-0.5 ${primaryText}`}>{s.value}</p>
            </div>
          ))}
        </div>
      </GlassCard>

      <GlassCard className="p-4" delay={0.8} isLightMode={isLightMode}>
        <div className="flex items-center justify-between mb-3">
          <h3 className={`text-sm font-semibold ${primaryText}`}>Layers Preview</h3>
          <button className={`flex items-center gap-1 text-[11px] text-cyan-500 hover:text-cyan-400 cursor-pointer pointer-events-auto transition-colors`}>
            View all <ChevronRight size={14} />
          </button>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {THUMBNAILS.map((t) => (
            <div
              key={t.label}
              className={`rounded-lg overflow-hidden transition-transform duration-300 ease-out hover:-translate-y-1 hover:shadow-lg ${isLightMode
                ? 'border border-sky-100 bg-white/60 shadow-md hover:border-sky-200 hover:shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                : 'border border-white/5 bg-slate-800/50 shadow-lg hover:border-cyan-500/40 hover:shadow-[0_0_15px_rgba(6,182,212,0.2)]'}`}
            >
              <div className="h-16 w-full" style={{ background: t.bg, opacity: 0.9 }} />
              <p className={`text-[10px] text-center py-1 ${isLightMode ? 'text-slate-600 bg-white/50' : 'text-sky-200/80 bg-slate-800/50'}`}>{t.label}</p>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
