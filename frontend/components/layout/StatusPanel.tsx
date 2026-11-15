"use client";

import React from "react";
import { CameraTelemetry } from "@/components/celestial/CameraController";
import { ShieldAlert, Activity, Target } from "lucide-react";

export interface StatusPanelProps {
  telemetry: CameraTelemetry | null;
  starCount?: number;
  targetCoords?: { ra: number; dec: number } | null;
}

/**
 * Scientific Status & Telemetry Panel for Milestone 1 & 2.
 * Reports active rendering engine, synthetic data provenance,
 * demonstration star counts, real-time spherical camera parameters, and target status.
 */
export function StatusPanel({
  telemetry,
  starCount = 4500,
  targetCoords = null,
}: StatusPanelProps) {
  return (
    <div className="p-3 bg-[#050b1a]/90 backdrop-blur-md border border-cyan-950/80 rounded-xl shadow-2xl font-mono text-[11px] text-slate-300 space-y-2 select-none">
      <div className="text-[10px] uppercase tracking-wider text-cyan-400 font-semibold pb-1 border-b border-cyan-950/60 flex items-center justify-between">
        <span className="flex items-center space-x-1">
          <Activity className="w-3.5 h-3.5" />
          <span>System Status & Telemetry</span>
        </span>
        <span className="text-emerald-400 text-[9px] flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>ACTIVE</span>
        </span>
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-400">
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
          <span className="text-slate-200">
            {telemetry ? `${telemetry.distance}` : "45.0"}
          </span>
        </div>
        <div>
          FOV:{" "}
          <span className="text-slate-200">
            {telemetry ? `${telemetry.fov}°` : "60°"}
          </span>
        </div>
        <div>
          Polar (θ):{" "}
          <span className="text-purple-300">
            {telemetry ? `${telemetry.polarDeg}°` : "70.5°"}
          </span>
        </div>
        <div>
          Azimuth (φ):{" "}
          <span className="text-purple-300">
            {telemetry ? `${telemetry.azimuthDeg}°` : "0.0°"}
          </span>
        </div>
      </div>

      {targetCoords && (
        <div className="pt-1.5 border-t border-cyan-950/60 flex items-center justify-between text-[10px]">
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
      <div className="pt-1.5 border-t border-cyan-950/60 flex items-center space-x-1.5 text-[10px] text-amber-300/90 bg-amber-950/20 px-2 py-1 rounded border border-amber-900/40">
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span>Data Source: Synthetic demonstration data (Procedural ICRS)</span>
      </div>
    </div>
  );
}
