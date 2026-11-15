"use client";

import React from "react";
import { useSkyStore } from "@/stores/useSkyStore";
import { AstronomicalTargetDetail } from "@/types/astronomy";
import {
  Compass,
  Clock,
  Activity,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export function ValidationTargetsView() {
  const validationTargets = useSkyStore((s) => s.validationTargets);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const selectTarget = useSkyStore((s) => s.selectTarget);
  const setActiveTab = useSkyStore((s) => s.setActiveTab);

  const handleInspectTarget = async (target: AstronomicalTargetDetail, tab: "sky" | "temporal" | "spectral") => {
    await selectTarget(target);
    setActiveTab(tab);
  };

  return (
    <div className="absolute inset-x-4 top-20 bottom-24 z-25 bg-[#040816]/95 backdrop-blur-xl border border-cyan-950/80 rounded-2xl shadow-2xl p-6 flex flex-col text-slate-200 pointer-events-auto overflow-y-auto">
      {/* View Header */}
      <div className="pb-4 border-b border-cyan-950/80 mb-6">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
          <h2 className="text-lg font-bold text-cyan-100 tracking-wide font-sans">
            NASA SPHEREx 5-Target Scientific Validation Suite
          </h2>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
            5 / 5 Targets Calibrated
          </span>
        </div>
        <p className="text-xs text-slate-400 font-sans mt-1">
          Validated against verified coordinates, multi-epoch observations, astrometric proper motion, and physical infrared SED profiles across 0.75 – 5.00 µm.
        </p>
      </div>

      {/* Target Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {validationTargets.map((target) => {
          const isSelected = selectedTarget?.id === target.id;

          return (
            <div
              key={target.id}
              className={`bg-[#060c1d]/90 border rounded-xl p-4 flex flex-col justify-between space-y-3 transition-all ${
                isSelected
                  ? "border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)] ring-1 ring-cyan-400/40"
                  : "border-cyan-950/80 hover:border-cyan-800"
              }`}
            >
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-base font-bold text-cyan-100">
                      {target.name}
                    </h3>
                    <div className="text-[11px] font-mono text-cyan-400">
                      {target.designation}
                    </div>
                  </div>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                    {target.spectral_class}
                  </span>
                </div>

                <div className="mt-1.5 inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-900/40">
                  {target.target_type}
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mt-2.5 line-clamp-3">
                  {target.description}
                </p>

                {/* Astrometry Summary */}
                <div className="bg-[#09152e]/70 border border-cyan-950/70 rounded p-2.5 font-mono text-[11px] space-y-1 mt-3">
                  <div className="flex justify-between">
                    <span className="text-slate-400">RA (HMS):</span>
                    <span className="text-cyan-300">{target.ra_hms}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Dec (DMS):</span>
                    <span className="text-cyan-300">{target.dec_dms}</span>
                  </div>
                  {target.proper_motion_ra_mas_yr !== undefined && (
                    <div className="flex justify-between text-[10px]">
                      <span className="text-slate-400">Proper Motion:</span>
                      <span className="text-amber-300">
                        ({target.proper_motion_ra_mas_yr}, {target.proper_motion_dec_mas_yr}) mas/yr
                      </span>
                    </div>
                  )}
                </div>

                {/* Mission Validation Role */}
                <div className="mt-2 text-[11px] bg-[#09152e]/40 p-2 rounded border border-slate-800/80">
                  <span className="text-[10px] font-mono uppercase text-cyan-400 font-semibold block">
                    Validation Role:
                  </span>
                  <span className="text-slate-300 text-[10px] leading-tight block">
                    {target.test_validation_role}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 border-t border-cyan-950/60 flex items-center space-x-2 font-mono text-[11px]">
                <button
                  onClick={() => handleInspectTarget(target, "sky")}
                  className="flex-1 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold py-1.5 px-2 rounded flex items-center justify-center space-x-1 transition-colors"
                >
                  <Compass className="w-3.5 h-3.5" />
                  <span>3D Sky</span>
                </button>
                <button
                  onClick={() => handleInspectTarget(target, "temporal")}
                  className="bg-[#09152e] hover:bg-[#0e2149] text-cyan-300 border border-cyan-900/60 py-1.5 px-2 rounded flex items-center space-x-1 transition-colors"
                  title="Temporal Timeline"
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>Epochs</span>
                </button>
                <button
                  onClick={() => handleInspectTarget(target, "spectral")}
                  className="bg-[#09152e] hover:bg-[#0e2149] text-purple-300 border border-purple-900/60 py-1.5 px-2 rounded flex items-center space-x-1 transition-colors"
                  title="102-Band Spectrum"
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>SED</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
