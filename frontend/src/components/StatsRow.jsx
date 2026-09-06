import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import LiquidHover from './LiquidHover';
import { Leaf, CloudRain, Droplets, Maximize, TrendingUp, Activity, Check } from 'lucide-react';

const CARDS = [
  { id: 'ndvi', label: 'Average NDVI', key: 'ndvi', icon: Leaf, status: 'Green', badgeCls: 'bg-emerald-400/15 text-emerald-300 border-emerald-400/30', badgeIcon: TrendingUp, iconCls: 'text-emerald-400', decimals: 2 },
  { id: 'rainfall', label: 'Total Rainfall', key: 'rainfall', icon: CloudRain, status: 'Monsoon', badgeCls: 'bg-sky-400/15 text-sky-300 border-sky-400/30', badgeIcon: Activity, iconCls: 'text-sky-400', decimals: 0 },
  { id: 'coverage', label: 'Surface Water Coverage', key: 'coverage', icon: Droplets, status: 'Stable', badgeCls: 'bg-cyan-400/15 text-cyan-300 border-cyan-400/30', badgeIcon: Check, iconCls: 'text-cyan-400', decimals: 1 },
  { id: 'area', label: 'Surface Water Area', key: 'area', icon: Maximize, status: 'Sector A', badgeCls: 'bg-teal-400/15 text-teal-300 border-teal-400/30', badgeIcon: Maximize, iconCls: 'text-teal-400', decimals: 1 },
];

function CountUp({ value, decimals = 0, duration = 1500 }) {
  const [display, setDisplay] = useState('0');
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    if (value === '--' || value == null || started.current) return;
    started.current = true;
    const num = parseFloat(value);
    if (isNaN(num)) { setDisplay(String(value)); return; }

    const start = performance.now();
    const step = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay((num * eased).toFixed(decimals));
      if (progress < 1) ref.current = requestAnimationFrame(step);
    };
    ref.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(ref.current);
  }, [value, decimals, duration]);

  return <span>{display}</span>;
}

export default function StatsRow({ data, isLightMode }) {
  const glassPanel = isLightMode
    ? 'rounded-2xl p-4 glow-pulse bg-gradient-to-br from-white/90 to-sky-50/70 backdrop-blur-xl border border-sky-100 shadow-[0_8px_30px_rgba(14,165,233,0.05)] transition-all duration-300 hover:bg-white hover:shadow-md hover:border-sky-200'
    : 'rounded-2xl p-4 glow-pulse bg-slate-900/70 backdrop-blur-xl border border-white/10 shadow-[0_8px_30px_rgba(0,0,0,0.5),_inset_0_1px_0_rgba(255,255,255,0.1)] transition-all duration-300 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.2),_inset_0_1px_0_rgba(255,255,255,0.1)]';

  const iconBox = isLightMode
    ? 'p-2.5 rounded-xl bg-white border border-sky-100 shadow-sm'
    : 'p-2.5 rounded-xl bg-slate-800/50 border border-white/10';

  const secondaryText = isLightMode ? 'text-slate-500' : 'text-sky-200/80';

  return (
    <div className="grid grid-cols-2 xl:grid-cols-4 gap-3.5">
      {CARDS.map((card, i) => {
        const Icon = card.icon;
        const Badge = card.badgeIcon;
        const value =
          card.key === 'ndvi' ? data?.vegetation?.average_ndvi ?? '--'
          : card.key === 'rainfall' ? data?.rainfall?.value_mm ?? '--'
          : card.key === 'coverage' ? data?.surface_water?.coverage_percent ?? '--'
          : data?.surface_water?.area_km2 ?? '--';
        const unit = card.key === 'ndvi' ? '' : card.key === 'rainfall' ? 'mm' : card.key === 'coverage' ? '%' : 'km²';

        return (
          <motion.div
            key={card.id}
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: 0.3 + i * 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          >
            <LiquidHover
              className={glassPanel}
              color={isLightMode ? 'rgba(14,165,233,0.10)' : 'rgba(56,189,248,0.15)'}
              secondary={isLightMode ? 'rgba(16,185,129,0.06)' : 'rgba(34,197,94,0.1)'}
            >
              <div className="flex items-start justify-between">
                <div className={`${iconBox} ${card.iconCls}`}>
                  <Icon size={20} />
                </div>
                <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${card.badgeCls}`}>
                  <Badge size={10} /> {card.status}
                </span>
              </div>
              <p className={`text-xs mt-3 ${secondaryText}`}>{card.label}</p>
              <p className={`text-2xl font-bold mt-0.5 ${isLightMode ? 'text-slate-800' : 'text-white'}`}>
                {value !== '--' ? <CountUp value={value} decimals={card.decimals} /> : '--'}{' '}
                <span className={`text-sm font-normal ${isLightMode ? 'text-slate-400' : 'text-sky-200/60'}`}>{unit}</span>
              </p>
            </LiquidHover>
          </motion.div>
        );
      })}
    </div>
  );
}
