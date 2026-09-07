import { motion } from 'framer-motion';
import { Leaf, Droplets, CloudRain, Maximize } from 'lucide-react';

const StatCard = ({ icon: Icon, label, value, unit, delay }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ delay, duration: 0.3 }}
    className="glass-panel rounded-2xl p-4 flex items-start gap-4"
  >
    <div className="p-3 bg-slate-800/50 rounded-lg text-cyan-400 border border-white/10">
      <Icon size={24} />
    </div>
    <div>
      <p className="text-sm text-white/70 font-medium">{label}</p>
      <p className="text-2xl font-bold text-white mt-1 drop-shadow">
        {value} <span className="text-sm font-normal text-white/70">{unit}</span>
      </p>
    </div>
  </motion.div>
);

export default function StatsBoard({ data }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <StatCard
        icon={Leaf} label="Average NDVI"
        value={data.vegetation.average_ndvi} unit="" delay={0.1}
      />
      <StatCard
        icon={CloudRain} label="Rainfall"
        value={data.rainfall.value_mm} unit="mm" delay={0.2}
      />
      <StatCard
        icon={Droplets} label="Water Cover"
        value={data.surface_water.coverage_percent} unit="%" delay={0.3}
      />
      <StatCard
        icon={Maximize} label="Water Area"
        value={data.surface_water.area_km2} unit="km²" delay={0.4}
      />
    </div>
  );
}