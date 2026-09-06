import { motion } from 'framer-motion';

export default function GlassCard({ children, className = '', delay = 0, rotate = false, animateBorder = false, isLightMode = false }) {
  const glassCls = isLightMode
    ? 'bg-gradient-to-br from-white/90 to-sky-50/70 backdrop-blur-xl border border-sky-100 rounded-2xl shadow-[0_8px_30px_rgba(14,165,233,0.05)]'
    : 'bg-slate-900/70 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_30px_rgba(0,0,0,0.5),_inset_0_1px_0_rgba(255,255,255,0.1)]';

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={`glass-card relative rounded-2xl ${glassCls} ${rotate ? 'rotate-1' : ''} ${className}`}
    >
      {animateBorder && (
        <>
          <div
            className="rotating-border rounded-2xl"
            style={{
              background:
                'conic-gradient(from 0deg, transparent, rgba(56,189,248,0.4), transparent, rgba(34,197,94,0.3), transparent)',
              filter: 'blur(1px)',
            }}
          />
          <motion.div
            className={`absolute -inset-px rounded-2xl bg-transparent border ${isLightMode ? 'border-cyan-200' : 'border-slate-600/40'}`}
            animate={{ opacity: [0.3, 0.8, 0.3] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
          />
        </>
      )}
      {children}
    </motion.div>
  );
}
