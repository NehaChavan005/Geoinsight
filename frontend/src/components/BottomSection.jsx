import { motion } from 'framer-motion';
import { FileJson, Copy, Download, RefreshCw, Zap, Wifi, Rss } from 'lucide-react';
import { useState } from 'react';
import GlassCard from './GlassCard';

const QUICK_ACTIONS = [
  { label: 'Export KML', icon: Download },
  { label: 'Refresh Layers', icon: RefreshCw },
  { label: 'Auto-Detect Mode', icon: Zap },
  { label: 'Stream Telemetry', icon: Rss },
  { label: 'Sync WMS', icon: Wifi },
];

export default function BottomSection({ data, loading, isLightMode }) {
  const [copied, setCopied] = useState(false);

  const json = data
    ? JSON.stringify(data, null, 2)
    : '{\n  "status": "awaiting_generation"\n}';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* noop */ }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <GlassCard className="lg:col-span-2 p-0 overflow-hidden" delay={0.7} isLightMode={isLightMode}>
        <div className={`flex items-center justify-between px-4 py-2.5 border-b ${isLightMode ? 'border-sky-100 bg-gradient-to-r from-white/70 to-sky-50/60' : 'border-white/10 bg-slate-900/40'}`}>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-400" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            <span className={`ml-2 flex items-center gap-1.5 text-xs font-mono ${isLightMode ? 'text-slate-500' : 'text-sky-200/80'}`}>
              <FileJson size={14} /> API Response (JSON)
            </span>
          </div>
          <button
            onClick={handleCopy}
            className="glass-button flex items-center gap-1 text-[11px] px-2 py-1 rounded-md text-cyan-600 dark:text-sky-200/80"
          >
            {copied ? <span>Copied</span> : <><Copy size={12} /> Copy</>}
          </button>
        </div>
        <div className="relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm z-10">
              <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            </div>
          )}
          <pre
            data-target="api"
            className={`p-4 text-xs leading-relaxed font-mono overflow-x-auto max-h-56 min-h-[120px] ${isLightMode ? 'text-slate-700' : 'text-sky-100/80'}`}
          >
            <code>{json}</code>
          </pre>
        </div>
      </GlassCard>

      <GlassCard className="p-4" delay={0.8} isLightMode={isLightMode}>
        <h3 className={`text-sm font-semibold mb-3 flex items-center gap-2 ${isLightMode ? 'text-slate-800' : 'text-white'}`}>
          <Zap size={16} className="text-cyan-500" /> Quick Actions
        </h3>
        <div className="flex flex-col gap-2">
          {QUICK_ACTIONS.map((a) => {
            const Icon = a.icon;
            return (
              <motion.button
                key={a.label}
                whileTap={{ scale: 0.97 }}
                className={`glass-button flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm ${isLightMode ? 'text-slate-700' : 'text-sky-100/90'} text-left`}
              >
                <Icon size={15} className="text-cyan-500" />
                {a.label}
              </motion.button>
            );
          })}
        </div>
      </GlassCard>
    </div>
  );
}