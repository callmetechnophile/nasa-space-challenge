"use client";

import React from "react";
import { CameraTelemetry } from "@/components/celestial/CameraController";
import { ShieldAlert, Activity, Target, CheckCircle2, X } from "lucide-react";
import { ProvenanceState } from "@/types/astronomy";

export interface StatusPanelProps {
  telemetry: CameraTelemetry | null;
  starCount?: number;
  targetCoords?: { ra: number; dec: number } | null;
  provenanceState?: ProvenanceState;
  className?: string;
  onClose?: () => void;
}

/**
 * Scientific Status & Telemetry Panel.
 * Reports active rendering engine, synthetic data provenance,
 * demonstration star counts, real-time spherical camera parameters, and target status.
 */
export function StatusPanel({
  telemetry,
  starCount = 4500,
  targetCoords = null,
  provenanceState = "SYNTHETIC_DEMO",
  className = "",
  onClose,
}: StatusPanelProps) {
  return (
    <div
      className={`p-3.5 bg-[#090d16]/95 backdrop-blur-md border border-cyan-900/60 rounded-xl shadow-2xl font-mono text-[11px] text-slate-300 space-y-2.5 select-none ${className}`}
    >
      <div className="text-[10px] uppercase tracking-wider text-cyan-400 font-semibold pb-1.5 border-b border-cyan-950/60 flex items-center justify-between">
        <span className="flex items-center space-x-1.5">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span>SYSTEM STATUS & TELEMETRY</span>
        </span>
        <div className="flex items-center space-x-2">
          <span className="text-emerald-400 text-[9px] font-semibold flex items-center space-x-1 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/40">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>ACTIVE</span>
          </span>
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-0.5 rounded hover:bg-slate-800/60 transition-colors"
              title="Close status panel"
              aria-label="Close status panel"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-slate-400">
        <div>
          Engine:{" "}
          <span className="text-cyan-300 font-semibold">Three.js (WebGL)</span>
        </div>
        <div>
          Demo Stars:{" "}
          <span className="text-cyan-300 font-semibold">{starCount.toLocaleString()}</span>
        </div>
        <div>
          Distance:{" "}
          <span className="text-slate-200 font-medium">
            {telemetry ? `${telemetry.distance}` : "16.2"}
          </span>
        </div>
        <div>
          FOV:{" "}
          <span className="text-slate-200 font-medium">
            {telemetry ? `${telemetry.fov}°` : "60°"}
          </span>
        </div>
        <div>
          Polar (θ):{" "}
          <span className="text-purple-300 font-medium">
            {telemetry ? `${telemetry.polarDeg}°` : "0.6°"}
          </span>
        </div>
        <div>
          Azimuth (φ):{" "}
          <span className="text-purple-300 font-medium">
            {telemetry ? `${telemetry.azimuthDeg}°` : "-69.3°"}
          </span>
        </div>
      </div>

      {targetCoords && (
        <div className="pt-2 border-t border-cyan-950/60 flex items-center justify-between text-[10px]">
          <span className="text-cyan-400 font-semibold flex items-center space-x-1">
            <Target className="w-3 h-3 text-cyan-400" />
            <span>Target:</span>
          </span>
          <span className="font-mono text-cyan-200">
            α {targetCoords.ra.toFixed(4)}°, δ {targetCoords.dec.toFixed(4)}°
          </span>
        </div>
      )}

      {/* Provenance Badge */}
      {provenanceState === "REAL_VERIFIED" ? (
        <div className="pt-2 border-t border-cyan-950/60 flex items-center space-x-1.5 text-[10px] text-emerald-300/90 bg-emerald-950/30 px-2 py-1 rounded border border-emerald-800/50">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <span>Data Source: REAL_VERIFIED (NASA SPHEREx Level-2)</span>
        </div>
      ) : (
        <div className="pt-2 border-t border-cyan-950/60 flex items-center space-x-1.5 text-[10px] text-amber-300/90 bg-amber-950/20 px-2 py-1.5 rounded border border-amber-900/40">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>Data Source: Synthetic demonstration data (Procedural ICRS)</span>
        </div>
      )}
    </div>
  );
}
