/**
 * LiquidHover - Wraps any element with a soft white radial gradient that
 * follows the cursor inside the card boundaries (frosted glass feel).
 */
import { useRef } from 'react';

export default function LiquidHover({
  children,
  className = '',
  color = 'rgba(56,189,248,0.14)',
  secondary = 'rgba(34,197,94,0.08)',
}) {
  const ref = useRef(null);

  const handleMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    el.style.setProperty('--mx', `${x}px`);
    el.style.setProperty('--my', `${y}px`);
  };

  return (
    <div
      ref={ref}
      onMouseMove={handleMove}
      className={`liquid-hover relative overflow-hidden ${className}`}
      style={{
        backgroundImage: `radial-gradient(600px circle at var(--mx,50%) var(--my,50%), ${color}, transparent 45%), radial-gradient(400px circle at var(--mx,50%) var(--my,50%), ${secondary}, transparent 50%)`,
      }}
    >
      {children}
    </div>
  );
}