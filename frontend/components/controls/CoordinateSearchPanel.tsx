"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Search,
  Crosshair,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  X,
  ChevronDown,
  ChevronUp,
  Info,
} from "lucide-react";
import {
  parseRA,
  parseDec,
  formatRaHms,
  formatDecDms,
} from "@/utils/coordinates";
import { useSkyStore } from "@/stores/useSkyStore";

export type CoordinateFormat = "decimal" | "sexagesimal";

export interface TargetCoordinates {
  ra: number;
  dec: number;
  format: CoordinateFormat;
  rawRa: string;
  rawDec: string;
  sourceLabel?: string;
}

export interface SearchPreset {
  id: string;
  name: string;
  designation: string;
  raDeg: number;
  decDeg: number;
  raHms: string;
  decDms: string;
}

export const SEARCH_PRESETS: SearchPreset[] = [
  {
    id: "barnards-star",
    name: "Barnard's Star",
    designation: "GJ 699",
    raDeg: 269.452083,
    decDeg: 4.693333,
    raHms: "17h 57m 48.50s",
    decDms: "+04° 41′ 36.00″",
  },
  {
    id: "wise-0855",
    name: "WISE 0855",
    designation: "WISE J085510.83-071442.5",
    raDeg: 133.795129,
    decDeg: -7.245147,
    raHms: "08h 55m 10.831s",
    decDms: "-07° 14′ 42.53″",
  },
  {
    id: "epsilon-indi-b",
    name: "Epsilon Indi B",
    designation: "HD 209100 B",
    raDeg: 331.043792,
    decDeg: -56.782722,
    raHms: "22h 04m 10.51s",
    decDms: "-56° 46′ 57.80″",
  },
  {
    id: "rw-aurigae",
    name: "RW Aurigae",
    designation: "RW Aur",
    raDeg: 76.956417,
    decDeg: 30.401417,
    raHms: "05h 07m 49.54s",
    decDms: "+30° 24′ 05.10″",
  },
  {
    id: "r-draconis",
    name: "R Draconis",
    designation: "R Dra",
    raDeg: 248.167625,
    decDeg: 66.755056,
    raHms: "16h 32m 40.23s",
    decDms: "+66° 45′ 18.20″",
  },
];

export interface CoordinateSearchPanelProps {
  onSearch: (target: TargetCoordinates) => void;
  onClearTarget: () => void;
  onResetCamera: () => void;
  onFovChange: (fov: number) => void;
  activeTarget: TargetCoordinates | null;
  currentFov: number;
  variant?: "dock" | "floating";
}

const FOV_PRESETS = [60, 30, 10, 5, 1, 0.5, 0.1];

