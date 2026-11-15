"use client";

import React, { useState } from "react";
import { Layers, ShieldCheck, Cpu } from "lucide-react";

interface DetectorUnit {
  id: string;
  name: string;
  wavelengthRange: string;
  channelStart: number;
  channelEnd: number;
  resolvingPower: string;
  detectorMaterial: string;
  operatingTemp: string;
  primaryFeatures: string[];
  scienceRole: string;
}

const DETECTORS: DetectorUnit[] = [
  {
    id: "D1",
    name: "Detector Array 1 (D1)",
    wavelengthRange: "0.75 – 1.11 µm",
    channelStart: 1,
    channelEnd: 17,
    resolvingPower: "R ≈ 41",
    detectorMaterial: "Teledyne H2RG 2.5 µm cutoff HgCdTe",
    operatingTemp: "~80 K (Passive V-groove shield cooling)",
    primaryFeatures: ["Paschen-ζ / Paschen-η", "M-dwarf stellar continuum", "High-redshift Lyman-break galaxies"],
    scienceRole: "Probes the cosmic optical-infrared transition and large-scale galaxy clustering for early universe inflation.",
  },
  {
    id: "D2",
    name: "Detector Array 2 (D2)",
    wavelengthRange: "1.11 – 1.64 µm",
    channelStart: 18,
    channelEnd: 34,
    resolvingPower: "R ≈ 41",
    detectorMaterial: "Teledyne H2RG 2.5 µm cutoff HgCdTe",
    operatingTemp: "~80 K (Passive V-groove shield cooling)",
    primaryFeatures: ["Paschen-β (1.282 µm)", "1.6 µm H⁻ minimum opacity bump in cool stars"],
    scienceRole: "Maps massive star-forming regions and provides photometric redshift anchors for hundreds of millions of galaxies.",
  },
  {
    id: "D3",
    name: "Detector Array 3 (D3)",
    wavelengthRange: "1.64 – 2.42 µm",
    channelStart: 35,
    channelEnd: 51,
    resolvingPower: "R ≈ 41",
    detectorMaterial: "Teledyne H2RG 2.5 µm cutoff HgCdTe",
    operatingTemp: "~80 K (Passive V-groove shield cooling)",
    primaryFeatures: ["Molecular Hydrogen H₂ (2.12 µm)", "Brackett-γ (2.166 µm)", "CO first overtone bands (2.29 µm)"],
    scienceRole: "Traces supersonic protostellar shock waves and measures stellar velocity dispersions in nearby galaxies.",
  },
  {
    id: "D4",
    name: "Detector Array 4 (D4)",
    wavelengthRange: "2.42 – 3.82 µm",
    channelStart: 52,
    channelEnd: 68,
    resolvingPower: "R ≈ 135 (High-Resolution Band)",
    detectorMaterial: "Teledyne H2RG 5.3 µm cutoff HgCdTe",
    operatingTemp: "~60 K (Radiatively cooled intermediate stage)",
    primaryFeatures: ["Interstellar Water Ice (3.05 µm)", "PAH C–H stretch emission (3.29 µm)", "Aliphatic organics (3.4 µm)"],
    scienceRole: "Higher spectral resolution R≈135 enables detailed separation of volatile ice absorption mantles from organic dust emission.",
  },
  {
    id: "D5",
    name: "Detector Array 5 (D5)",
    wavelengthRange: "3.82 – 4.42 µm",
    channelStart: 69,
    channelEnd: 85,
    resolvingPower: "R ≈ 135 (High-Resolution Band)",
    detectorMaterial: "Teledyne H2RG 5.3 µm cutoff HgCdTe",
    operatingTemp: "~55 K (Dedicated passive cryogenic radiator)",
    primaryFeatures: ["Brackett-α (4.052 µm)", "Solid CO₂ ice band (4.27 µm)", "Gas-phase CO₂"],
    scienceRole: "Crucial for planetary ingredient surveys: measures carbon dioxide ice freezing points in protoplanetary disks.",
  },
  {
    id: "D6",
    name: "Detector Array 6 (D6)",
    wavelengthRange: "4.42 – 5.00 µm",
    channelStart: 86,
    channelEnd: 102,
    resolvingPower: "R ≈ 135 (High-Resolution Band)",
    detectorMaterial: "Teledyne H2RG 5.3 µm cutoff HgCdTe",
    operatingTemp: "~55 K (Dedicated passive cryogenic radiator)",
    primaryFeatures: ["Solid CO ice (4.67 µm)", "Gas-phase CO fundamental", "OCS ice (4.9 µm)", "Warm dust continuum"],
    scienceRole: "Unmasks carbon monoxide ice and deep infrared continuum emission from cold protostars and distant quasars.",
  },
];

