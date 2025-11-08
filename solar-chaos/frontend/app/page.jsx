"use client";
import { motion } from "framer-motion";
import SpaceBackground from "../components/SpaceBackground";

export default function Home() {
  return (
    <div className="relative min-h-screen font-sans text-gray-200">
      <SpaceBackground />
      <main className="relative z-10 flex flex-col items-center justify-center min-h-screen">
        <motion.h1
          initial={{ opacity: 0, y: -40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="text-5xl md:text-6xl font-extrabold tracking-wide text-center text-white drop-shadow-lg"
        >
          🚀 SolarGuard Dashboard
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 1 }}
          className="mt-3 text-lg text-gray-400 text-center"
        >
          Satellite Tracker & Risk Forecaster
        </motion.p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mt-16 w-full max-w-6xl">
          <motion.button
            whileHover={{ scale: 1.05 }}
            className="solar-card"
            onClick={() => (window.location.href = "/satellite")}
          >
            🛰️ Satellite Visualization
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            className="solar-card"
            onClick={() => (window.location.href = "/debris")}
          >
            ☄️ Debris Visualization
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            className="solar-card"
            onClick={() => (window.location.href = "/solar-storm")}
          >
            🌞 Solar Storms
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            className="solar-card"
            onClick={() => (window.location.href = "/solar-wind")}
          >
            💨 Solar Wind
          </motion.button>
        </div>

        <style jsx>{`
          .solar-card {
            padding: 3rem;
            border-radius: 30px;
            background: #f97316;
            border: 2px solid #fb923c;
            box-shadow: 0 25px 60px rgba(249, 115, 22, 0.6);
            backdrop-filter: blur(12px);
            transition: all 0.3s ease;
            font-size: 2rem;
            font-weight: 800;
            color: white;
            text-align: center;
            cursor: pointer;
            width: 100%;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .solar-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 35px 90px rgba(249, 115, 22, 0.8);
            background: #ea580c;
            border-color: #fdba74;
          }
        `}</style>
      </main>
    </div>
  );
}
 