export function CoordinateSearchPanel({
  onSearch,
  onClearTarget,
  onResetCamera,
  onFovChange,
  activeTarget,
  currentFov,
  variant = "dock",
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

  // Synchronize input fields when activeTarget changes
  useEffect(() => {
    if (activeTarget) {
      if (format === "sexagesimal") {
        setRaInput(formatRaHms(activeTarget.ra));
        setDecInput(formatDecDms(activeTarget.dec));
      } else {
        setRaInput(activeTarget.ra.toFixed(6));
        setDecInput(activeTarget.dec.toFixed(6));
      }
      setRaError(null);
      setDecError(null);
    }
  }, [activeTarget, format]);

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

  // Unified Preset Application for all 5 NASA Targets
  const applyPreset = (preset: SearchPreset) => {
    const rawRa = format === "sexagesimal" ? preset.raHms : preset.raDeg.toFixed(6);
    const rawDec = format === "sexagesimal" ? preset.decDms : preset.decDeg.toFixed(6);
    setRaInput(rawRa);
    setDecInput(rawDec);
    setRaError(null);
    setDecError(null);

    useSkyStore.getState().selectTarget(preset.id);
    onSearch({
      ra: preset.raDeg,
      dec: preset.decDeg,
      format,
      rawRa,
      rawDec,
      sourceLabel: preset.name,
    });
  };

  const applyWise0855Preset = () => {
    const p = SEARCH_PRESETS.find((t) => t.id === "wise-0855")!;
    applyPreset(p);
  };

  // Custom FOV handler
  const handleCustomFovSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseFloat(customFovInput);
    if (!isNaN(parsed) && parsed >= 0.05 && parsed <= 120) {
      onFovChange(parsed);
    }
  };

  // Format toggle button bar
  const formatSelector = (
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
  );

  // Core coordinate input form
  const coordinateForm = (
    <form onSubmit={handleExecuteSearch} className="space-y-2">
      {/* RA Input */}
      <div>
        <div className="flex justify-between items-center mb-0.5">
          <label className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Right Ascension (RA)
          </label>
          <span className="text-[9px] text-cyan-500 font-mono">
            {format === "decimal" ? "[0° – 360°)" : "[00h – 24h)"}
          </span>
        </div>
        <input
          type="text"
          value={raInput}
          onChange={handleRaChange}
          placeholder={format === "decimal" ? "e.g. 133.795129" : "e.g. 08h 55m 10.831s"}
          className={`w-full px-2.5 py-1 bg-[#02040b] border ${
            raError ? "border-rose-500/80 text-rose-200" : "border-cyan-900/50 text-cyan-100"
          } rounded text-xs font-mono focus:outline-none focus:border-cyan-400 transition-colors placeholder:text-slate-600`}
        />
        {raError && (
          <div className="flex items-center space-x-1 mt-0.5 text-[9px] text-rose-400">
            <AlertCircle className="w-2.5 h-2.5 flex-shrink-0" />
            <span>{raError}</span>
          </div>
        )}
      </div>

      {/* Dec Input */}
      <div>
        <div className="flex justify-between items-center mb-0.5">
          <label className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Declination (Dec)
          </label>
          <span className="text-[9px] text-cyan-500 font-mono">[-90° – +90°]</span>
        </div>
        <input
          type="text"
          value={decInput}
          onChange={handleDecChange}
          placeholder={format === "decimal" ? "e.g. -7.245147" : "e.g. -07° 14′ 42.53″"}
          className={`w-full px-2.5 py-1 bg-[#02040b] border ${
            decError ? "border-rose-500/80 text-rose-200" : "border-cyan-900/50 text-cyan-100"
          } rounded text-xs font-mono focus:outline-none focus:border-cyan-400 transition-colors placeholder:text-slate-600`}
        />
        {decError && (
          <div className="flex items-center space-x-1 mt-0.5 text-[9px] text-rose-400">
            <AlertCircle className="w-2.5 h-2.5 flex-shrink-0" />
            <span>{decError}</span>
          </div>
        )}
      </div>

      {/* Action buttons: Search & Reset */}
      <div className="flex items-center space-x-2 pt-0.5">
        <button
          type="submit"
          className="flex-1 py-1 px-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded text-xs transition-all shadow-[0_0_8px_rgba(6,182,212,0.3)] active:scale-[0.98] flex items-center justify-center space-x-1.5"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Search & Fly</span>
        </button>

        <button
          type="button"
          onClick={onResetCamera}
          title="Reset Camera Orientation"
          className="p-1 px-2.5 bg-[#09152e] hover:bg-cyan-950/80 text-slate-300 hover:text-cyan-300 border border-cyan-900/50 rounded transition-colors flex items-center justify-center space-x-1 text-xs"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>
    </form>
  );

  // Optical FOV controls
  const fovControls = (
    <div className="space-y-1.5">
      <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider flex items-center justify-between">
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
            className={`py-0.5 rounded text-[10px] font-mono font-medium transition-colors border ${
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
            className="w-full py-0.5 text-center bg-[#040817] border border-cyan-950/80 rounded text-[10px] text-cyan-200 focus:outline-none focus:border-cyan-400"
            title="Custom FOV (°)"
            placeholder="FOV°"
          />
        </form>
      </div>
    </div>
  );

  // Target locked card
  const targetCard = activeTarget ? (
    <div className="p-2.5 bg-cyan-950/40 border border-cyan-700/50 rounded-lg space-y-1.5 h-full flex flex-col justify-between">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5 text-cyan-300 font-semibold text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>ACTIVE TARGET LOCKED</span>
          </div>
          <button
            onClick={onClearTarget}
            title="Clear Active Target"
            className="text-slate-400 hover:text-rose-300 transition-colors p-0.5 rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="text-[10px] text-slate-300 space-y-0.5">
          <div>
            <span className="text-slate-500">RA: </span>
            <span className="font-mono text-cyan-200 font-semibold">
              {activeTarget.ra.toFixed(6)}°
            </span>{" "}
            <span className="text-slate-400">({formatRaHms(activeTarget.ra)})</span>
          </div>
          <div>
            <span className="text-slate-500">Dec: </span>
            <span className="font-mono text-cyan-200 font-semibold">
              {activeTarget.dec.toFixed(6)}°
            </span>{" "}
            <span className="text-slate-400">({formatDecDms(activeTarget.dec)})</span>
          </div>
        </div>
      </div>

      {activeTarget.sourceLabel && (
        <div className="text-[9px] text-amber-300/90 italic pt-1 border-t border-cyan-900/40 truncate">
          Source: {activeTarget.sourceLabel}
        </div>
      )}
    </div>
  ) : (
    <div className="p-3 bg-[#080e1c] border border-cyan-950/60 rounded-lg text-slate-400 text-[10px] space-y-1.5 h-full flex flex-col justify-center">
      <div className="flex items-center space-x-1.5 text-cyan-400 font-semibold text-[11px]">
        <Info className="w-3.5 h-3.5 shrink-0" />
        <span>Astrometric Target Guidance</span>
      </div>
      <p className="text-slate-300 leading-relaxed">
        Enter coordinates in either Decimal Degrees (e.g. 133.795129, -7.245147) or standard Sexagesimal notation (e.g. 08h 55m 10.83s, -07° 14′ 42.5″).
      </p>
      <div className="text-[9px] text-slate-500 font-mono">
        Coordinates are automatically synchronized to URL query parameters for reproducible deep-linking.
      </div>
    </div>
  );

  // RENDER DOCK VARIANT (Default)
  if (variant === "dock") {
    return (
      <div className="p-3 font-mono text-xs text-slate-200 select-none">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Column 1: Format Selector & Coordinate Form */}
          <div className="space-y-2 bg-[#080e1c] p-2.5 rounded-lg border border-cyan-950/70">
            {formatSelector}
            {coordinateForm}
          </div>

          {/* Column 2: Optical FOV & Quick Presets */}
          <div className="space-y-3 bg-[#080e1c] p-2.5 rounded-lg border border-cyan-950/70 flex flex-col justify-between">
            {fovControls}

            {/* Navigation Presets: NASA SPHEREx 5 Validation Targets */}
            <div className="pt-2 border-t border-cyan-950/60">
              <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-1 flex items-center justify-between">
                <span>NASA Challenge Validation Presets</span>
                <span className="text-[9px] text-cyan-400 font-mono">5 Targets</span>
              </div>
              <div className="grid grid-cols-2 gap-1">
                {SEARCH_PRESETS.map((p) => {
                  const isSelected = activeTarget && (
                    activeTarget.sourceLabel === p.name ||
                    (Math.abs(activeTarget.ra - p.raDeg) < 0.005 && Math.abs(activeTarget.dec - p.decDeg) < 0.005)
                  );
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => applyPreset(p)}
                      className={`text-left p-1 rounded transition-all text-[10px] font-mono border ${
                        isSelected
                          ? "bg-cyan-950/90 border-cyan-400 text-cyan-200 shadow-[0_0_6px_rgba(6,182,212,0.3)] ring-1 ring-cyan-400/50"
                          : "bg-[#07132a] hover:bg-cyan-950/70 border-cyan-900/60 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-cyan-300 truncate">{p.name}</span>
                      </div>
                      <div className="text-[8px] text-slate-500 truncate">
                        {p.raDeg.toFixed(2)}°, {p.decDeg.toFixed(2)}°
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Column 3: Active Target Status or Guidance */}
          <div className="h-full">
            {targetCard}
          </div>
        </div>
      </div>
    );
  }

  // RENDER FLOATING VARIANT (Original legacy fallback)
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
          {formatSelector}
          {coordinateForm}

          {/* Navigation Presets */}
          <div className="pt-2 border-t border-cyan-950/60">
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
                  PRESET
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                08h 55m 10.831s &bull; -07° 14′ 42.53″
              </div>
            </button>
          </div>

          {/* FOV Controls */}
          <div className="pt-2 border-t border-cyan-950/60">
            {fovControls}
          </div>

          {/* Active Target Locked */}
          {targetCard}
        </div>
      )}
    </div>
  );
}
