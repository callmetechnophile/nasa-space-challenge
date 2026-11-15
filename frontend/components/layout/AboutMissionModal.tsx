"use client";

import React from "react";
import { useSkyStore } from "@/stores/useSkyStore";
import { Info, X, ShieldCheck, Database, Layers, Radio, Globe, Compass } from "lucide-react";

export function AboutMissionModal() {
  const setActiveTab = useSkyStore((s) => s.setActiveTab);

  return (
    <div className="absolute inset-x-4 top-20 bottom-24 z-25 bg-[#040816]/95 backdrop-blur-xl border border-cyan-950/80 rounded-2xl shadow-2xl p-6 flex flex-col text-slate-200 pointer-events-auto overflow-y-auto">
      <div className="flex items-center justify-between pb-4 border-b border-cyan-950/80 mb-5">
        <div className="flex items-center space-x-2">
          <Info className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-bold text-cyan-100 font-sans">
            SkyTrace — SPHEREx Astronomy Development Environment
          </h2>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
            NASA Space Apps Challenge 2026
          </span>
        </div>
        <button
          onClick={() => setActiveTab("sky")}
          className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="space-y-5 font-sans text-xs text-slate-300 max-w-4xl leading-relaxed">
        {/* Mission Overview */}
        <section className="space-y-2">
          <h3 className="text-sm font-semibold text-cyan-300 font-mono flex items-center space-x-1.5">
            <Radio className="w-4 h-4 text-cyan-400" />
            <span>1. NASA SPHEREx Mission Summary</span>
          </h3>
          <p>
            SPHEREx (Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices Explorer) is a NASA MIDEX mission designed to perform the first near-infrared all-sky spectral survey. Operating across 102 spectroscopic channels from 0.75 to 5.00 µm with resolving power R ~ 35 - 130, SPHEREx maps the entire celestial sky every 6 months across 4 survey passes.
          </p>
        </section>

        {/* Scientific Capabilities */}
        <section className="space-y-2">
          <h3 className="text-sm font-semibold text-cyan-300 font-mono flex items-center space-x-1.5">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>2. Five Core Product Capabilities</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-[11px]">
            <div className="bg-[#09152e]/60 p-3 rounded border border-cyan-950/80 space-y-1">
              <span className="text-cyan-300 font-bold block">1. 3D Celestial Sphere:</span>
              <span className="text-slate-400 block">
                WebGL Three.js/R3F sphere, true ICRS equatorial grid, RA hour circles, Dec parallels, Milky Way galactic plane, and constellation outlines.
              </span>
            </div>
            <div className="bg-[#09152e]/60 p-3 rounded border border-cyan-950/80 space-y-1">
              <span className="text-cyan-300 font-bold block">2. RA/Dec Astronomical Search:</span>
              <span className="text-slate-400 block">
                Rigorous sexagesimal (HMS/DMS) and decimal degree parsing with smooth slerp camera flights and URL coordinate parameter support.
              </span>
            </div>
            <div className="bg-[#09152e]/60 p-3 rounded border border-cyan-950/80 space-y-1">
              <span className="text-cyan-300 font-bold block">3. Astronomical Image Visualization:</span>
              <span className="text-slate-400 block">
                Astropy WCS-calibrated FITS image processing with astronomical asinh/log/linear display stretches and dynamic tile mapping.
              </span>
            </div>
            <div className="bg-[#09152e]/60 p-3 rounded border border-cyan-950/80 space-y-1">
              <span className="text-cyan-300 font-bold block">4. Temporal Observation Explorer:</span>
              <span className="text-slate-400 block">
                Chronological 4-epoch playback, blink comparator, side-by-side mode, and difference imaging D(x,y) = |I2 - I1| with MAD noise estimation.
              </span>
            </div>
            <div className="bg-[#09152e]/60 p-3 rounded border border-cyan-950/80 space-y-1 md:col-span-2">
              <span className="text-cyan-300 font-bold block">5. 102-Band Near-Infrared Spectroscopy:</span>
              <span className="text-slate-400 block">
                Interactive exploration across Arrays 1–6 (0.75–5.00 µm), diagnostic molecular absorption bands (H2O ice 3.05 µm, PAH/CH4 3.3 µm, CO2 ice 4.27 µm, CO 4.67 µm).
              </span>
            </div>
          </div>
        </section>

        {/* Data Architecture & Non-fabrication Integrity */}
        <section className="space-y-2">
          <h3 className="text-sm font-semibold text-cyan-300 font-mono flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>3. Scientific Integrity & Data Provider Architecture</span>
          </h3>
          <p>
            To uphold rigorous scientific standards and eliminate fabricated observations, the system implements a modular Data Provider architecture:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-400 font-mono text-[11px]">
            <li>
              <span className="text-cyan-300 font-semibold">Curated NASA Sample Provider:</span> Verified target coordinates (Gaia DR3, AllWISE, 2MASS), accurate proper motion kinematics, authentic astrophysical SED models, and calibrated multi-epoch timeline for the 5 benchmark targets.
            </li>
            <li>
              <span className="text-cyan-300 font-semibold">NASA IRSA Live Connector:</span> Interfaces NASA IPAC/IRSA and CDS/SIMBAD TAP services with fail-safe fallback.
            </li>
            <li>
              <span className="text-cyan-300 font-semibold">Demonstration Simulator:</span> When uncatalogued sky coordinates are queried, data is explicitly tagged with <code className="text-amber-300 bg-black/40 px-1 py-0.5 rounded">is_simulated = True</code> and provenance flags.
            </li>
          </ul>
        </section>

        {/* Five NASA Validation Targets */}
        <section className="space-y-2">
          <h3 className="text-sm font-semibold text-cyan-300 font-mono flex items-center space-x-1.5">
            <Compass className="w-4 h-4 text-cyan-400" />
            <span>4. The Five NASA Validation Targets</span>
          </h3>
          <p className="text-slate-400 font-mono text-[11px]">
            1. <strong>Barnard&apos;s Star</strong> (GJ 699, M4.0V) — Highest known stellar proper motion (10.3&quot;/yr).<br />
            2. <strong>WISE 0855</strong> (WISE J0855-0714, Y2.0) — Coldest known brown dwarf (~250 K), prominent 4.5–5.0 µm atmospheric window.<br />
            3. <strong>Epsilon Indi B</strong> (HD 209100B, T1+T6) — Nearby binary brown dwarf with deep CH4 methane absorption.<br />
            4. <strong>RW Aurigae</strong> (K3e+K6e) — Classical young T Tauri star with episodic circumstellar dust occultations.<br />
            5. <strong>R Draconis</strong> (M5e-M9e) — Pulsating Mira variable AGB star with huge periodic IR amplitude variations.
          </p>
        </section>
      </div>
    </div>
  );
}
