"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Clock, ArrowRight } from "lucide-react";

type TemporalViewMode = "epoch1" | "epoch2" | "diff" | "significance";

export function TemporalEpochComparison() {
  const [mode, setMode] = useState<TemporalViewMode>("diff");

  return (
    <div className="w-full max-w-5xl mx-auto my-12 border border-slate-800/80 rounded-2xl bg-[#040814]/90 backdrop-blur-sm overflow-hidden shadow-xl">
      {/* Top telemetry bar */}
      <div className="px-6 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4 bg-[#02050f]/90">
        <div className="flex items-center gap-3">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono tracking-wider text-slate-300 uppercase">
            Time-Domain Difference Pipeline (Δt = 8.1 Days)
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono text-slate-300">
          <span>COORDINATES: <strong className="text-slate-100 font-semibold">α 46.844°, δ +01.832°</strong></span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[460px]">
        {/* Visual display container */}
        <div className="lg:col-span-7 relative flex items-center justify-center p-8 bg-[#02040c] overflow-hidden min-h-[340px]">
          {/* Graphical rendering of the field */}
          <div className="relative w-72 h-72 sm:w-84 sm:h-84 border border-slate-800/80 rounded-xl bg-[#010207] overflow-hidden shadow-inner flex items-center justify-center">
            <svg viewBox="0 0 300 300" className="w-full h-full" role="img" aria-label={`Temporal comparison view in ${mode} mode`}>
              <defs>
                {/* Transient spot in Epoch 2 and Difference */}
                <radialGradient id="transientGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity="1" />
                  <stop offset="40%" stopColor="#2dd4bf" stopOpacity="0.7" />
                  <stop offset="80%" stopColor="#38bdf8" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
                </radialGradient>

                <radialGradient id="sigGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#f43f5e" stopOpacity="1" />
                  <stop offset="45%" stopColor="#fb7185" stopOpacity="0.8" />
                  <stop offset="85%" stopColor="#f43f5e" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="#f43f5e" stopOpacity="0" />
                </radialGradient>
              </defs>

              {/* Static background field stars (present in Epoch 1 & 2, canceled out in diff/significance) */}
              <g
                className="transition-opacity duration-500"
                style={{ opacity: mode === "epoch1" || mode === "epoch2" ? 1 : 0.08 }}
              >
                <circle cx="50" cy="60" r="3.0" fill="#f1f5f9" />
                <circle cx="85" cy="190" r="2.2" fill="#bae6fd" />
                <circle cx="230" cy="70" r="3.5" fill="#fef08a" />
                <circle cx="250" cy="220" r="2.8" fill="#f8fafc" />
                <circle cx="120" cy="240" r="1.8" fill="#e2e8f0" />
                <circle cx="210" cy="160" r="2.0" fill="#bae6fd" />
                <circle cx="70" cy="120" r="1.5" fill="#94a3b8" />
                <circle cx="180" cy="40" r="2.4" fill="#f1f5f9" />
              </g>

              {/* The transient source at center (x:150, y:150) */}
              {mode === "epoch1" && (
                /* In Epoch 1: source is quiescent / below detection threshold */
                <g>
                  <circle cx="150" cy="150" r="1.0" fill="#64748b" opacity="0.5" />
                </g>
              )}

              {mode === "epoch2" && (
                /* In Epoch 2: new transient burst appears */
                <g className="transition-all duration-500">
                  <circle cx="150" cy="150" r="28" fill="url(#transientGlow)" opacity="0.6" />
                  <circle cx="150" cy="150" r="4.5" fill="#ffffff" />
                  <circle cx="150" cy="150" r="12" stroke="#38bdf8" strokeWidth="1" fill="none" strokeDasharray="2 2" />
                </g>
              )}

              {mode === "diff" && (
                /* In Difference mode: static stars cancel, isolated point source emerges! */
                <g className="transition-all duration-500">
                  <circle cx="150" cy="150" r="40" fill="url(#transientGlow)" opacity="0.85" />
                  <circle cx="150" cy="150" r="5" fill="#ffffff" />
                  <circle cx="150" cy="150" r="16" stroke="#2dd4bf" strokeWidth="1.5" fill="none" />
                  {/* Astrometric crosshair */}
                  <line x1="120" y1="150" x2="135" y2="150" stroke="#38bdf8" strokeWidth="1.2" />
                  <line x1="165" y1="150" x2="180" y2="150" stroke="#38bdf8" strokeWidth="1.2" />
                  <line x1="150" y1="120" x2="150" y2="135" stroke="#38bdf8" strokeWidth="1.2" />
                  <line x1="150" y1="165" x2="150" y2="180" stroke="#38bdf8" strokeWidth="1.2" />
                </g>
              )}

              {mode === "significance" && (
                /* In Significance Map: matched filter SNR peaks at 18.5 sigma */
                <g className="transition-all duration-500">
                  <circle cx="150" cy="150" r="44" fill="url(#sigGlow)" opacity="0.9" />
                  <circle cx="150" cy="150" r="6" fill="#fff1f2" />
                  <circle cx="150" cy="150" r="22" stroke="#f43f5e" strokeWidth="1.5" fill="none" strokeDasharray="3 3" />
                  <text x="150" y="195" textAnchor="middle" fill="#f43f5e" fontSize="12" fontFamily="monospace" fontWeight="bold">
                    SNR: +18.46 σ
                  </text>
                </g>
              )}
            </svg>

            {/* Badge overlay on canvas */}
            <div className="absolute top-3 left-3 px-2.5 py-1 rounded bg-black/80 border border-slate-700/80 text-xs font-mono text-cyan-300">
              {mode === "epoch1" && "OBSERVE: 2026W31 (t₁)"}
              {mode === "epoch2" && "COMPARE: 2026W32 (t₂)"}
              {mode === "diff" && "DIFFERENCE: I₂ - I₁"}
              {mode === "significance" && "SIGNIFICANCE: S = Δ / σ"}
            </div>
          </div>
        </div>

        {/* Narrative & Mode Controls */}
        <div className="lg:col-span-5 p-6 lg:p-8 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-slate-800/80 bg-[#030611]">
          <div>
            <div className="text-xs font-mono text-cyan-400 mb-2">TIME-DOMAIN INVESTIGATION</div>
            <h3 className="text-xl font-bold text-slate-100 tracking-tight mb-3 [text-wrap:balance]">
              {mode === "epoch1" && "Epoch 1 — Baseline Survey"}
              {mode === "epoch2" && "Epoch 2 — Search Epoch"}
              {mode === "diff" && "Pixel-Matched Residual"}
              {mode === "significance" && "Matched-Filter Detection"}
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed mb-5 [text-wrap:pretty]">
              {mode === "epoch1" &&
                "Initial all-sky pass captures the baseline infrared emission. The transient target is either quiescent or below instrumental detection thresholds."}
              {mode === "epoch2" &&
                "Eight days later, SPHEREx scans the same coordinates. A variable star flares or an infrared transient erupts, superimposed against invariant stellar background."}
              {mode === "diff" &&
                "Subtracting the calibrated baseline from the search observation eliminates millions of static stars, leaving only true temporal astronomical flux variations."}
              {mode === "significance" &&
                "Convolving the difference image with the authentic native detector ePSF achieves optimal matched-filter detection, yielding +18.46σ significance with zero false positives."}
            </p>

            {/* Step Selector Buttons */}
            <div className="grid grid-cols-2 gap-2 mb-6">
              <button
                onClick={() => setMode("epoch1")}
                className={`px-3 py-2.5 rounded-lg text-xs font-medium text-left transition-all border ${
                  mode === "epoch1"
                    ? "bg-cyan-950/80 text-cyan-200 border-cyan-500/50 shadow-sm"
                    : "bg-slate-900/50 text-slate-300 border-slate-800 hover:text-slate-100 hover:bg-slate-800/50"
                }`}
              >
                1. Observe (t₁)
              </button>
              <button
                onClick={() => setMode("epoch2")}
                className={`px-3 py-2.5 rounded-lg text-xs font-medium text-left transition-all border ${
                  mode === "epoch2"
                    ? "bg-cyan-950/80 text-cyan-200 border-cyan-500/50 shadow-sm"
                    : "bg-slate-900/50 text-slate-300 border-slate-800 hover:text-slate-100 hover:bg-slate-800/50"
                }`}
              >
                2. Compare (t₂)
              </button>
              <button
                onClick={() => setMode("diff")}
                className={`px-3 py-2.5 rounded-lg text-xs font-medium text-left transition-all border ${
                  mode === "diff"
                    ? "bg-cyan-950/80 text-cyan-200 border-cyan-500/50 shadow-sm"
                    : "bg-slate-900/50 text-slate-300 border-slate-800 hover:text-slate-100 hover:bg-slate-800/50"
                }`}
              >
                3. Difference (Δ)
              </button>
              <button
                onClick={() => setMode("significance")}
                className={`px-3 py-2.5 rounded-lg text-xs font-medium text-left transition-all border ${
                  mode === "significance"
                    ? "bg-rose-950/80 text-rose-200 border-rose-500/50 shadow-sm"
                    : "bg-slate-900/50 text-slate-300 border-slate-800 hover:text-slate-100 hover:bg-slate-800/50"
                }`}
              >
                4. Significance (SNR)
              </button>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800/80">
            <Link
              href="/workspace?tab=temporal"
              className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-400 hover:text-cyan-300 group transition-colors"
            >
              <span>See temporal analysis</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
