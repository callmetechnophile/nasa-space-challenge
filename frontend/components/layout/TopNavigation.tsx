"use client";

import React from "react";
import {
  Compass,
  Clock,
  Activity,
  ShieldCheck,
  Info,
  Layers,
} from "lucide-react";
import { useSkyStore } from "@/stores/useSkyStore";

export function TopNavigation() {
  const activeTab = useSkyStore((s) => s.activeTab);
  const setActiveTab = useSkyStore((s) => s.setActiveTab);

  return (
    <header className="h-12 border-b border-cyan-950/70 bg-[#030612]/95 backdrop-blur-md px-3 sm:px-4 flex items-center justify-between z-30 select-none font-mono">
      {/* Title & Mission Branding */}
      <div className="flex items-center space-x-2.5 text-xs">
        <div className="flex items-center space-x-1.5 cursor-pointer" onClick={() => setActiveTab("sky")}>
          <div className="w-6 h-6 rounded bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center font-black text-[11px] text-white shadow-[0_0_10px_rgba(6,182,212,0.3)]">
            SP
          </div>
          <span className="font-bold tracking-wider text-cyan-50 text-sm">
            SPHEREx
          </span>
        </div>

        <span className="text-slate-700 hidden sm:inline">|</span>

        <span className="text-cyan-300 font-medium tracking-wide hidden md:inline">
          3D Sky Explorer
        </span>

        <span className="text-slate-700 hidden lg:inline">|</span>

        <span className="hidden lg:inline-flex items-center space-x-1.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-950/60 text-amber-300 border border-amber-800/50">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
          <span>DEMONSTRATION MODE</span>
        </span>
      </div>

      {/* Central Navigation Tabs */}
      <nav className="flex items-center space-x-1 sm:space-x-1.5">
        <button
          onClick={() => setActiveTab("sky")}
          className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs transition-all ${
            activeTab === "sky"
              ? "bg-cyan-500/20 text-cyan-200 border border-cyan-500/60 shadow-[0_0_10px_rgba(6,182,212,0.25)] font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-[#07132e]/50 border border-transparent"
          }`}
          title="Interactive 3D Celestial Coordinate Sphere"
        >
          <Compass className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">3D Sky</span>
        </button>

        <button
          onClick={() => setActiveTab("temporal")}
          className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs transition-all ${
            activeTab === "temporal"
              ? "bg-cyan-500/20 text-cyan-200 border border-cyan-500/60 shadow-[0_0_10px_rgba(6,182,212,0.25)] font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-[#07132e]/50 border border-transparent"
          }`}
          title="Temporal Observation Comparison (Milestone 4)"
        >
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Temporal</span>
          <span className="text-[9px] bg-cyan-950 text-cyan-300 px-1 py-0.2 rounded border border-cyan-800">
            M4
          </span>
        </button>

        <button
          onClick={() => setActiveTab("spectral")}
          className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs transition-all ${
            activeTab === "spectral"
              ? "bg-cyan-500/20 text-cyan-200 border border-cyan-500/60 shadow-[0_0_10px_rgba(6,182,212,0.25)] font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-[#07132e]/50 border border-transparent"
          }`}
          title="102-Band Near-Infrared Spectroscopy"
        >
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
          <span className="hidden sm:inline">102 Bands</span>
          <span className="sm:hidden">Bands</span>
        </button>

        <button
          onClick={() => setActiveTab("targets")}
          className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs transition-all ${
            activeTab === "targets"
              ? "bg-cyan-500/20 text-cyan-200 border border-cyan-500/60 shadow-[0_0_10px_rgba(6,182,212,0.25)] font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-[#07132e]/50 border border-transparent"
          }`}
          title="NASA 5-Target Scientific Benchmark Suite"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden md:inline">5 Targets</span>
          <span className="md:hidden">Targets</span>
        </button>
      </nav>

      {/* Right Controls: Milestone Badge & About */}
      <div className="flex items-center space-x-3 text-[11px]">
        <div className="hidden md:flex items-center space-x-1.5 text-slate-400 font-mono text-[10px]">
          <span className="text-cyan-400 font-semibold">M3:</span>
          <span>WCS Image Rendering</span>
        </div>
        <div className="flex items-center space-x-1 text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-900/50 text-[10px]">
          <Compass className="w-3 h-3" />
          <span>ICRS & WCS</span>
        </div>
        <button
          onClick={() => setActiveTab(activeTab === "about" ? "sky" : "about")}
          className={`p-1.5 rounded-lg border transition-all ${
            activeTab === "about"
              ? "bg-cyan-500/20 border-cyan-500/60 text-cyan-200"
              : "border-cyan-950/70 text-slate-400 hover:text-cyan-300 hover:bg-[#09152e]"
          }`}
          title="About SPHEREx Mission Architecture"
        >
          <Info className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