export function DetectorArrayViewer() {
  const [selectedDetectorId, setSelectedDetectorId] = useState<string>("D4");
  const selected = DETECTORS.find((d) => d.id === selectedDetectorId) || DETECTORS[3];

  return (
    <div className="w-full border border-slate-800/80 rounded-2xl bg-[#040814]/90 backdrop-blur-sm overflow-hidden shadow-2xl my-8">
      {/* Telemetry bar */}
      <div className="px-6 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4 bg-[#02050f]/90">
        <div className="flex items-center gap-2.5">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200">
            Focal Plane Assembly: 6 Linear Variable Filter Detectors
          </span>
        </div>
        <div className="text-xs font-mono text-slate-300">
          6 × 2048×2048 H2RG Arrays · 102 Total Channels
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[460px]">
        {/* Interactive Focal Plane Layout Diagram */}
        <div className="lg:col-span-6 p-8 flex flex-col items-center justify-center bg-[#02040a]">
          <div className="w-full max-w-sm space-y-4">
            <div className="text-xs font-mono text-slate-400 text-center uppercase tracking-wider">
              Focal Plane Physical Layout
            </div>

            {/* 2-tier 3x2 detector grid */}
            <div className="grid grid-cols-3 gap-3">
              {DETECTORS.map((det) => {
                const isSelected = det.id === selectedDetectorId;
                return (
                  <button
                    key={det.id}
                    onClick={() => setSelectedDetectorId(det.id)}
                    className={`aspect-square p-3 rounded-lg flex flex-col items-center justify-between transition-all border text-left ${
                      isSelected
                        ? "bg-cyan-950/80 text-cyan-200 border-cyan-500 shadow-md ring-1 ring-cyan-500"
                        : "bg-slate-950/70 text-slate-300 border-slate-800 hover:border-slate-700 hover:text-slate-100"
                    }`}
                  >
                    <div className="w-full flex items-center justify-between">
                      <span className="font-mono font-bold text-sm">{det.id}</span>
                      <span className="text-[10px] font-mono text-slate-400">{det.resolvingPower.split(" ")[0]}</span>
                    </div>

                    {/* Authentic infrared linear filter coating indicator */}
                    <div className="w-full h-1.5 rounded bg-amber-500/40 my-1 opacity-90" />

                    <div className="w-full text-xs font-mono text-slate-400 truncate">
                      {det.wavelengthRange}
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="text-xs font-mono text-slate-400 text-center">
              Pixel Scale: 6.2″/pixel · FOV per array: 3.5° × 3.5°
            </div>
          </div>
        </div>

        {/* Selected Detector Detailed Specs & Science Role */}
        <div className="lg:col-span-6 p-6 lg:p-8 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-slate-800/80 bg-[#030611]">
          <div className="space-y-5">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Detector Specification
              </div>
              <h3 className="text-2xl font-bold text-slate-100 tracking-tight [text-wrap:balance]">
                {selected.name}
              </h3>
              <div className="text-xs font-mono text-cyan-300 mt-1">
                Wavelength Range: {selected.wavelengthRange} · Channels {selected.channelStart}–{selected.channelEnd} of 102
              </div>
            </div>

            {/* Quick Specs Readout - flattened */}
            <div className="grid grid-cols-2 gap-3 py-3 border-y border-slate-800 text-xs font-mono">
              <div>
                <span className="text-slate-400 block">Resolving Power:</span>
                <span className="text-slate-100 font-semibold">{selected.resolvingPower}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Operating Temp:</span>
                <span className="text-slate-100 font-semibold">{selected.operatingTemp.split(" ")[0]}</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-400 block">Detector Substrate:</span>
                <span className="text-slate-200">{selected.detectorMaterial}</span>
              </div>
            </div>

            {/* Primary Signatures */}
            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-2">
                Primary Spectral Signatures Detected:
              </span>
              <ul className="space-y-1 text-xs text-slate-300">
                {selected.primaryFeatures.map((feat, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Scientific Mission Role */}
            <div className="pl-3.5 border-l-2 border-cyan-500/50 text-xs text-slate-300 space-y-1">
              <span className="font-semibold text-cyan-300 block">Astrophysical Science Goal</span>
              <p className="text-slate-300 leading-relaxed [text-wrap:pretty]">{selected.scienceRole}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
