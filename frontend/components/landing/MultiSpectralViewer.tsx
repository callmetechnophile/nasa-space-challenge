"use client";

import React, { useState } from "react";
import { Eye, Sparkles, Layers, Flame } from "lucide-react";

interface SpectralRegime {
  id: string;
  name: string;
  wavelength: string;
  bandRange: string;
  detector: string;
  icon: React.ComponentType<{ className?: string }>;
  physicalPhenomenon: string;
  astronomyInsight: string;
  visualDustOpacity: number;
  visualCoreColor: string;
  visualFilamentOpacity: number;
}

const REGIMES: SpectralRegime[] = [
  {
    id: "optical",
    name: "Optical (Visible)",
    wavelength: "0.55 µm",
    bandRange: "Human Vision (V-Band)",
    detector: "External Optical Survey",
    icon: Eye,
    physicalPhenomenon: "Heavy dust extinction & silhouette scattering",
    astronomyInsight:
      "Dense clouds of sub-micron silicate dust grains completely block and absorb background starlight. The central protostar and inner accretion disk are entirely invisible to optical telescopes.",
    visualDustOpacity: 0.85,
    visualCoreColor: "#64748b",
    visualFilamentOpacity: 0.1,
  },
  {
    id: "nir",
    name: "Near-Infrared",
    wavelength: "1.25 µm",
    bandRange: "SPHEREx Array D1 (0.75–1.1 µm) & D2",
    detector: "Detectors D1 / D2",
    icon: Sparkles,
    physicalPhenomenon: "Rayleigh scattering reduction & stellar continuum",
    astronomyInsight:
      "Because scattering cross-section drops as λ⁻⁴, near-infrared photons penetrate the surrounding dust envelope. Hundreds of previously obscured background red giants and young stellar objects emerge.",
    visualDustOpacity: 0.45,
    visualCoreColor: "#38bdf8",
    visualFilamentOpacity: 0.35,
  },
  {
    id: "mir_pah",
    name: "Mid-Infrared (PAH Dust)",
    wavelength: "3.30 µm",
    bandRange: "SPHEREx Array D4 (2.4–3.8 µm)",
    detector: "Detector D4",
    icon: Flame,
    physicalPhenomenon: "Aromatic C–H vibrational stretch luminescence",
    astronomyInsight:
      "Complex organic molecules known as Polycyclic Aromatic Hydrocarbons (PAHs) absorb UV starlight and re-emit via discrete vibrational resonances at 3.3 µm, tracing warm photodissociation ridges.",
    visualDustOpacity: 0.2,
    visualCoreColor: "#2dd4bf",
    visualFilamentOpacity: 0.75,
  },
  {
    id: "deep_ir",
    name: "Deep Infrared (Biogenic Ices)",
    wavelength: "4.80 µm",
    bandRange: "SPHEREx Array D6 (4.4–5.0 µm)",
    detector: "Detector D6",
    icon: Layers,
    physicalPhenomenon: "Interstellar ice absorption & embedded protostars",
    astronomyInsight:
      "Unmasks cold grain mantles containing water ice (H₂O), carbon dioxide (CO₂), and carbon monoxide (CO). These biogenic reservoirs represent the chemical precursors of habitable planetary systems.",
    visualDustOpacity: 0.08,
    visualCoreColor: "#fb7185",
    visualFilamentOpacity: 0.9,
  },
];

