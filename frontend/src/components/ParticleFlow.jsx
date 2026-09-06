/**
 * ParticleFlow - A full-dashboard Canvas overlay that spawns glowing
 * data particles from the central map and flows them along bezier curves
 * into target injection points (API Response box + AI Insight card).
 *
 * Targets are located by data-target="/.../" CSS selectors resolved at
 * animation time so they follow the actual DOM layout.
 */
import { useEffect, useRef } from 'react';

const TARGET_GROUPS = [
  { selector: '[data-target="api"]', color: '56,189,248' },
  { selector: '[data-target="insight"]', color: '34,197,94' },
];

export default function ParticleFlow({ active, originRef }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let raf = 0;
    let particles = [];
    let last = performance.now();
    const dpr = window.devicePixelRatio || 1;

    const sizeCanvas = () => {
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    sizeCanvas();
    window.addEventListener('resize', sizeCanvas);

    const getTarget = (selector) => {
      const el = document.querySelector(selector);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
    };

    const getOrigin = () => {
      if (originRef && originRef.current) {
        const r = originRef.current.getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
      }
      return { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    };

    const spawn = () => {
      const origin = getOrigin();
      particles = [];
      const total = 70;
      for (let i = 0; i < total; i++) {
        const group = TARGET_GROUPS[i % TARGET_GROUPS.length];
        const target = getTarget(group.selector);
        if (!target) continue;
        // control points form a curved path from map to target
        const mx = (origin.x + target.x) / 2 + (Math.random() - 0.5) * 220;
        const my = Math.min(origin.y, target.y) - 120 - Math.random() * 140;
        particles.push({
          x: origin.x + (Math.random() - 0.5) * 60,
          y: origin.y + (Math.random() - 0.5) * 60,
          from: origin,
          ctrl: { x: mx, y: my },
          to: target,
          t: Math.random() * 0.4,
          speed: 0.008 + Math.random() * 0.012,
          color: group.color,
          size: 1.5 + Math.random() * 2.5,
          life: 1,
        });
      }
    };

    const step = () => {
      const now = performance.now();
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

      particles.forEach((p) => {
        p.t += p.speed * (1 + dt);
        if (p.t >= 1) {
          p.life -= dt * 2.2;
        }
        const inv = 1 - p.t;
        // Quadratic bezier point
        const ux =
          inv * inv * p.from.x +
          2 * inv * p.t * p.ctrl.x +
          p.t * p.t * p.to.x;
        const uy =
          inv * inv * p.from.y +
          2 * inv * p.t * p.ctrl.y +
          p.t * p.t * p.to.y;

        const glow = 0.5 + 0.5 * Math.sin(now / 140 + p.x);
        ctx.beginPath();
        ctx.arc(ux, uy, p.size * p.life, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.color},${Math.max(0, p.life) * (0.5 + glow * 0.5)})`;
        ctx.shadowColor = `rgba(${p.color},0.9)`;
        ctx.shadowBlur = 12 * p.life;
        ctx.fill();
        ctx.shadowBlur = 0;

        // trailing streak
        ctx.beginPath();
        ctx.moveTo(ux, uy);
        ctx.lineTo(ux - p.speed * 900 * p.t * 0.4, uy - p.speed * 700 * p.t * 0.4);
        ctx.strokeStyle = `rgba(${p.color},${Math.max(0, p.life) * 0.35})`;
        ctx.lineWidth = p.size * 0.6;
        ctx.stroke();
      });

      particles = particles.filter((p) => p.life > 0 && p.t < 1.6);
      if (particles.length > 0) {
        raf = requestAnimationFrame(step);
      } else {
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      }
    };

    if (active) {
      spawn();
      raf = requestAnimationFrame(step);
    } else {
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', sizeCanvas);
    };
  }, [active, originRef]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-[9999]"
    />
  );
}
