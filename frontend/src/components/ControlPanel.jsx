import { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin, Calendar, Activity } from 'lucide-react';

export default function ControlPanel({ onGenerate, isLoading }) {
  const [district, setDistrict] = useState('Kamrup');
  const [month, setMonth] = useState('2026-06');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel rounded-2xl p-6"
    >
      <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 text-white">
        <Activity size={20} className="text-white" /> Analysis Parameters
      </h2>

      <div className="space-y-5">
        <div>
          <label className="text-sm text-white/70 font-medium mb-1.5 flex items-center gap-2">
            <MapPin size={16} /> Target District
          </label>
          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="w-full bg-[#0f172a]/60 border border-white/10 rounded-lg p-3 text-slate-100 outline-none focus:border-cyan-400 backdrop-blur-xl disabled:opacity-70 [color-scheme:dark]"
            disabled
          >
            <option value="Kamrup" className="bg-slate-900 text-white">
              Kamrup, Assam
            </option>
          </select>
        </div>

        <div>
          <label className="text-sm text-white/70 font-medium mb-1.5 flex items-center gap-2">
            <Calendar size={16} /> Observation Month
          </label>
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="w-full bg-[#0f172a]/60 border border-white/10 rounded-lg p-3 text-slate-100 outline-none focus:border-cyan-400 backdrop-blur-xl [color-scheme:dark]"
          />
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onGenerate(district, month)}
          disabled={isLoading}
          className="w-full mt-4 glass-button font-bold py-3 px-4 rounded-lg flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-white"
        >
          {isLoading ? 'Processing Satellite Data...' : 'Generate Report'}
        </motion.button>
      </div>
    </motion.div>
  );
}