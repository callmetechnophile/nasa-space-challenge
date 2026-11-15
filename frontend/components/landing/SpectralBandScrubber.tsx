"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AudioLines, ArrowRight } from "lucide-react";

interface BandInfo {
  channel: number;
  array: string;
  detectorName: string;
  wavelength: number; // in um
  feature: string;
  physicalRole: string;
}

// 10 key representative anchor bands across the 102 channels
const ANCHOR_BANDS: BandInfo[] = [
  {
    channel: 8,
    array: "Array 1 (D1)",
    detectorName: "Band 1 / D1",
    wavelength: 0.88,
    feature: "Paschen-ζ / Evolved Stellar Photospheres",
    physicalRole: "Probes older stellar populations and low-mass M-dwarf stellar continuum.",
  },
  {
    channel: 23,
    array: "Array 2 (D2)",
    detectorName: "Band 2 / D2",
    wavelength: 1.28,
    feature: "Paschen-β Recombination (1.282 µm)",
    physicalRole: "Quantifies ionised hydrogen gas in massive star-forming regions with minimal dust attenuation.",
  },
  {
    channel: 42,
    array: "Array 3 (D3)",
    detectorName: "Band 3 / D3",
    wavelength: 2.12,
    feature: "Molecular Hydrogen H₂ (v=1-0 S(1))",
    physicalRole: "Traces supersonic shocks and energetic bipolar protostellar outflows colliding with cold gas.",
  },
  {
    channel: 56,
    array: "Array 4 (D4)",
    detectorName: "Band 4 / D4",
    wavelength: 2.65,
    feature: "Water Vapor Hot Band (H₂O Gas)",
    physicalRole: "Diagnostic of warm molecular clouds and water release in cometary/protoplanetary envelopes.",
  },
  {
    channel: 61,
    array: "Array 4 (D4)",
    detectorName: "Band 4 / D4",
    wavelength: 3.05,
    feature: "H₂O Interstellar Ice Band (3.05 µm)",
    physicalRole: "Key biogenic ice absorption feature mapping water reservoir inventories across cold molecular cores.",
  },
  {
    channel: 65,
    array: "Array 4 (D4)",
    detectorName: "Band 4 / D4",
    wavelength: 3.30,
    feature: "PAH C–H Stretch Emission (3.29 µm)",
    physicalRole: "Fluorescent emission from complex aromatic organics excited by ambient interstellar UV radiation.",
  },
  {
    channel: 77,
    array: "Array 5 (D5)",
    detectorName: "Band 5 / D5",
    wavelength: 4.05,
    feature: "Brackett-α Recombination (4.052 µm)",
    physicalRole: "Highest-intensity infrared hydrogen line for unmasking heavily dust-embedded H II regions.",
  },
  {
    channel: 81,
    array: "Array 5 (D5)",
    detectorName: "Band 5 / D5",
    wavelength: 4.27,
    feature: "Solid-state CO₂ Ice Band (4.27 µm)",
    physicalRole: "Deep ice absorption diagnostic measuring carbon dioxide freezing in circumstellar planet-forming disks.",
  },
  {
    channel: 93,
    array: "Array 6 (D6)",
    detectorName: "Band 6 / D6",
    wavelength: 4.67,
    feature: "Carbon Monoxide Fundamental Band (CO)",
    physicalRole: "Measures solid CO ice and gaseous carbon monoxide in cool outer protostellar envelopes.",
  },
  {
    channel: 101,
    array: "Array 6 (D6)",
    detectorName: "Band 6 / D6",
    wavelength: 4.96,
    feature: "Deep Infrared Continuum & OCS Ice",
    physicalRole: "Probes carbonyl sulfide and cold thermal continuum near SPHEREx longest wavelength limit.",
  },
];

