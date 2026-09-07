import { motion } from 'framer-motion';

export default function IntroScreen({ onStart, isLightMode }) {
  const textColor = isLightMode ? "text-slate-800" : "text-white";
  const subText = isLightMode ? "text-slate-500" : "text-sky-200";

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.5 } }}
      className="fixed inset-0 z-[9999] h-screen w-screen flex flex-col items-center justify-center pointer-events-auto"
    >
      <div className="flex flex-col items-center justify-center text-center mb-24 w-full px-4">
        
        <motion.p 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className={`${subText} tracking-widest uppercase text-xs md:text-sm mb-4 font-semibold`}
        >
          Geospatial Intelligence
        </motion.p>
        
        <motion.h1 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className={`text-6xl md:text-8xl lg:text-9xl font-bold ${textColor} tracking-tight mb-10 drop-shadow-lg`}
        >
          GeoInsight
        </motion.h1>
        
        <motion.button
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6 }}
          whileHover={{ scale: 1.05, boxShadow: isLightMode ? "0 0 30px rgba(14,165,233,0.3)" : "0 0 30px rgba(56, 189, 248, 0.5)" }}
          whileTap={{ scale: 0.95 }}
          onClick={onStart}
          className={`px-10 py-4 rounded-full font-bold tracking-widest uppercase transition-all ${
            isLightMode 
              ? "bg-white/70 backdrop-blur-md border border-white text-slate-800 shadow-lg hover:bg-white" 
              : "bg-white/20 backdrop-blur-md border border-white/50 text-white shadow-[0_0_15px_rgba(255,255,255,0.2)] hover:bg-white/30"
          }`}
        >
          GET STARTED
        </motion.button>

      </div>
    </motion.div>
  );
}
