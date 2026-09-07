import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const FULL_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

export default function MonthPicker({ isLightMode, value = '2026-06', onChange }) {
  const initialYear = parseInt(value.slice(0, 4), 10);
  const initialMonth = parseInt(value.slice(5, 7), 10) - 1;

  const [isOpen, setIsOpen] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(initialMonth);
  const [selectedYear, setSelectedYear] = useState(initialYear);
  const [viewYear, setViewYear] = useState(initialYear);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (!value) return;
    const y = parseInt(value.slice(0, 4), 10);
    const m = parseInt(value.slice(5, 7), 10) - 1;
    if (!Number.isNaN(y) && !Number.isNaN(m)) {
      setSelectedYear(y);
      setSelectedMonth(m);
    }
  }, [value]);

  const handleMonthSelect = (index) => {
    setSelectedMonth(index);
    setSelectedYear(viewYear);
    setIsOpen(false);
    onChange?.(`${viewYear}-${String(index + 1).padStart(2, '0')}`);
  };

  const textPrimary = isLightMode ? 'text-slate-800' : 'text-white';
  const textSecondary = isLightMode ? 'text-slate-500' : 'text-slate-400';
  const glassPanel = isLightMode
    ? 'bg-white/95 backdrop-blur-2xl border border-sky-100 shadow-[0_8px_30px_rgba(14,165,233,0.15)]'
    : 'bg-slate-900/90 backdrop-blur-2xl border border-white/10 shadow-[0_8px_30px_rgba(0,0,0,0.6)]';

  const hoverItem = isLightMode
    ? 'hover:bg-sky-50 text-slate-700'
    : 'hover:bg-white/10 text-slate-300';

  const activeItem = isLightMode
    ? 'bg-cyan-500 text-white shadow-md'
    : 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-300';

  const iconBg = isLightMode
    ? 'bg-sky-50 text-emerald-500 group-hover:bg-sky-100'
    : 'bg-white/5 text-emerald-400 group-hover:bg-white/10';

  return (
    <div className="relative z-[99999] flex-1 min-w-[160px]" ref={dropdownRef}>
      {/* Trigger */}
      <button onClick={() => setIsOpen(!isOpen)} className="flex items-center gap-2.5 w-full text-left group">
        <div className={`p-2 rounded-lg transition-colors ${iconBg}`}>
          <Calendar size={18} className="shrink-0" />
        </div>
        <div className="flex-1">
          <p className={`block text-[10px] uppercase tracking-widest mb-0.5 ${textSecondary}`}>Select Month</p>
          <p className={`text-sm font-medium leading-tight ${textPrimary}`}>
            {FULL_MONTHS[selectedMonth]}, {selectedYear}
          </p>
        </div>
      </button>

      {/* Dropdown Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className={`absolute top-full left-0 mt-3 w-64 rounded-2xl p-4 z-[99999] ${glassPanel}`}
          >
            {/* Year Selector */}
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={() => setViewYear((y) => y - 1)}
                className={`p-1.5 rounded-lg transition-colors ${hoverItem}`}
                aria-label="Previous year"
              >
                <ChevronLeft size={20} />
              </button>
              <span className={`font-bold text-lg ${textPrimary}`}>{viewYear}</span>
              <button
                onClick={() => setViewYear((y) => y + 1)}
                className={`p-1.5 rounded-lg transition-colors ${hoverItem}`}
                aria-label="Next year"
              >
                <ChevronRight size={20} />
              </button>
            </div>

            {/* Months Grid */}
            <div className="grid grid-cols-3 gap-2">
              {MONTHS.map((month, index) => {
                const isActive = selectedMonth === index && selectedYear === viewYear;
                return (
                  <button
                    key={month}
                    onClick={() => handleMonthSelect(index)}
                    className={`py-2 text-sm font-medium rounded-xl transition-all ${
                      isActive ? activeItem : hoverItem
                    }`}
                  >
                    {month}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}