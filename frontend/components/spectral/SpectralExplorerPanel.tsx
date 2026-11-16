"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useSkyStore } from "@/stores/useSkyStore";
import {
  Activity,
  Layers,
  Sparkles,
  Sliders,
  Info,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  FileCode2,
  Download,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Compass,
} from "lucide-react";

function getNominalBand(channel: number) {
  const arrays = [
    { arr: 1, min: 0.75, max: 1.11, count: 17, r: 41.0, feat: "Paschen series, CN absorption, Na I doublet, stellar continuum" },
    { arr: 2, min: 1.11, max: 1.64, count: 17, r: 41.0, feat: "J/H-band continuum, FeH, H2O vapor, Paschen beta" },
    { arr: 3, min: 1.64, max: 2.42, count: 17, r: 41.0, feat: "H/K-band continuum, CO overtone, H2 1-0 S(1), water vapor" },
    { arr: 4, min: 2.42, max: 3.82, count: 17, r: 35.0, feat: "H2O ice (3.05 µm), PAH (3.3 µm), CH4 methane absorption" },
    { arr: 5, min: 3.82, max: 4.42, count: 17, r: 110.0, feat: "High-resolution CO2 ice (4.27 µm), 13CO2 ice, SO2" },
    { arr: 6, min: 4.42, max: 5.00, count: 17, r: 130.0, feat: "High-resolution CO gas & ice (4.67 µm), XCN (4.62 µm), OCS" },
  ];
  const arrIdx = Math.max(1, Math.min(6, Math.ceil(channel / 17)));
  const cfg = arrays[arrIdx - 1];
  const idxInArr = (channel - 1) % 17;
  const step = (cfg.max - cfg.min) / 17;
  const wl = cfg.min + (idxInArr + 0.5) * step;
  const bw = wl / cfg.r;
  return {
    channel_index: channel,
    array_index: arrIdx,
    array_name: `Array ${arrIdx}`,
    wavelength_um: Number(wl.toFixed(4)),
    bandwidth_um: Number(bw.toFixed(5)),
    resolving_power_r: cfg.r,
    key_features: `${cfg.feat} (~${wl.toFixed(2)} µm)`,
  };
}

