"use client";

import React from "react";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Grid,
  Sparkles,
  Tag,
} from "lucide-react";

export interface ViewControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
  showGrid: boolean;
  onToggleGrid: () => void;
  showStars: boolean;
  onToggleStars: () => void;
  showLabels: boolean;
  onToggleLabels: () => void;
}

/**
 * Compact View Controls HUD for Milestone 1.
 * Provides direct, responsive controls for camera manipulation and layer toggles.
 */
export function ViewControls({
  onZoomIn,
  onZoomOut,
  onResetView,
  showGrid,
  onToggleGrid,
  showStars,
  onToggleStars,
  showLabels,
  onToggleLabels,
}: ViewControlsProps) {
  return (
    <div className="flex flex-col space-y-1.5 p-2 bg-[#050b1a]/90 backdrop-blur-md border border-cyan-950/80 rounded-xl shadow-2xl font-mono text-xs text-slate-200 select-none">
      <div className="text-[10px] uppercase tracking-wider text-cyan-400 font-semibold px-1 pb-1 border-b border-cyan-950/60 flex items-center justify-between">
        <span>Controls</span>
        <span className="text-[9px] text-slate-500">M1</span>
      </div>

      {/* Camera Action Buttons */}
      <div className="flex items-center space-x-1">
        <button
          onClick={onZoomIn}
          title="Zoom In (Closer View)"
          className="p-2 bg-[#09152e] hover:bg-cyan-950/80 text-cyan-300 border border-cyan-900/50 rounded-lg transition-colors flex items-center justify-center"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={onZoomOut}
          title="Zoom Out (Wider View)"
          className="p-2 bg-[#09152e] hover:bg-cyan-950/80 text-cyan-300 border border-cyan-900/50 rounded-lg transition-colors flex items-center justify-center"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={onResetView}
          title="Reset Camera Orientation & Distance"
          className="flex-1 py-1.5 px-2 bg-[#09152e] hover:bg-[#0e2149] text-cyan-300 border border-cyan-900/50 rounded-lg transition-colors flex items-center justify-center space-x-1 text-[11px]"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset View</span>
        </button>
      </div>

      {/* Layer Toggles */}
      <div className="space-y-1 pt-1 border-t border-cyan-950/60 text-[11px]">
        {/* Star Field Toggle */}
        <button
          onClick={onToggleStars}
          className={`w-full py-1.5 px-2 rounded-lg flex items-center justify-between border transition-all ${
            showStars
              ? "bg-cyan-950/70 border-cyan-500/50 text-cyan-200"
              : "bg-[#09152e]/50 border-cyan-950/60 text-slate-500 hover:text-slate-300"
          }`}
        >
          <span className="flex items-center space-x-1.5">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>Demonstration Stars</span>
          </span>
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              showStars ? "bg-cyan-400" : "bg-slate-600"
            }`}
          />
        </button>

        {/* Celestial Grid Toggle */}
        <button
          onClick={onToggleGrid}
          className={`w-full py-1.5 px-2 rounded-lg flex items-center justify-between border transition-all ${
            showGrid
              ? "bg-cyan-950/70 border-cyan-500/50 text-cyan-200"
              : "bg-[#09152e]/50 border-cyan-950/60 text-slate-500 hover:text-slate-300"
          }`}
        >
          <span className="flex items-center space-x-1.5">
            <Grid className="w-3 h-3 text-cyan-400" />
            <span>Coordinate Grid</span>
          </span>
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              showGrid ? "bg-cyan-400" : "bg-slate-600"
            }`}
          />
        </button>

        {/* Coordinate Labels Toggle */}
        <button
          onClick={onToggleLabels}
          disabled={!showGrid}
          className={`w-full py-1.5 px-2 rounded-lg flex items-center justify-between border transition-all ${
            showGrid && showLabels
              ? "bg-cyan-950/70 border-cyan-500/50 text-cyan-200"
              : "bg-[#09152e]/50 border-cyan-950/60 text-slate-500 hover:text-slate-300 disabled:opacity-40"
          }`}
        >
          <span className="flex items-center space-x-1.5">
            <Tag className="w-3 h-3 text-cyan-400" />
            <span>Grid Labels & Poles</span>
          </span>
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              showGrid && showLabels ? "bg-cyan-400" : "bg-slate-600"
            }`}
          />
        </button>
      </div>
    </div>
  );
}