export function SpectralBandScrubber() {
  const [selectedChannel, setSelectedChannel] = useState<number>(61);

  // Compute or interpolate channel stats
  const minLam = 0.75;
  const maxLam = 5.0;
  const approxLambda = Number((minLam + (selectedChannel - 1) * ((maxLam - minLam) / 101)).toFixed(3));
  
  // Find closest anchor band
  const closestAnchor = ANCHOR_BANDS.reduce((prev, curr) =>
    Math.abs(curr.channel - selectedChannel) < Math.abs(prev.channel - selectedChannel) ? curr : prev
  );

  // Array designation based on channel
  const arrayIndex =
    selectedChannel <= 17 ? 1 :
    selectedChannel <= 34 ? 2 :
    selectedChannel <= 51 ? 3 :
    selectedChannel <= 68 ? 4 :
    selectedChannel <= 85 ? 5 : 6;

  // Resolving power R = lambda / delta_lambda ~ 41 to 135
  const resolvingPower = Math.round(41 + (selectedChannel / 102) * 85);

  return (
    <div className="w-full max-w-5xl mx-auto my-12 border border-slate-800/80 rounded-2xl bg-[#040814]/90 backdrop-blur-sm overflow-hidden shadow-xl">
      {/* Top telemetry bar */}
      <div className="px-6 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4 bg-[#02050f]/90">
        <div className="flex items-center gap-3">
          <AudioLines className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono tracking-wider text-slate-300 uppercase">
            102-Band Linear Variable Filter (LVF) Laboratory
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-slate-300">
          <span>SURVEY RANGE: <strong className="text-slate-100 font-semibold">0.75 – 5.00 µm</strong></span>
          <span className="text-slate-600">|</span>
          <span>CHANNELS: <strong className="text-cyan-300 font-semibold">102 CONTIGUOUS</strong></span>
        </div>
      </div>

      <div className="p-6 lg:p-8 space-y-8">
        {/* Dynamic Spectrum Curve Plot */}
        <div className="relative w-full h-44 sm:h-52 bg-[#02040c] border border-slate-800/80 rounded-xl p-4 overflow-hidden shadow-inner">
          {/* Axis markers */}
          <div className="absolute top-3 left-4 text-xs font-mono text-slate-400">
            FLUX DENSITY F_λ (MJy/sr)
          </div>
          <div className="absolute bottom-2 left-4 text-xs font-mono text-slate-400">0.75 µm</div>
          <div className="absolute bottom-2 right-4 text-xs font-mono text-slate-400">5.00 µm</div>

          {/* SVG Spectrum Curve with Water & CO2 Ice absorption dips and PAH emission peak */}
          <svg viewBox="0 0 800 200" preserveAspectRatio="none" className="w-full h-full" role="img" aria-label="Spectral Energy Distribution curve across 102 channels">
            <defs>
              <linearGradient id="spectrumGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                <stop offset="25%" stopColor="#2dd4bf" stopOpacity="0.8" />
                <stop offset="55%" stopColor="#a78bfa" stopOpacity="0.8" />
                <stop offset="75%" stopColor="#f43f5e" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#f97316" stopOpacity="0.8" />
              </linearGradient>
              <linearGradient id="curveFill" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid lines */}
            <line x1="0" y1="50" x2="800" y2="50" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.8" />
            <line x1="0" y1="100" x2="800" y2="100" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.8" />
            <line x1="0" y1="150" x2="800" y2="150" stroke="#1e293b" strokeDasharray="3 3" strokeWidth="0.8" />

            {/* Representative SED Curve */}
            <path
              d="M 0,110 
                 Q 100,70 180,85 
                 T 320,80 
                 Q 380,82 420,150 
                 Q 440,165 470,110 
                 Q 485,30 500,120 
                 Q 550,115 580,160 
                 Q 600,170 630,125 
                 Q 710,130 800,145"
              fill="none"
              stroke="url(#spectrumGradient)"
              strokeWidth="2.5"
            />
            {/* Fill under curve */}
            <path
              d="M 0,110 
                 Q 100,70 180,85 
                 T 320,80 
                 Q 380,82 420,150 
                 Q 440,165 470,110 
                 Q 485,30 500,120 
                 Q 550,115 580,160 
                 Q 600,170 630,125 
                 Q 710,130 800,145 L 800,200 L 0,200 Z"
              fill="url(#curveFill)"
            />

            {/* Interactive Selected Channel Indicator Line */}
            {(() => {
              const xPos = ((selectedChannel - 1) / 101) * 800;
              return (
                <g>
                  <line
                    x1={xPos}
                    y1="10"
                    x2={xPos}
                    y2="190"
                    stroke="#38bdf8"
                    strokeWidth="2"
                    strokeDasharray="4 2"
                  />
                  <circle cx={xPos} cy="100" r="5" fill="#38bdf8" />
                  <circle cx={xPos} cy="100" r="10" stroke="#38bdf8" strokeWidth="1" fill="none" opacity="0.6" />
                </g>
              );
            })()}
          </svg>
        </div>

        {/* Channel Scrubber Slider */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-300">
            <span>SCRUB CHANNELS (1 — 102)</span>
            <span className="text-cyan-300 font-semibold">CHANNEL {selectedChannel} / 102</span>
          </div>
          <input
            type="range"
            min={1}
            max={102}
            value={selectedChannel}
            onChange={(e) => setSelectedChannel(Number(e.target.value))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 hover:accent-cyan-300 focus:outline-none"
            aria-label="SPHEREx 102-channel spectral scrubber"
          />
          <div className="flex justify-between text-xs font-mono text-slate-400">
            <span>Array 1 (D1)</span>
            <span>Array 2 (D2)</span>
            <span>Array 3 (D3)</span>
            <span>Array 4 (D4)</span>
            <span>Array 5 (D5)</span>
            <span>Array 6 (D6)</span>
          </div>
        </div>

        {/* Selected Channel Scientific Readout Bar (No nested cards) */}
        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-800 border-t border-b border-slate-800/80 py-4">
          <div className="py-2 md:py-0 md:pr-4">
            <div className="text-xs font-mono text-slate-400 mb-1">DETECTOR ARRAY</div>
            <div className="text-base font-bold text-slate-100">Detector D{arrayIndex}</div>
            <div className="text-xs text-slate-400 mt-1">Linear Variable Filter Band {arrayIndex}</div>
          </div>
          <div className="py-2 md:py-0 md:px-4">
            <div className="text-xs font-mono text-slate-400 mb-1">WAVELENGTH & RESOLUTION</div>
            <div className="text-base font-bold text-cyan-300">{approxLambda} µm</div>
            <div className="text-xs text-slate-400 mt-1">Resolving Power R ≈ {resolvingPower}</div>
          </div>
          <div className="py-2 md:py-0 md:pl-4">
            <div className="text-xs font-mono text-slate-400 mb-1">PROXIMATE SIGNATURE</div>
            <div className="text-base font-bold text-slate-100 truncate">{closestAnchor.feature.split("/")[0]}</div>
            <div className="text-xs text-slate-400 mt-1 truncate">{closestAnchor.physicalRole}</div>
          </div>
        </div>

        {/* Quick jump anchor buttons */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-xs font-mono text-slate-400 mr-2">Featured Diagnostic Lines:</span>
          {ANCHOR_BANDS.slice(1, 7).map((b) => (
            <button
              key={b.channel}
              onClick={() => setSelectedChannel(b.channel)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors border ${
                selectedChannel === b.channel
                  ? "bg-cyan-950/80 text-cyan-200 border-cyan-500/50 shadow-sm"
                  : "bg-slate-900/40 text-slate-300 border-slate-800 hover:text-slate-100 hover:border-slate-700"
              }`}
            >
              Ch {b.channel} ({b.wavelength} µm)
            </button>
          ))}
        </div>

        {/* CTA link to full IDE spectral laboratory */}
        <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between flex-wrap gap-4">
          <span className="text-xs text-slate-400">
            Interactive spectral cube sampling is powered by calibrated SPHEREx FITS Level 2 products.
          </span>
          <Link
            href="/workspace?tab=spectral"
            className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-400 hover:text-cyan-300 group transition-colors"
          >
            <span>Explore the spectral laboratory</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>
    </div>
  );
}
