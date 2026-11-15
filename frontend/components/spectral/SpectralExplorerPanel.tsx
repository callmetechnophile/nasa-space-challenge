"use client";

import React, { useMemo, useState } from "react";
import { useSkyStore } from "@/stores/useSkyStore";
import { Activity, Layers, Sparkles, Sliders, Info, CheckCircle2 } from "lucide-react";

export function SpectralExplorerPanel() {
  const bands = useSkyStore((s) => s.bands);
  const selectedChannel = useSkyStore((s) => s.selectedChannel);
  const setSelectedChannel = useSkyStore((s) => s.setSelectedChannel);
  const spectralProfile = useSkyStore((s) => s.spectralProfile);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);

  const [activeArrayTab, setActiveArrayTab] = useState<number | "all">("all");
  const [hoveredPoint, setHoveredPoint] = useState<any | null>(null);

  // Filter bands according to selected array tab
  const filteredBands = useMemo(() => {
    if (activeArrayTab === "all") return bands;
    return bands.filter((b) => b.array_index === activeArrayTab);
  }, [bands, activeArrayTab]);

  const activeBand = useMemo(() => {
    return bands.find((b) => b.channel_index === selectedChannel) || bands[0];
  }, [bands, selectedChannel]);

  // Compute SVG plot scales
  const plotData = useMemo(() => {
    if (!spectralProfile || spectralProfile.length === 0) return null;

    const valid = spectralProfile.filter((p) => p.flux_mjy !== null && p.flux_mjy !== undefined);
    if (valid.length === 0) return null;

    const minX = 0.7;
    const maxX = 5.05;
    const fluxes = valid.map((p) => p.flux_mjy as number);
    const minY = 0.0;
    const maxY = Math.max(...fluxes) * 1.25 || 1.0;

    const width = 760;
    const height = 240;
    const padX = 55;
    const padY = 30;

    const scaleX = (wl: number) => padX + ((wl - minX) / (maxX - minX)) * (width - 2 * padX);
    const scaleY = (fl: number) => height - padY - ((fl - minY) / (maxY - minY)) * (height - 2 * padY);

    const points = valid.map((p) => ({
      ...p,
      x: scaleX(p.wavelength_um),
      y: scaleY(p.flux_mjy as number),
      errTop: p.flux_err_mjy ? scaleY((p.flux_mjy as number) + p.flux_err_mjy) : null,
      errBottom: p.flux_err_mjy ? scaleY(Math.max(0, (p.flux_mjy as number) - p.flux_err_mjy)) : null,
    }));

    const linePath = points.map((pt, i) => `${i === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`).join(" ");

    return { points, linePath, width, height, minX, maxX, minY, maxY, scaleX, scaleY };
  }, [spectralProfile]);

  return (
    <div className="absolute inset-x-4 top-20 bottom-24 z-25 bg-[#040816]/95 backdrop-blur-xl border border-cyan-950/80 rounded-2xl shadow-2xl p-5 flex flex-col text-slate-200 pointer-events-auto overflow-hidden">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between pb-4 border-b border-cyan-950/80 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-bold text-cyan-100 tracking-wide font-sans">
              SPHEREx 102 Spectral Bands Explorer (0.75 – 5.00 µm)
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              R ~ 35 - 130
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Target: <span className="text-cyan-300 font-semibold">{selectedTarget ? selectedTarget.name : "Active Sky Region"}</span> | Spectral Class: {selectedTarget ? selectedTarget.spectral_class : "Continuum"}
          </p>
        </div>

        {/* Array Tabs (1 to 6 or All) */}
        <div className="flex items-center space-x-1 font-mono text-xs">
          <button
            onClick={() => setActiveArrayTab("all")}
            className={`px-2.5 py-1 rounded text-[11px] transition-all ${
              activeArrayTab === "all"
                ? "bg-cyan-500 text-slate-950 font-semibold shadow-[0_0_8px_rgba(6,182,212,0.3)]"
                : "bg-[#09152e] text-slate-400 hover:text-slate-200"
            }`}
          >
            All 102 Bands
          </button>
          {[1, 2, 3, 4, 5, 6].map((arrId) => (
            <button
              key={arrId}
              onClick={() => setActiveArrayTab(arrId)}
              className={`px-2 py-1 rounded text-[11px] transition-all ${
                activeArrayTab === arrId
                  ? "bg-cyan-500 text-slate-950 font-semibold shadow-[0_0_8px_rgba(6,182,212,0.3)]"
                  : "bg-[#09152e] text-slate-400 hover:text-slate-200"
              }`}
            >
              Arr {arrId}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Layout: Left Spectrum Graph, Right Band Inspector */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-5 pt-4 overflow-hidden">
        {/* Interactive Spectral Flux Chart (2 Columns) */}
        <div className="lg:col-span-2 flex flex-col bg-[#060c1d]/90 border border-cyan-950/80 rounded-xl p-4 shadow-inner overflow-hidden">
          <div className="flex items-center justify-between font-mono text-xs text-slate-400 mb-2">
            <span className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span>Spectral Energy Distribution (SED) F_λ (mJy) vs Wavelength (µm)</span>
            </span>
            {activeBand && (
              <span className="text-cyan-300">
                Active Channel: {activeBand.channel_index} ({activeBand.wavelength_um.toFixed(3)} µm)
              </span>
            )}
          </div>

          {/* SVG Plot */}
          <div className="flex-1 w-full relative flex items-center justify-center">
            {plotData ? (
              <svg
                viewBox={`0 0 ${plotData.width} ${plotData.height}`}
                className="w-full h-full max-h-[300px] select-none"
              >
                {/* Background Grid */}
                {[1.0, 2.0, 3.0, 4.0, 5.0].map((wl) => {
                  const x = plotData.scaleX(wl);
                  return (
                    <g key={`grid-x-${wl}`}>
                      <line
                        x1={x}
                        y1={20}
                        x2={x}
                        y2={plotData.height - 25}
                        stroke="#1e293b"
                        strokeDasharray="3 3"
                      />
                      <text
                        x={x}
                        y={plotData.height - 10}
                        textAnchor="middle"
                        fill="#64748b"
                        fontSize="10"
                        fontFamily="monospace"
                      >
                        {wl.toFixed(1)} µm
                      </text>
                    </g>
                  );
                })}

                {/* Absorption Feature Annotations */}
                {[
                  { name: "H2O Ice", wl: 3.05, color: "#38bdf8" },
                  { name: "PAH/CH4", wl: 3.3, color: "#a855f7" },
                  { name: "CO2 Ice", wl: 4.27, color: "#f43f5e" },
                  { name: "CO Ice/Gas", wl: 4.67, color: "#f59e0b" },
                ].map((feat) => {
                  const x = plotData.scaleX(feat.wl);
                  return (
                    <g key={feat.name}>
                      <line
                        x1={x}
                        y1={22}
                        x2={x}
                        y2={plotData.height - 30}
                        stroke={feat.color}
                        strokeWidth="1"
                        strokeOpacity="0.4"
                      />
                      <text
                        x={x}
                        y={28}
                        textAnchor="middle"
                        fill={feat.color}
                        fontSize="9"
                        fontFamily="monospace"
                        fontWeight="bold"
                      >
                        {feat.name}
                      </text>
                    </g>
                  );
                })}

                {/* Spectral Curve Path */}
                <path
                  d={plotData.linePath}
                  fill="none"
                  stroke="#06b6d4"
                  strokeWidth="2.2"
                />

                {/* Active Band Cursor Line */}
                {activeBand && (
                  <line
                    x1={plotData.scaleX(activeBand.wavelength_um)}
                    y1={15}
                    x2={plotData.scaleX(activeBand.wavelength_um)}
                    y2={plotData.height - 25}
                    stroke="#22d3ee"
                    strokeWidth="2"
                    strokeDasharray="4 2"
                  />
                )}

                {/* Data Points with Error Bars */}
                {plotData.points.map((pt) => {
                  const isSelected = pt.channel_index === selectedChannel;
                  return (
                    <g
                      key={pt.channel_index}
                      className="cursor-pointer"
                      onClick={() => setSelectedChannel(pt.channel_index)}
                      onMouseEnter={() => setHoveredPoint(pt)}
                      onMouseLeave={() => setHoveredPoint(null)}
                    >
                      {/* Error bar */}
                      {pt.errTop !== null && pt.errBottom !== null && (
                        <line
                          x1={pt.x}
                          y1={pt.errTop}
                          x2={pt.x}
                          y2={pt.errBottom}
                          stroke="#0891b2"
                          strokeWidth="1"
                          opacity="0.6"
                        />
                      )}
                      {/* Point Circle */}
                      <circle
                        cx={pt.x}
                        cy={pt.y}
                        r={isSelected ? 4.5 : 2.5}
                        fill={isSelected ? "#22d3ee" : "#38bdf8"}
                        stroke="#040816"
                        strokeWidth="1.5"
                      />
                    </g>
                  );
                })}
              </svg>
            ) : (
              <div className="text-slate-500 font-mono text-xs">
                Loading 102-channel spectral energy distribution...
              </div>
            )}
          </div>

          {/* Hover Tooltip Readout */}
          <div className="h-6 mt-1 flex items-center justify-between font-mono text-[11px] text-cyan-300">
            {hoveredPoint ? (
              <span>
                Band {hoveredPoint.channel_index}: λ = {hoveredPoint.wavelength_um.toFixed(3)} µm | Flux = {hoveredPoint.flux_mjy?.toFixed(3)} mJy (±{hoveredPoint.flux_err_mjy?.toFixed(3)})
              </span>
            ) : (
              <span className="text-slate-400">
                Hover or click any spectral point to inspect flux & molecular band associations.
              </span>
            )}
          </div>
        </div>

        {/* Right Active Band Detail Inspector (1 Column) */}
        <div className="flex flex-col bg-[#060c1d]/90 border border-cyan-950/80 rounded-xl p-4 space-y-3 font-sans overflow-y-auto">
          <div className="border-b border-cyan-950/80 pb-2.5">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-semibold block">
              Band Diagnostic Readout
            </span>
            <h3 className="text-base font-bold text-cyan-100 font-mono">
              Channel {activeBand?.channel_index}: {activeBand?.wavelength_um.toFixed(3)} µm
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              {activeBand?.array_name} — Linear Variable Filter (LVF)
            </span>
          </div>

          {/* Instrument Specifications Table */}
          <div className="bg-[#09152e]/70 border border-cyan-950/80 rounded-lg p-3 font-mono text-xs space-y-1.5">
            <div className="flex justify-between">
              <span className="text-slate-400">Central Wavelength:</span>
              <span className="text-cyan-300 font-semibold">{activeBand?.wavelength_um.toFixed(3)} µm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Bandwidth (Δλ):</span>
              <span className="text-slate-200">{activeBand?.bandwidth_um.toFixed(4)} µm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Resolving Power (R):</span>
              <span className="text-amber-300 font-semibold">R ~ {activeBand?.resolving_power_r}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Array Number:</span>
              <span className="text-purple-300">Array {activeBand?.array_index}</span>
            </div>
          </div>

          {/* Key Astrophysical Signatures in this Band */}
          <div className="space-y-1 text-xs">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-semibold block">
              Astrophysical Signatures:
            </span>
            <p className="text-slate-300 leading-relaxed text-[11px] bg-[#09152e]/40 p-2 rounded border border-slate-800">
              {activeBand?.key_features}
            </p>
          </div>

          {/* Rapid Channel Selector Slider */}
          <div className="space-y-1 pt-2 border-t border-cyan-950/60 font-mono">
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>Channel Slider (1 to 102):</span>
              <span className="text-cyan-300 font-bold">{selectedChannel}</span>
            </div>
            <input
              type="range"
              min={1}
              max={102}
              value={selectedChannel}
              onChange={(e) => setSelectedChannel(Number(e.target.value))}
              className="w-full accent-cyan-500 cursor-pointer"
            />
          </div>

          {/* Channel Grid Badges */}
          <div className="pt-2">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 mb-1.5 block font-semibold">
              Select Channel (Array {activeArrayTab}):
            </span>
            <div className="max-h-36 overflow-y-auto grid grid-cols-6 gap-1 font-mono text-[10px]">
              {filteredBands.map((b) => (
                <button
                  key={b.channel_index}
                  onClick={() => setSelectedChannel(b.channel_index)}
                  className={`py-1 rounded text-center transition-all ${
                    selectedChannel === b.channel_index
                      ? "bg-cyan-500 text-slate-950 font-bold shadow-[0_0_8px_rgba(6,182,212,0.4)]"
                      : "bg-[#09152e] hover:bg-[#0e2149] text-cyan-200/80 border border-cyan-950"
                  }`}
                >
                  {b.channel_index}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
