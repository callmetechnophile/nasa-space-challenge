"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Search,
  Crosshair,
  RotateCcw,
  Compass,
  AlertCircle,
  CheckCircle2,
  X,
  ChevronDown,
  ChevronUp,
  Maximize2,
} from "lucide-react";
import {
  parseRA,
  parseDec,
  formatRaHms,
  formatDecDms,
  raToDegrees,
  decToDegrees,
} from "@/utils/coordinates";

export type CoordinateFormat = "decimal" | "sexagesimal";

export interface TargetCoordinates {
  ra: number;
  dec: number;
  format: CoordinateFormat;
  rawRa: string;
  rawDec: string;
  sourceLabel?: string;
}

export interface CoordinateSearchPanelProps {
  onSearch: (target: TargetCoordinates) => void;
  onClearTarget: () => void;
  onResetCamera: () => void;
  onFovChange: (fov: number) => void;
  activeTarget: TargetCoordinates | null;
  currentFov: number;
}

const FOV_PRESETS = [60, 30, 10, 5, 1, 0.5, 0.1];

export function CoordinateSearchPanel({
  onSearch,
  onClearTarget,
  onResetCamera,
  onFovChange,
  activeTarget,
  currentFov,
}: CoordinateSearchPanelProps) {
  const [format, setFormat] = useState<CoordinateFormat>("decimal");
  const [raInput, setRaInput] = useState<string>("0.000000");
  const [decInput, setDecInput] = useState<string>("0.000000");
  const [raError, setRaError] = useState<string | null>(null);
  const [decError, setDecError] = useState<string | null>(null);
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [customFovInput, setCustomFovInput] = useState<string>(currentFov.toString());

  // Keep custom FOV input synced with currentFov
  useEffect(() => {
    setCustomFovInput(currentFov.toString());
  }, [currentFov]);

  // When format switches, convert current valid values between formats
  const handleFormatChange = (newFormat: CoordinateFormat) => {
    if (newFormat === format) return;

    if (!raError && !decError) {
      try {
        const raRes = parseRA(raInput);
        const decRes = parseDec(decInput);

        if (newFormat === "sexagesimal") {
          setRaInput(raRes.formatted);
          setDecInput(decRes.formatted);
        } else {
          setRaInput(raRes.degrees.toFixed(6));
          setDecInput(decRes.degrees.toFixed(6));
        }
      } catch {
        // Keep existing strings if parsing fails
      }
    }
    setFormat(newFormat);
    setRaError(null);
    setDecError(null);
  };

  // Real-time RA validation
  const validateRA = useCallback((val: string): number | null => {
    if (!val.trim()) {
      setRaError("RA coordinate is required");
      return null;
    }
    try {
      const res = parseRA(val);
      if (res.degrees < 0 || res.degrees >= 360) {
        setRaError("RA must be in range [0, 360) degrees");
        return null;
      }
      setRaError(null);
      return res.degrees;
    } catch (err: any) {
      setRaError(err?.message || "Invalid Right Ascension coordinate");
      return null;
    }
  }, []);

  // Real-time Dec validation
  const validateDec = useCallback((val: string): number | null => {
    if (!val.trim()) {
      setDecError("Dec coordinate is required");
      return null;
    }
    try {
      const res = parseDec(val);
      if (res.degrees < -90 || res.degrees > 90) {
        setDecError("Declination must be in range [-90, +90] degrees");
        return null;
      }
      setDecError(null);
      return res.degrees;
    } catch (err: any) {
      setDecError(err?.message || "Invalid Declination coordinate");
      return null;
    }
  }, []);

  const handleRaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setRaInput(val);
    validateRA(val);
  };

  const handleDecChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setDecInput(val);
    validateDec(val);
  };

  const handleExecuteSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const raDeg = validateRA(raInput);
    const decDeg = validateDec(decInput);

    if (raDeg === null || decDeg === null) return;

    onSearch({
      ra: raDeg,
      dec: decDeg,
      format,
      rawRa: raInput,
      rawDec: decInput,
      sourceLabel: "COORDINATE SEARCH",
    });
  };

  // Preset: WISE 0855 test target
  const applyWise0855Preset = () => {
    if (format === "sexagesimal") {
      setRaInput("08h 55m 10.831s");
      setDecInput("-07° 14′ 42.53″");
    } else {
      setRaInput("133.795129");
      setDecInput("-7.245147");
    }
    setRaError(null);
    setDecError(null);

    onSearch({
      ra: 133.795129,
      dec: -7.245147,
      format,
      rawRa: format === "sexagesimal" ? "08h 55m 10.831s" : "133.795129",
      rawDec: format === "sexagesimal" ? "-07° 14′ 42.53″" : "-7.245147",
      sourceLabel: "COORDINATE NAVIGATION TEST — WISE 0855",
    });
  };

  // Custom FOV handler
  const handleCustomFovSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseFloat(customFovInput);
    if (!isNaN(parsed) && parsed >= 0.05 && parsed <= 120) {
      onFovChange(parsed);
    }
  };

  return (
    <div className="bg-[#050b1a]/95 backdrop-blur-md border border-cyan-950/80 rounded-xl shadow-2xl font-mono text-xs text-slate-200 select-none overflow-hidden transition-all duration-300">
      {/* Header bar */}
      <div className="px-3 py-2 bg-[#071026] border-b border-cyan-950/70 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Crosshair className="w-4 h-4 text-cyan-400" />
          <span className="font-semibold text-cyan-200 tracking-wide">
            Coordinate Navigation
          </span>
          <span className="text-[10px] bg-cyan-950/80 text-cyan-400 border border-cyan-800/50 px-1.5 py-0.2 rounded font-bold">
            M2
          </span>
        </div>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-slate-400 hover:text-cyan-300 transition-colors p-1"
          title={isCollapsed ? "Expand Panel" : "Collapse Panel"}
        >
          {isCollapsed ? (
            <ChevronDown className="w-3.5 h-3.5" />
          ) : (
            <ChevronUp className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {!isCollapsed && (
        <div className="p-3 space-y-3">
          {/* Format selector */}
          <div className="flex items-center space-x-1 p-0.5 bg-[#02050f] rounded-lg border border-cyan-950/60">
            <button
              type="button"
              onClick={() => handleFormatChange("decimal")}
              className={`flex-1 py-1 text-center rounded text-[11px] font-medium transition-colors ${
                format === "decimal"
                  ? "bg-cyan-950 text-cyan-300 border border-cyan-700/60 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Decimal Degrees
            </button>
            <button
              type="button"
              onClick={() => handleFormatChange("sexagesimal")}
              className={`flex-1 py-1 text-center rounded text-[11px] font-medium transition-colors ${
                format === "sexagesimal"
                  ? "bg-cyan-950 text-cyan-300 border border-cyan-700/60 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sexagesimal (HMS/DMS)
            </button>
          </div>

          {/* Coordinate Form */}
          <form onSubmit={handleExecuteSearch} className="space-y-2.5">
            {/* RA Input */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                  Right Ascension (RA)
                </label>
                <span className="text-[10px] text-cyan-500">
                  {format === "decimal" ? "[0° – 360°)" : "[00h – 24h)"}
                </span>
              </div>
              <div className="relative">
                <input
                  type="text"
                  value={raInput}
                  onChange={handleRaChange}
                  placeholder={
                    format === "decimal" ? "e.g. 133.795129" : "e.g. 08h 55m 10.831s"
                  }
                  className={`w-full px-2.5 py-1.5 bg-[#02040b] border ${
                    raError ? "border-rose-500/80 text-rose-200" : "border-cyan-900/50 text-cyan-100"
                  } rounded-lg text-xs font-mono focus:outline-none focus:border-cyan-400 transition-colors placeholder:text-slate-600`}
                />
              </div>
              {raError && (
                <div className="flex items-center space-x-1 mt-1 text-[10px] text-rose-400">
                  <AlertCircle className="w-3 h-3 flex-shrink-0" />
                  <span>{raError}</span>
                </div>
              )}
            </div>

            {/* Dec Input */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                  Declination (Dec)
                </label>
                <span className="text-[10px] text-cyan-500">[-90° – +90°]</span>
              </div>
              <div className="relative">
                <input
                  type="text"
                  value={decInput}
                  onChange={handleDecChange}
                  placeholder={
                    format === "decimal" ? "e.g. -7.245147" : "e.g. -07° 14′ 42.53″"
                  }
                  className={`w-full px-2.5 py-1.5 bg-[#02040b] border ${
                    decError ? "border-rose-500/80 text-rose-200" : "border-cyan-900/50 text-cyan-100"
                  } rounded-lg text-xs font-mono focus:outline-none focus:border-cyan-400 transition-colors placeholder:text-slate-600`}
                />
              </div>
              {decError && (
                <div className="flex items-center space-x-1 mt-1 text-[10px] text-rose-400">
                  <AlertCircle className="w-3 h-3 flex-shrink-0" />
                  <span>{decError}</span>
                </div>
              )}
            </div>

            {/* Action buttons: Search & Reset */}
            <div className="flex items-center space-x-2 pt-1">
              <button
                type="submit"
                className="flex-1 py-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded-lg shadow-[0_0_12px_rgba(6,182,212,0.3)] transition-all flex items-center justify-center space-x-1.5 text-xs active:scale-[0.98]"
              >
                <Search className="w-3.5 h-3.5" />
                <span>Search & Fly</span>
              </button>

              <button
                type="button"
                onClick={onResetCamera}
                title="Reset Camera Orientation"
                className="p-1.5 bg-[#09152e] hover:bg-cyan-950/80 text-slate-300 hover:text-cyan-300 border border-cyan-900/50 rounded-lg transition-colors flex items-center justify-center"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>

          {/* Test Targets & Preset */}
          <div className="pt-2 border-t border-cyan-950/60">
            <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-1.5 flex items-center justify-between">
              <span>Navigation Test Presets</span>
            </div>
            <button
              type="button"
              onClick={applyWise0855Preset}
              className="w-full text-left p-1.5 bg-[#07132a] hover:bg-cyan-950/70 border border-cyan-800/40 rounded-lg transition-colors text-[11px] group"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-cyan-300 group-hover:text-cyan-200">
                  WISE 0855 Test Target
                </span>
                <span className="text-[9px] text-amber-400 bg-amber-950/70 border border-amber-800/60 px-1 py-0.2 rounded">
                  M2 PRESET
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                08h 55m 10.831s &bull; -07° 14′ 42.53″
              </div>
            </button>
          </div>

          {/* Optical Field of View (FOV) Controls */}
          <div className="pt-2 border-t border-cyan-950/60">
            <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-1.5 flex items-center justify-between">
              <span>Optical Field of View</span>
              <span className="text-cyan-400 font-bold">{currentFov}°</span>
            </div>

            {/* Quick preset pills */}
            <div className="grid grid-cols-4 gap-1">
              {FOV_PRESETS.map((fov) => (
                <button
                  key={fov}
                  type="button"
                  onClick={() => onFovChange(fov)}
                  className={`py-1 rounded text-[10px] font-mono font-medium transition-colors border ${
                    Math.abs(currentFov - fov) < 0.01
                      ? "bg-cyan-600/30 border-cyan-400 text-cyan-200 font-bold shadow-[0_0_8px_rgba(6,182,212,0.2)]"
                      : "bg-[#040817] border-cyan-950/80 text-slate-400 hover:text-cyan-300 hover:border-cyan-800/60"
                  }`}
                >
                  {fov}°
                </button>
              ))}

              {/* Custom FOV Mini Input */}
              <form onSubmit={handleCustomFovSubmit} className="col-span-1">
                <input
                  type="number"
                  step="any"
                  min="0.05"
                  max="120"
                  value={customFovInput}
                  onChange={(e) => setCustomFovInput(e.target.value)}
                  onBlur={handleCustomFovSubmit}
                  className="w-full py-1 text-center bg-[#040817] border border-cyan-950/80 rounded text-[10px] text-cyan-200 focus:outline-none focus:border-cyan-400"
                  title="Custom FOV (°)"
                />
              </form>
            </div>
          </div>

          {/* Active Target Locked Card */}
          {activeTarget && (
            <div className="p-2 bg-cyan-950/40 border border-cyan-700/50 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1 text-cyan-300 font-semibold text-[11px]">
                  <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                  <span>TARGET LOCKED</span>
                </div>
                <button
                  onClick={onClearTarget}
                  title="Clear Active Target"
                  className="text-slate-400 hover:text-rose-300 transition-colors p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>

              <div className="text-[10px] text-slate-300 space-y-0.5">
                <div>
                  <span className="text-slate-500">RA: </span>
                  <span className="font-mono text-cyan-200">
                    {activeTarget.ra.toFixed(6)}°
                  </span>{" "}
                  <span className="text-slate-400">
                    ({formatRaHms(activeTarget.ra)})
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Dec: </span>
                  <span className="font-mono text-cyan-200">
                    {activeTarget.dec.toFixed(6)}°
                  </span>{" "}
                  <span className="text-slate-400">
                    ({formatDecDms(activeTarget.dec)})
                  </span>
                </div>
              </div>

              {activeTarget.sourceLabel && (
                <div className="text-[9px] text-amber-300/80 italic pt-0.5 border-t border-cyan-900/40">
                  {activeTarget.sourceLabel}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
