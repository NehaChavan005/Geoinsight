export default function AnimatedHills({ isLightMode }) {
  return (
    <div className="absolute bottom-0 left-0 right-0 h-40 overflow-hidden pointer-events-none z-0">
      <style>{`
        @media (prefers-reduced-motion: no-preference) {
          @keyframes breathe {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.05); }
          }
          @keyframes parallax-rear {
            0% { transform: translateX(0); }
            100% { transform: translateX(3px); }
          }
          @keyframes parallax-mid {
            0% { transform: translateX(0); }
            100% { transform: translateX(-5px); }
          }
          @keyframes parallax-front {
            0% { transform: translateX(0); }
            100% { transform: translateX(8px); }
          }
          @keyframes glass-sweep {
            0% { transform: translateX(-100%) skewX(-15deg); }
            100% { transform: translateX(200%) skewX(-15deg); }
          }
          .hill-glow { animation: breathe 8s ease-in-out infinite; }
          .hill-rear { animation: parallax-rear 12s ease-in-out infinite alternate; }
          .hill-mid  { animation: parallax-mid  16s ease-in-out infinite alternate; }
          .hill-front { animation: parallax-front 20s ease-in-out infinite alternate; }
          .glass-sweep-anim { animation: glass-sweep 10s ease-in-out infinite; }
        }
      `}</style>

      {/* Atmospheric glow behind mountains */}
      <div className="absolute bottom-0 left-0 right-0 h-28 bg-cyan-500/10 blur-2xl hill-glow" />

      {/* SVG mountain layers */}
      <svg
        className="absolute bottom-0 left-0 w-full h-full"
        viewBox="0 0 400 120"
        preserveAspectRatio="none"
        fill="none"
      >
        <defs>
          <linearGradient id="rear-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={isLightMode ? 'rgba(14,165,233,0.10)' : 'rgba(56,189,248,0.08)'} />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
          <linearGradient id="mid-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={isLightMode ? 'rgba(14,165,233,0.18)' : 'rgba(56,189,248,0.14)'} />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
          <linearGradient id="front-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={isLightMode ? 'rgba(14,165,233,0.30)' : 'rgba(56,189,248,0.22)'} />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
        </defs>

        {/* Rear mountains */}
        <g className="hill-rear">
          <path
            d="M0 120 L30 65 L65 85 L100 42 L140 78 L175 50 L210 72 L250 35 L290 68 L330 55 L370 80 L400 60 L400 120 Z"
            fill="url(#rear-grad)"
          />
        </g>

        {/* Middle mountains */}
        <g className="hill-mid">
          <path
            d="M0 120 L45 72 L80 90 L120 55 L160 82 L200 48 L240 75 L280 58 L320 85 L360 62 L400 78 L400 120 Z"
            fill="url(#mid-grad)"
          />
        </g>

        {/* Front mountains */}
        <g className="hill-front">
          <path
            d="M0 120 L50 80 L90 95 L130 68 L170 88 L210 60 L250 82 L290 70 L330 90 L370 72 L400 85 L400 120 Z"
            fill="url(#front-grad)"
          />
        </g>
      </svg>

      {/* Glass reflection sweep overlay on front mountains */}
      <div className="absolute bottom-0 left-0 right-0 h-20 overflow-hidden pointer-events-none">
        <div
          className="glass-sweep-anim absolute bottom-0 left-0 w-1/3 h-full"
          style={{
            background: 'linear-gradient(90deg, transparent, rgba(186,230,253,0.10), transparent)',
          }}
        />
      </div>

      {/* Top fade gradient to blend into sidebar */}
      <div className={`absolute top-0 left-0 right-0 h-16 z-10 bg-gradient-to-b ${isLightMode ? 'from-white/95' : 'from-slate-900/95'} to-transparent`} />
    </div>
  );
}
