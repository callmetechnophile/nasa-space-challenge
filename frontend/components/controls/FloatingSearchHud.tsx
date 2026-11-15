"use client";

import React, { useState } from "react";
import { useSkyStore } from "@/stores/useSkyStore";
import {
  Search,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Crosshair,
  Layers,
  ChevronDown,
  Globe,
  Star,
  Eye,
  Sliders,
} from "lucide-react";

export function FloatingSearchHud() {
  const raDeg = useSkyStore((s) => s.raDeg);
  const decDeg = useSkyStore((s) => s.decDeg);
  const raHms = useSkyStore((s) => s.raHms);
  const decDms = useSkyStore((s) => s.decDms);
  const galacticL = useSkyStore((s) => s.galacticL);
  const galacticB = useSkyStore((s) => s.galacticB);
  const fovDeg = useSkyStore((s) => s.fovDeg);
  const validationTargets = useSkyStore((s) => s.validationTargets);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const selectTarget = useSkyStore((s) => s.selectTarget);
  const setCoordinateStrings = useSkyStore((s) => s.setCoordinateStrings);
  const setCoordinates = useSkyStore((s) => s.setCoordinates);
  const resetCamera = useSkyStore((s) => s.resetCamera);

  const showGrid = useSkyStore((s) => s.showGrid);
  const showConstellations = useSkyStore((s) => s.showConstellations);
  const showGalacticPlane = useSkyStore((s) => s.showGalacticPlane);
  const showEcliptic = useSkyStore((s) => s.showEcliptic);
  const showCutoutOverlay = useSkyStore((s) => s.showCutoutOverlay);
  const toggleLayer = useSkyStore((s) => s.toggleLayer);

  // Search input state
  const [raInput, setRaInput] = useState(raHms);
  const [decInput, setDecInput] = useState(decDms);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [layersOpen, setLayersOpen] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!raInput || !decInput) return;
    setIsSearching(true);
    setSearchError(null);
    try {
      await setCoordinateStrings(raInput, decInput);
    } catch (err: any) {
      setSearchError(err?.message || "Invalid coordinates format");
    } finally {
      setIsSearching(false);
    }
  };

  const handleZoom = (delta: number) => {
    const newFov = Math.max(0.05, Math.min(60.0, fovDeg * delta));
    setCoordinates(raDeg, decDeg, newFov);
  };

  return (
    <div className="absolute top-4 left-4 z-20 flex flex-col space-y-2 pointer-events-auto">
      {/* Search Bar & Target Selector */}
      <div className="bg-[#050b1a]/90 backdrop-blur-md border border-cyan-950/80 rounded-xl p-3 shadow-2xl w-[380px] text-slate-200">
        <form onSubmit={handleSearch} className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase tracking-wider text-cyan-400 font-semibold flex items-center space-x-1">
              <Crosshair className="w-3.5 h-3.5" />
              <span>Celestial Search</span>
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              Deg or Sexagesimal
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[10px] font-mono text-slate-400 mb-0.5">
                Right Ascension (RA)
              </label>
              <input
                type="text"
                value={raInput}
                onChange={(e) => setRaInput(e.target.value)}
                placeholder="08h 55m 10.83s"
                className="w-full bg-[#0a1329] border border-cyan-900/60 rounded px-2.5 py-1 text-xs font-mono text-cyan-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400"
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono text-slate-400 mb-0.5">
                Declination (Dec)
              </label>
              <input
                type="text"
                value={decInput}
                onChange={(e) => setDecInput(e.target.value)}
                placeholder="-07° 14' 42.50&quot;"
                className="w-full bg-[#0a1329] border border-cyan-900/60 rounded px-2.5 py-1 text-xs font-mono text-cyan-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          {searchError && (
            <div className="text-[11px] font-mono text-rose-400 bg-rose-950/30 px-2 py-1 rounded border border-rose-900/40">
              {searchError}
            </div>
          )}

          <div className="flex items-center space-x-2 pt-0.5">
            <button
              type="submit"
              disabled={isSearching}
              className="flex-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-semibold text-xs py-1.5 px-3 rounded flex items-center justify-center space-x-1.5 transition-colors shadow-[0_0_12px_rgba(6,182,212,0.3)]"
            >
              <Search className="w-3.5 h-3.5" />
              <span>{isSearching ? "Searching..." : "Navigate to Sky Position"}</span>
            </button>

            <button
              type="button"
              onClick={resetCamera}
              title="Reset Celestial Camera"
              className="p-1.5 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/60 rounded text-slate-300 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </form>

        {/* Quick NASA Validation Targets */}
        <div className="mt-3 pt-2.5 border-t border-cyan-950/60">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1.5 flex items-center justify-between">
            <span>NASA Test Targets:</span>
            <span className="text-[9px] text-cyan-500/80">Click to Fly</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {validationTargets.map((target) => {
              const isSelected = selectedTarget?.id === target.id;
              return (
                <button
                  key={target.id}
                  onClick={() => {
                    selectTarget(target);
                    setRaInput(target.ra_hms);
                    setDecInput(target.dec_dms);
                  }}
                  className={`px-2 py-1 rounded text-[11px] font-mono transition-all ${
                    isSelected
                      ? "bg-cyan-500 text-slate-950 font-semibold shadow-[0_0_8px_rgba(6,182,212,0.4)]"
                      : "bg-[#09152e] hover:bg-[#0e2149] text-cyan-200/90 border border-cyan-900/40"
                  }`}
                >
                  {target.name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Real-time Telemetry HUD Card */}
      <div className="bg-[#050b1a]/90 backdrop-blur-md border border-cyan-950/80 rounded-xl p-3 shadow-xl w-[380px] font-mono text-[11px] text-slate-300">
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-400">
          <div>
            RA (deg):{" "}
            <span className="text-cyan-300 font-semibold">
              {raDeg.toFixed(4)}°
            </span>
          </div>
          <div>
            Dec (deg):{" "}
            <span className="text-cyan-300 font-semibold">
              {decDeg.toFixed(4)}°
            </span>
          </div>
          <div>
            RA (HMS): <span className="text-slate-200">{raHms}</span>
          </div>
          <div>
            Dec (DMS): <span className="text-slate-200">{decDms}</span>
          </div>
          <div>
            Galactic (l, b):{" "}
            <span className="text-purple-300">
              {galacticL.toFixed(1)}°, {galacticB.toFixed(1)}°
            </span>
          </div>
          <div>
            FoV:{" "}
            <span className="text-amber-300">
              {fovDeg < 1.0 ? `${(fovDeg * 60).toFixed(1)}'` : `${fovDeg.toFixed(2)}°`}
            </span>
          </div>
        </div>

        {/* Camera and Layer Shortcuts Toolbar */}
        <div className="mt-2.5 pt-2 border-t border-cyan-950/60 flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => handleZoom(0.6)}
              className="p-1.5 bg-[#09152e] hover:bg-cyan-950/80 text-cyan-300 border border-cyan-900/40 rounded transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => handleZoom(1.6)}
              className="p-1.5 bg-[#09152e] hover:bg-cyan-950/80 text-cyan-300 border border-cyan-900/40 rounded transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Layers Toggle Popover Button */}
          <div className="relative">
            <button
              onClick={() => setLayersOpen(!layersOpen)}
              className="px-2 py-1 bg-[#09152e] hover:bg-[#0e2149] text-cyan-300 border border-cyan-900/40 rounded flex items-center space-x-1 text-[11px]"
            >
              <Layers className="w-3 h-3" />
              <span>Layers</span>
              <ChevronDown className="w-3 h-3" />
            </button>

            {layersOpen && (
              <div className="absolute left-0 mt-1 w-48 bg-[#050b1a] border border-cyan-900/80 rounded-lg p-2 shadow-2xl space-y-1.5 text-[11px] z-30">
                <label className="flex items-center justify-between cursor-pointer hover:text-cyan-200">
                  <span>Coordinate Grid</span>
                  <input
                    type="checkbox"
                    checked={showGrid}
                    onChange={() => toggleLayer("showGrid")}
                    className="accent-cyan-500"
                  />
                </label>
                <label className="flex items-center justify-between cursor-pointer hover:text-cyan-200">
                  <span>Constellations</span>
                  <input
                    type="checkbox"
                    checked={showConstellations}
                    onChange={() => toggleLayer("showConstellations")}
                    className="accent-cyan-500"
                  />
                </label>
                <label className="flex items-center justify-between cursor-pointer hover:text-cyan-200">
                  <span>Galactic Plane</span>
                  <input
                    type="checkbox"
                    checked={showGalacticPlane}
                    onChange={() => toggleLayer("showGalacticPlane")}
                    className="accent-cyan-500"
                  />
                </label>
                <label className="flex items-center justify-between cursor-pointer hover:text-cyan-200">
                  <span>Ecliptic Plane</span>
                  <input
                    type="checkbox"
                    checked={showEcliptic}
                    onChange={() => toggleLayer("showEcliptic")}
                    className="accent-cyan-500"
                  />
                </label>
                <label className="flex items-center justify-between cursor-pointer hover:text-cyan-200">
                  <span>Cutout Projection</span>
                  <input
                    type="checkbox"
                    checked={showCutoutOverlay}
                    onChange={() => toggleLayer("showCutoutOverlay")}
                    className="accent-cyan-500"
                  />
                </label>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