export function MultiSpectralViewer() {
  const [activeRegimeId, setActiveRegimeId] = useState<string>("mir_pah");
  const current = REGIMES.find((r) => r.id === activeRegimeId) || REGIMES[0];

  return (
    <div className="w-full max-w-5xl mx-auto my-12 border border-slate-800/80 rounded-2xl bg-[#040814]/90 backdrop-blur-sm overflow-hidden shadow-xl">
      {/* Top scientific telemetry bar */}
      <div className="px-6 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4 bg-[#02050f]/90">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          <span className="text-xs font-mono tracking-wider text-slate-300 uppercase">
            Spectral Dimension Decomposition
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-slate-300">
          <span>CENTRAL λ: <strong className="text-cyan-300 font-semibold">{current.wavelength}</strong></span>
          <span className="text-slate-600">|</span>
          <span className="hidden sm:inline">{current.detector}</span>
        </div>
      </div>

      {/* Main viewer section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[460px]">
        {/* Interactive simulated celestial view */}
        <div className="lg:col-span-7 relative flex items-center justify-center p-8 bg-[#02040a] overflow-hidden min-h-[320px]">
          {/* Celestial object simulation SVG */}
          <div className="relative w-72 h-72 sm:w-88 sm:h-88 flex items-center justify-center transition-all duration-700 ease-out">
            <svg viewBox="0 0 400 400" className="w-full h-full drop-shadow-xl" role="img" aria-label={`Simulated celestial view in ${current.name}`}>
              <defs>
                {/* Core emission */}
                <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor={current.visualCoreColor} stopOpacity="0.95" />
                  <stop offset="35%" stopColor={current.visualCoreColor} stopOpacity="0.5" />
                  <stop offset="70%" stopColor={current.visualCoreColor} stopOpacity="0.12" />
                  <stop offset="100%" stopColor={current.visualCoreColor} stopOpacity="0" />
                </radialGradient>

                {/* Filament emission */}
                <radialGradient id="filamentGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity={current.visualFilamentOpacity} />
                  <stop offset="60%" stopColor="#2dd4bf" stopOpacity={current.visualFilamentOpacity * 0.6} />
                  <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
                </radialGradient>
              </defs>

              {/* Background stars (more visible as dust clears) */}
              <g className="transition-opacity duration-700" style={{ opacity: 1 - current.visualDustOpacity * 0.7 }}>
                <circle cx="60" cy="80" r="1.5" fill="#f8fafc" />
                <circle cx="95" cy="290" r="1.2" fill="#bae6fd" />
                <circle cx="330" cy="110" r="1.5" fill="#fef08a" />
                <circle cx="310" cy="320" r="1.8" fill="#f8fafc" />
                <circle cx="150" cy="50" r="1.0" fill="#e0f2fe" />
                <circle cx="270" cy="70" r="1.4" fill="#fed7aa" />
                <circle cx="210" cy="350" r="1.2" fill="#f8fafc" />
                <circle cx="70" cy="180" r="1.6" fill="#bae6fd" />
              </g>

              {/* Extended nebular gas filaments */}
              <path
                d="M120,200 C80,120 180,80 200,140 C220,200 320,160 300,240 C280,320 160,300 120,200 Z"
                fill="url(#filamentGlow)"
                className="transition-all duration-700 ease-out"
                transform="rotate(25 200 200)"
              />
              <path
                d="M140,180 C100,260 200,320 260,260 C320,200 260,110 200,160 C160,200 150,150 140,180 Z"
                fill="url(#filamentGlow)"
                className="transition-all duration-700 ease-out"
                transform="rotate(-40 200 200)"
              />

              {/* Central protostellar core */}
              <circle cx="200" cy="200" r="130" fill="url(#coreGlow)" />
              <circle
                cx="200"
                cy="200"
                r="18"
                fill={current.visualCoreColor}
                className="transition-all duration-500"
              />

              {/* Foreground obscuring dust lane (strong in optical, fades in infrared) */}
              <path
                d="M80,240 Q150,180 210,210 T320,180 Q260,240 190,230 T80,240 Z"
                fill="#02040a"
                className="transition-all duration-700 ease-out"
                style={{ opacity: current.visualDustOpacity }}
              />
              <path
                d="M130,170 Q180,140 240,160 T310,140 Q250,190 190,180 T130,170 Z"
                fill="#030712"
                className="transition-all duration-700 ease-out"
                style={{ opacity: current.visualDustOpacity * 0.9 }}
              />

              {/* Targeting reticle ring */}
              <circle
                cx="200"
                cy="200"
                r="50"
                stroke="rgba(56, 189, 248, 0.3)"
                strokeWidth="1"
                strokeDasharray="4 4"
                fill="none"
              />
              <line x1="140" y1="200" x2="160" y2="200" stroke="rgba(56, 189, 248, 0.4)" strokeWidth="1" />
              <line x1="240" y1="200" x2="260" y2="200" stroke="rgba(56, 189, 248, 0.4)" strokeWidth="1" />
              <line x1="200" y1="140" x2="200" y2="160" stroke="rgba(56, 189, 248, 0.4)" strokeWidth="1" />
              <line x1="200" y1="240" x2="200" y2="260" stroke="rgba(56, 189, 248, 0.4)" strokeWidth="1" />
            </svg>
          </div>

          <div className="absolute bottom-4 left-6 text-xs font-mono text-slate-400">
            SPHEREx Simulation Model · Source: Star-Forming Nebula Core
          </div>
        </div>

        {/* Editorial description and regime selector */}
        <div className="lg:col-span-5 p-6 lg:p-8 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-slate-800/80 bg-[#030611]">
          <div>
            <div className="text-xs font-mono text-cyan-400 mb-2">{current.bandRange}</div>
            <h3 className="text-xl font-bold text-slate-100 tracking-tight mb-3 [text-wrap:balance]">
              {current.name}
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed mb-5 [text-wrap:pretty]">
              {current.astronomyInsight}
            </p>

            <div className="pl-3.5 border-l-2 border-cyan-500/50 text-xs text-slate-300 mb-6 space-y-1">
              <span className="font-semibold text-cyan-300 block">Astrophysical Mechanism</span>
              <p className="text-slate-300 leading-relaxed [text-wrap:pretty]">{current.physicalPhenomenon}</p>
            </div>
          </div>

          {/* Regime selector buttons */}
          <div className="space-y-2 pt-2 border-t border-slate-800/60">
            <div className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-2">
              Select Observation Band:
            </div>
            <div className="grid grid-cols-2 gap-2">
              {REGIMES.map((r) => {
                const Icon = r.icon;
                const isSelected = r.id === activeRegimeId;
                return (
                  <button
                    key={r.id}
                    onClick={() => setActiveRegimeId(r.id)}
                    className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs font-medium transition-all text-left ${
                      isSelected
                        ? "bg-cyan-950/80 text-cyan-200 border border-cyan-500/50 shadow-sm"
                        : "bg-slate-900/40 text-slate-300 border border-slate-800/60 hover:bg-slate-800/50 hover:text-slate-100"
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 shrink-0 ${isSelected ? "text-cyan-400" : "text-slate-400"}`} />
                    <span className="truncate">{r.name.split(" ")[0]} ({r.wavelength})</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
