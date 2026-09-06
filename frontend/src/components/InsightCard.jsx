import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

export default function InsightCard({ text }) {
  if (!text) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="relative p-[1px] rounded-2xl bg-gradient-to-br from-cyan-400/70 to-emerald-400/50 overflow-hidden"
    >
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-xl" />
      <div className="relative glass-panel p-5 rounded-[15px] h-full">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3 uppercase tracking-wider">
          <Sparkles size={16} /> AI Environmental Insight
        </h3>
        <p className="text-white/90 leading-relaxed text-sm">{text}</p>
      </div>
    </motion.div>
  );
}