export function SpectralExplorerPanel() {
  const bands = useSkyStore((s) => s.bands);
  const selectedChannel = useSkyStore((s) => s.selectedChannel);
  const setSelectedChannel = useSkyStore((s) => s.setSelectedChannel);
  const spectralProfile = useSkyStore((s) => s.spectralProfile);
  const isSpectralLoading = useSkyStore((s) => s.isSpectralLoading);
  const spectralCoverageState = useSkyStore((s) => s.spectralCoverageState);
  const spectralMode = useSkyStore((s) => s.spectralMode);
  const setSpectralMode = useSkyStore((s) => s.setSpectralMode);
  const bandCatalogState = useSkyStore((s) => s.bandCatalogState);
  const loadBandCatalogue = useSkyStore((s) => s.loadBandCatalogue);
  const loadSpectralProfile = useSkyStore((s) => s.loadSpectralProfile);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const raDeg = useSkyStore((s) => s.raDeg);
  const decDeg = useSkyStore((s) => s.decDeg);

  const [activeArrayTab, setActiveArrayTab] = useState<number | "all">("all");
  const [hoveredPoint, setHoveredPoint] = useState<any | null>(null);

  // Load band catalogue and spectral profile on mount or coordinate shift
  useEffect(() => {
    if (bands.length === 0) {
      loadBandCatalogue();
    }
    loadSpectralProfile(raDeg, decDeg, selectedTarget?.id, spectralMode);
  }, [raDeg, decDeg, selectedTarget?.id, spectralMode, bands.length, loadBandCatalogue, loadSpectralProfile]);

  // Guaranteed active band metadata: never empty or undefined
  const activeBand = useMemo(() => {
    const found = bands.find((b) => b.channel_index === selectedChannel);
    if (found) return found;
    return getNominalBand(selectedChannel || 20);
  }, [bands, selectedChannel]);

  // Full 102 bands list (fallback to nominal if loading)
  const fullBandsList = useMemo(() => {
    if (bands && bands.length === 102) return bands;
    return Array.from({ length: 102 }, (_, i) => getNominalBand(i + 1));
  }, [bands]);

  // Filter bands according to selected array tab
  const filteredBands = useMemo(() => {
    if (activeArrayTab === "all") return fullBandsList;
    return fullBandsList.filter((b) => b.array_index === activeArrayTab);
  }, [fullBandsList, activeArrayTab]);

  // Active measurement for currently selected band
  const activeMeasurement = useMemo(() => {
    return (spectralProfile || []).find((p) => p.channel_index === selectedChannel) || null;
  }, [spectralProfile, selectedChannel]);

  // Count of valid flight measurements
  const validMeasurements = useMemo(() => {
    return (spectralProfile || []).filter((p) => p.flux_is_available && p.flux_mjy !== null);
  }, [spectralProfile]);

  // Compute SVG plot scales
  const plotData = useMemo(() => {
    if (!spectralProfile || spectralProfile.length === 0) return null;

    const valid = spectralProfile.filter((p) => p.flux_is_available && p.flux_mjy !== null);
    if (valid.length === 0 && spectralMode === "real") return null;

    const minX = 0.7;
    const maxX = 5.05;
    const pointsToPlot = spectralMode === "real" ? valid : spectralProfile;
    if (pointsToPlot.length === 0) return null;

    const fluxes = pointsToPlot.map((p) => (p.flux_mjy !== null ? (p.flux_mjy as number) : 0));
    const minY = 0.0;
    const maxY = Math.max(...fluxes) * 1.3 || 1.0;

    const width = 760;
    const height = 240;
    const padX = 55;
    const padY = 30;

    const scaleX = (wl: number) => padX + ((wl - minX) / (maxX - minX)) * (width - 2 * padX);
    const scaleY = (fl: number) => height - padY - ((fl - minY) / (maxY - minY)) * (height - 2 * padY);

    const points = pointsToPlot.map((p) => {
      const fl = p.flux_mjy !== null ? (p.flux_mjy as number) : 0;
      const err = p.flux_err_mjy || 0;
      return {
        ...p,
        x: scaleX(p.wavelength_um),
        y: scaleY(fl),
        errTop: p.flux_err_mjy ? scaleY(fl + err) : null,
        errBottom: p.flux_err_mjy ? scaleY(Math.max(0, fl - err)) : null,
      };
    });

    const linePath =
      spectralMode === "synthetic"
        ? points.map((pt, i) => `${i === 0 ? "M" : "L"} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`).join(" ")
        : "";

    return { points, linePath, width, height, minX, maxX, minY, maxY, scaleX, scaleY };
  }, [spectralProfile, spectralMode]);

  return (
    <div className="absolute inset-x-4 top-20 bottom-24 z-25 bg-[#040816]/95 backdrop-blur-xl border border-cyan-950/80 rounded-2xl shadow-2xl p-4 md:p-5 flex flex-col text-slate-200 pointer-events-auto overflow-hidden">
      {/* Top Header & Spectral Mode Controls */}
      <div className="flex flex-wrap items-center justify-between pb-3.5 border-b border-cyan-950/80 gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400 shrink-0" />
            <h2 className="text-base font-bold text-cyan-100 tracking-wide font-sans">
              SPHEREx 102 Spectral Bands Explorer (0.75 – 5.00 µm)
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              R ~ 35 - 130
            </span>
            {spectralMode === "real" ? (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>FLIGHT CALIBRATION (WCS-WAVE)</span>
              </span>
            ) : (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700 flex items-center space-x-1">
                <Sparkles className="w-3 h-3 text-amber-400" />
                <span>SYNTHETIC DEMO BASELINE</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Coordinates: <span className="text-cyan-300 font-mono font-semibold">RA {raDeg.toFixed(4)}°, Dec {decDeg.toFixed(4)}°</span>
            {selectedTarget && (
              <span className="ml-2 text-slate-400">
                | Target: <strong className="text-slate-200">{selectedTarget.name}</strong> ({selectedTarget.spectral_class})
              </span>
            )}
          </p>
        </div>

        {/* Mode Selector & Array Tabs */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Real vs Synthetic Switcher */}
          <div className="flex items-center space-x-1 bg-[#09152e] p-0.5 rounded border border-cyan-900/60 font-mono text-[11px]">
            <button
              onClick={() => setSpectralMode("real")}
              className={`px-2.5 py-1 rounded transition-all flex items-center space-x-1 ${
                spectralMode === "real"
                  ? "bg-cyan-600 text-white font-semibold shadow-[0_0_8px_rgba(6,182,212,0.4)]"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>Authentic Flight SED</span>
            </button>
            <button
              onClick={() => setSpectralMode("synthetic")}
              className={`px-2.5 py-1 rounded transition-all flex items-center space-x-1 ${
                spectralMode === "synthetic"
                  ? "bg-amber-600 text-white font-semibold shadow-[0_0_8px_rgba(245,158,11,0.4)]"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>Synthetic Model</span>
            </button>
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
                onClick={() => {
                  setActiveArrayTab(arrId);
                  // Ensure selectedChannel is within the selected array
                  const minChan = (arrId - 1) * 17 + 1;
                  const maxChan = arrId * 17;
                  if (selectedChannel < minChan || selectedChannel > maxChan) {
                    setSelectedChannel(minChan);
                  }
                }}
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
      </div>

      {/* Main Content Layout: Left Spectrum Graph, Right Band Inspector */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 pt-3 overflow-hidden">
        {/* Interactive Spectral Flux Chart (2 Columns) */}
        <div className="lg:col-span-2 flex flex-col bg-[#060c1d]/90 border border-cyan-950/80 rounded-xl p-3.5 shadow-inner overflow-hidden">
          <div className="flex flex-wrap items-center justify-between font-mono text-xs text-slate-400 mb-1.5 gap-2">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-cyan-200 font-semibold text-[11px]">
                Spectral Energy Distribution (SED) F_λ (MJy/sr) vs Wavelength λ (µm)
              </span>
            </div>
            <div className="text-[11px] flex items-center space-x-2">
              <span className="text-slate-400">
                Coverage:{" "}
                <strong className={validMeasurements.length > 0 ? "text-emerald-400" : "text-amber-300"}>
                  {spectralMode === "synthetic"
                    ? "102 Channels (Simulated)"
                    : validMeasurements.length > 0
                    ? `${validMeasurements.length} of 102 Channels Measured`
                    : "0 Measured in Current Pointing"}
                </strong>
              </span>
              <span className="text-cyan-300">
                Active: Band {activeBand.channel_index} ({activeBand.wavelength_um.toFixed(3)} µm)
              </span>
            </div>
          </div>

          {/* SVG Plot Container */}
          <div className="flex-1 w-full relative flex items-center justify-center min-h-[220px] bg-black/40 rounded border border-cyan-950/60 p-2">
            {isSpectralLoading ? (
              <div className="flex flex-col items-center justify-center space-y-2 text-cyan-300 font-mono text-xs">
                <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
                <span>Evaluating WCS-WAVE calibration across focal plane...</span>
              </div>
            ) : plotData ? (
              <svg
                viewBox={`0 0 ${plotData.width} ${plotData.height}`}
                className="w-full h-full max-h-[300px] select-none"
              >
                {/* Background Wavelength Grid */}
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

                {/* Laboratory Reference Lines (Explicitly labeled as laboratory references) */}
                {[
                  { name: "H2O Ice (Ref)", wl: 3.05, color: "#38bdf8" },
                  { name: "PAH/CH4 (Ref)", wl: 3.3, color: "#a855f7" },
                  { name: "CO2 Ice (Ref)", wl: 4.27, color: "#f43f5e" },
                  { name: "CO Gas/Ice (Ref)", wl: 4.67, color: "#f59e0b" },
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
                        strokeDasharray="2 2"
                        strokeOpacity="0.4"
                      />
                      <text
                        x={x}
                        y={28}
                        textAnchor="middle"
                        fill={feat.color}
                        fontSize="8"
                        fontFamily="monospace"
                        fontWeight="bold"
                        opacity="0.8"
                      >
                        {feat.name}
                      </text>
                    </g>
                  );
                })}

                {/* Synthetic continuous path (only in synthetic mode) */}
                {plotData.linePath && (
                  <path
                    d={plotData.linePath}
                    fill="none"
                    stroke="#06b6d4"
                    strokeWidth="1.8"
                    strokeDasharray={spectralMode === "synthetic" ? "4 2" : "none"}
                  />
                )}

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

                {/* Data Points with Calibrated Error Bars */}
                {plotData.points.map((pt) => {
                  const isSelected = pt.channel_index === selectedChannel;
                  const isReal = pt.provenance_state === "REAL_VERIFIED" || !pt.is_simulated;
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
                          stroke={isReal ? "#34d399" : "#0891b2"}
                          strokeWidth="1.5"
                          opacity="0.8"
                        />
                      )}
                      {/* Top and Bottom error bar caps */}
                      {pt.errTop !== null && (
                        <line
                          x1={pt.x - 3}
                          y1={pt.errTop}
                          x2={pt.x + 3}
                          y2={pt.errTop}
                          stroke={isReal ? "#34d399" : "#0891b2"}
                          strokeWidth="1.5"
                        />
                      )}
                      {pt.errBottom !== null && (
                        <line
                          x1={pt.x - 3}
                          y1={pt.errBottom}
                          x2={pt.x + 3}
                          y2={pt.errBottom}
                          stroke={isReal ? "#34d399" : "#0891b2"}
                          strokeWidth="1.5"
                        />
                      )}
                      {/* Point Circle */}
                      <circle
                        cx={pt.x}
                        cy={pt.y}
                        r={isSelected ? 5.0 : 3.0}
                        fill={isReal ? (isSelected ? "#10b981" : "#34d399") : (isSelected ? "#22d3ee" : "#38bdf8")}
                        stroke="#040816"
                        strokeWidth="1.5"
                      />
                    </g>
                  );
                })}
              </svg>
            ) : (
              /* Informative Scientific Empty State */
              <div className="p-4 text-center space-y-2 max-w-md font-mono text-xs">
                <Compass className="w-8 h-8 text-cyan-400 mx-auto opacity-70" />
                <div className="text-cyan-200 font-bold text-[13px]">
                  Unobserved Pointing In Current Flight Array
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  No Level-2 flight observations currently cover RA {raDeg.toFixed(4)}°, Dec {decDeg.toFixed(4)}° on this array.
                  In SPHEREx, full 102-channel coverage is achieved through progressive all-sky survey scans.
                </p>
                <div className="bg-[#09152e]/80 border border-cyan-900/60 p-2 rounded text-[10px] text-emerald-300">
                  <ShieldCheck className="w-3.5 h-3.5 inline mr-1 text-emerald-400" />
                  <strong>Anti-fabrication Invariant:</strong> Unobserved channels remain explicitly null. Synthetic data is never substituted for missing observations.
                </div>
                <button
                  onClick={() => setSpectralMode("synthetic")}
                  className="px-3 py-1 bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 rounded text-[10px]"
                >
                  View Synthetic Demonstration Baseline
                </button>
              </div>
            )}
          </div>

          {/* Hover Tooltip Readout & Disclaimer */}
          <div className="mt-2 pt-1 border-t border-cyan-950/60 flex flex-wrap items-center justify-between font-mono text-[11px] text-cyan-300 gap-2">
            <div>
              {hoveredPoint ? (
                <span>
                  Band {hoveredPoint.channel_index}: λ = {hoveredPoint.wavelength_um.toFixed(3)} µm | Flux = {hoveredPoint.flux_mjy?.toFixed(4)} MJy/sr (±{hoveredPoint.flux_err_mjy?.toFixed(4)})
                  {hoveredPoint.provenance_state === "REAL_VERIFIED" && (
                    <span className="ml-2 text-emerald-400 font-bold">[REAL FLIGHT FITS]</span>
                  )}
                </span>
              ) : (
                <span className="text-slate-400 text-[10px]">
                  Hover or click any spectral point to inspect calibrated flux, uncertainty, and array specifications.
                </span>
              )}
            </div>
            <div className="text-[9px] text-slate-500 italic">
              * Reference lines indicate laboratory molecular wavelengths.
            </div>
          </div>
        </div>

        {/* Right Active Band Detail Inspector (1 Column) */}
        <div className="flex flex-col bg-[#060c1d]/90 border border-cyan-950/80 rounded-xl p-3.5 space-y-3 font-sans overflow-y-auto">
          {/* Diagnostic Header */}
          <div className="border-b border-cyan-950/80 pb-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-semibold block">
                Band Diagnostic Readout
              </span>
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                Array {activeBand.array_index} (D{activeBand.array_index})
              </span>
            </div>
            <h3 className="text-base font-bold text-cyan-100 font-mono mt-0.5">
              Channel {activeBand.channel_index}: {activeBand.wavelength_um.toFixed(3)} µm
            </h3>
            <span className="text-[10px] font-mono text-slate-400">
              {activeBand.array_name} — Linear Variable Filter (LVF)
            </span>
          </div>

          {/* Instrument Specifications Table */}
          <div className="bg-[#09152e]/70 border border-cyan-950/80 rounded-lg p-2.5 font-mono text-xs space-y-1.5">
            <div className="flex justify-between">
              <span className="text-slate-400">Central Wavelength:</span>
              <span className="text-cyan-300 font-semibold">{activeBand.wavelength_um.toFixed(3)} µm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Bandwidth (Δλ):</span>
              <span className="text-slate-200">{activeBand.bandwidth_um.toFixed(4)} µm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Resolving Power (R):</span>
              <span className="text-amber-300 font-semibold">R ~ {activeBand.resolving_power_r}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Detector ID:</span>
              <span className="text-purple-300">D{activeBand.array_index} ({activeBand.array_index <= 3 ? "SWIR 2.5 µm" : "MWIR 5.3 µm"})</span>
            </div>
            <div className="flex justify-between pt-1 border-t border-cyan-950">
              <span className="text-slate-400">Calibration:</span>
              <span className="text-emerald-400 text-[10px]">WCS-WAVE (HDU 6)</span>
            </div>
          </div>

          {/* Measurement Status Card */}
          <div className="bg-[#09152e]/50 border border-cyan-950 rounded-lg p-2.5 font-mono text-[11px] space-y-1">
            <span className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold block">
              Measurement Status:
            </span>
            {activeMeasurement && activeMeasurement.flux_is_available && activeMeasurement.flux_mjy !== null ? (
              <div className="space-y-1">
                <div className="text-emerald-300 font-bold flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>★ Measured Flight Flux: {activeMeasurement.flux_mjy.toFixed(4)} MJy/sr</span>
                </div>
                <div className="text-slate-400 text-[10px]">
                  Uncertainty (σ): ±{activeMeasurement.flux_err_mjy?.toFixed(4)} MJy/sr (VARIANCE)
                </div>
                <div className="text-cyan-300 text-[9px]">
                  Quality: Clean Source (FLAGS: 0x00200000 BIT_SOURCE)
                </div>
              </div>
            ) : (
              <div className="text-slate-400 text-[10px] space-y-0.5">
                <div className="text-amber-300/90 font-semibold">
                  Unobserved in current single-epoch pointing
                </div>
                <div className="text-slate-500 text-[9px]">
                  This bandpass is carried on Array {activeBand.array_index}. Measurement requires observation visit covering this coordinate on Detector D{activeBand.array_index}.
                </div>
              </div>
            )}
          </div>

          {/* Key Astrophysical Signatures */}
          <div className="space-y-1 text-xs">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-semibold block">
              Astrophysical Bandpass Associations:
            </span>
            <p className="text-slate-300 leading-relaxed text-[10px] bg-[#09152e]/40 p-2 rounded border border-slate-800 font-mono">
              {activeBand.key_features}
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
          <div className="pt-1">
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 mb-1 block font-semibold">
              Select Channel (Array {activeArrayTab}):
            </span>
            <div className="max-h-32 overflow-y-auto grid grid-cols-6 gap-1 font-mono text-[9px]">
              {filteredBands.map((b) => {
                const isSelected = selectedChannel === b.channel_index;
                const isObserved = (spectralProfile || []).some(
                  (p) => p.channel_index === b.channel_index && p.flux_is_available && p.flux_mjy !== null
                );
                return (
                  <button
                    key={b.channel_index}
                    onClick={() => setSelectedChannel(b.channel_index)}
                    className={`py-1 rounded text-center transition-all relative ${
                      isSelected
                        ? "bg-cyan-500 text-slate-950 font-bold shadow-[0_0_8px_rgba(6,182,212,0.4)]"
                        : isObserved
                        ? "bg-emerald-950 text-emerald-300 border border-emerald-600 font-semibold"
                        : "bg-[#09152e] hover:bg-[#0e2149] text-cyan-200/80 border border-cyan-950"
                    }`}
                  >
                    <span>{b.channel_index}</span>
                    {isObserved && (
                      <span className="absolute top-0.5 right-0.5 w-1 h-1 rounded-full bg-emerald-400" />
                    )}
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
