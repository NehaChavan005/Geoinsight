import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin } from 'lucide-react';

const DISTRICTS = [
  'Bajali',
  'Baksa',
  'Barpeta',
  'Biswanath',
  'Bongaigaon',
  'Cachar',
  'Charaideo',
  'Chirang',
  'Darrang',
  'Dhemaji',
  'Dhubri',
  'Dibrugarh',
  'Dima Hasao',
  'Goalpara',
  'Golaghat',
  'Hailakandi',
  'Hojai',
  'Jorhat',
  'Kamrup',
  'Kamrup Metropolitan',
  'Karbi Anglong',
  'Karbi Anglong West',
  'Kokrajhar',
  'Lakhimpur',
  'Majuli',
  'Morigaon',
  'Nagaon',
  'Nalbari',
  'Sivasagar',
  'Sonitpur',
  'South Salmara-Mankachar',
  'Tinsukia',
  'Tamulpur',
  'Udalguri',
  'West Karbi Anglong',
];

export default function DistrictPicker({ isLightMode, value = 'Kamrup', onChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState(value);
  const dropdownRef = useRef(null);

  useEffect(() => {
    setSelectedDistrict(value);
  }, [value]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (district) => {
    setSelectedDistrict(district);
    setIsOpen(false);
    onChange?.(district);
  };

  const textPrimary = isLightMode ? 'text-slate-800' : 'text-white';
  const textSecondary = isLightMode ? 'text-slate-500' : 'text-slate-400';
  const glassPanel = isLightMode
    ? 'bg-white/95 backdrop-blur-2xl border border-sky-100 shadow-[0_8px_30px_rgba(14,165,233,0.15)]'
    : 'bg-slate-900/95 backdrop-blur-2xl border border-white/10 shadow-[0_15px_50px_rgba(0,0,0,0.8)]';

  const hoverItem = isLightMode
    ? 'hover:bg-sky-50 text-slate-700'
    : 'hover:bg-white/10 text-slate-300';

  const activeItem = isLightMode
    ? 'bg-cyan-500 text-white shadow-md'
    : 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-300';

  const iconBg = isLightMode
    ? 'bg-sky-50 text-cyan-500 group-hover:bg-sky-100'
    : 'bg-white/5 text-cyan-400 group-hover:bg-white/10';

  return (
    <div className="relative z-[99999] flex-1 min-w-[160px]" ref={dropdownRef}>
      {/* Custom Scrollbar Styling */}
      <style>{`
        .premium-scrollbar::-webkit-scrollbar { width: 6px; }
        .premium-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .premium-scrollbar::-webkit-scrollbar-thumb { background-color: ${isLightMode ? '#cbd5e1' : '#334155'}; border-radius: 10px; }
        .premium-scrollbar::-webkit-scrollbar-thumb:hover { background-color: ${isLightMode ? '#94a3b8' : '#475569'}; }
      `}</style>

      {/* Trigger */}
      <button
        type="button"
        onClick={() => setIsOpen((o) => !o)}
        className="flex items-center gap-2.5 w-full text-left group"
      >
        <div className={`p-2 rounded-lg transition-colors ${iconBg}`}>
          <MapPin size={18} className="shrink-0" />
        </div>
        <div className="flex-1">
          <p className={`block text-[10px] uppercase tracking-widest mb-0.5 ${textSecondary}`}>
            Select District
          </p>
          <p className={`font-bold leading-none ${textPrimary}`}>
            {selectedDistrict}
            <span className="font-normal text-sm opacity-80">, Assam</span>
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
            className={`absolute top-full left-0 mt-3 w-72 max-h-80 overflow-y-auto premium-scrollbar rounded-2xl p-2 z-[99999] ${glassPanel}`}
          >
            <div className="flex flex-col gap-1">
              {DISTRICTS.map((district) => {
                const isActive = selectedDistrict === district;
                return (
                  <button
                    type="button"
                    key={district}
                    onClick={() => handleSelect(district)}
                    className={`text-left px-4 py-2.5 text-sm font-medium rounded-xl transition-all ${
                      isActive ? activeItem : hoverItem
                    }`}
                  >
                    {district}
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