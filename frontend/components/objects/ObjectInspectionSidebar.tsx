"use client";

import React from "react";
import { useSkyStore } from "@/stores/useSkyStore";
import {
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Database,
  Calendar,
  ExternalLink,
  ShieldCheck,
  Compass,
} from "lucide-react";

export function ObjectInspectionSidebar() {
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const sidebarCollapsed = useSkyStore((s) => s.sidebarCollapsed);
  const setSidebarCollapsed = useSkyStore((s) => s.setSidebarCollapsed);
  const selectedEpoch = useSkyStore((s) => s.selectedEpoch);
  const setSelectedEpochIndex = useSkyStore((s) => s.setSelectedEpochIndex);
  const epochIndex = useSkyStore((s) => s.epochIndex);

  if (sidebarCollapsed) {
    return (
      <div className="absolute top-4 right-4 z-20">
        <button
          onClick={() => setSidebarCollapsed(false)}
          className="p-2.5 bg-[#050b1a]/90 backdrop-blur-md border border-cyan-950/80 rounded-xl text-cyan-400 hover:text-cyan-200 shadow-xl transition-all"
          title="Expand Inspection Sidebar"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <aside className="absolute top-4 right-4 bottom-4 w-96 z-20 flex flex-col bg-[#050b1a]/95 backdrop-blur-lg border border-cyan-950/80 rounded-xl shadow-2xl overflow-hidden pointer-events-auto text-slate-200">
      {/* Sidebar Header */}
      <div className="p-3.5 border-b border-cyan-950/80 flex items-center justify-between bg-[#08122c]/60">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <h2 className="text-xs font-mono uppercase tracking-wider font-semibold text-cyan-300">
            Object Telemetry & Catalog
          </h2>
        </div>
        <button
          onClick={() => setSidebarCollapsed(true)}
          className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition-colors"
          title="Collapse Sidebar"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-xs">
        {selectedTarget ? (
          <>
            {/* Target Title & Classification */}
            <div>
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-bold text-cyan-100 tracking-wide">
                    {selectedTarget.name}
                  </h3>
                  <div className="text-[11px] font-mono text-cyan-400/90">
                    {selectedTarget.designation}
                  </div>
                </div>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/50">
                  {selectedTarget.spectral_class}
                </span>
              </div>
              <div className="mt-1 inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-900/40">
                {selectedTarget.target_type}
              </div>
            </div>

            {/* Verified Astrometric Coordinates Card */}
            <div className="bg-[#09152e]/80 border border-cyan-950/80 rounded-lg p-3 font-mono space-y-1.5 text-[11px]">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1 flex items-center justify-between">
                <span>Verified Astrometry (ICRS)</span>
                <span className="text-cyan-400 text-[9px]">Gaia / SIMBAD</span>
              </div>
              <div className="grid grid-cols-2 gap-1.5 text-slate-300">
                <div>
                  RA: <span className="text-cyan-300">{selectedTarget.ra_hms}</span>
                </div>
                <div>
                  Dec: <span className="text-cyan-300">{selectedTarget.dec_dms}</span>
                </div>
                <div>
                  RA (deg): <span>{selectedTarget.ra_deg.toFixed(4)}°</span>
                </div>
                <div>
                  Dec (deg): <span>{selectedTarget.dec_deg.toFixed(4)}°</span>
                </div>
              </div>

              {/* Kinematics (Proper Motion, Parallax, Distance) */}
              <div className="pt-2 border-t border-cyan-950/60 grid grid-cols-2 gap-1.5 text-[10px] text-slate-300">
                <div>
                  μ_RA:{" "}
                  <span className="text-amber-300">
                    {selectedTarget.proper_motion_ra_mas_yr !== undefined
                      ? `${selectedTarget.proper_motion_ra_mas_yr} mas/yr`
                      : "N/A"}
                  </span>
                </div>
                <div>
                  μ_Dec:{" "}
                  <span className="text-amber-300">
                    {selectedTarget.proper_motion_dec_mas_yr !== undefined
                      ? `${selectedTarget.proper_motion_dec_mas_yr} mas/yr`
                      : "N/A"}
                  </span>
                </div>
                <div>
                  Parallax:{" "}
                  <span className="text-emerald-300">
                    {selectedTarget.parallax_mas !== undefined
                      ? `${selectedTarget.parallax_mas} mas`
                      : "N/A"}
                  </span>
                </div>
                <div>
                  Distance:{" "}
                  <span className="text-emerald-300">
                    {selectedTarget.distance_pc !== undefined
                      ? `${selectedTarget.distance_pc} pc (${(
                          selectedTarget.distance_pc * 3.26156
                        ).toFixed(1)} ly)`
                      : "N/A"}
                  </span>
                </div>
              </div>
            </div>

            {/* Astrophysical Description & Mission Role */}
            <div className="space-y-1.5">
              <h4 className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
                Astrophysical Profile
              </h4>
              <p className="text-slate-300 leading-relaxed text-[11px]">
                {selectedTarget.description}
              </p>
              <div className="bg-[#09152e]/50 border border-slate-800/80 p-2.5 rounded text-[11px] text-slate-300 space-y-1">
                <span className="font-semibold text-cyan-400 block">
                  SPHEREx Validation Role:
                </span>
                <span className="text-slate-300 leading-snug block">
                  {selectedTarget.test_validation_role}
                </span>
              </div>
            </div>

            {/* Available Observation Epochs */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1">
                  <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Available Observation Epochs</span>
                </h4>
                <span className="text-[10px] font-mono text-cyan-400">
                  {selectedTarget.available_epochs.length} Passes
                </span>
              </div>

              <div className="space-y-1.5">
                {selectedTarget.available_epochs.map((ep, idx) => {
                  const isActive = epochIndex === idx;
                  return (
                    <button
                      key={ep.epoch_id}
                      onClick={() => setSelectedEpochIndex(idx)}
                      className={`w-full text-left p-2 rounded border font-mono transition-all flex items-center justify-between ${
                        isActive
                          ? "bg-cyan-950/70 border-cyan-500 text-cyan-100 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                          : "bg-[#09152e]/50 border-cyan-950/60 text-slate-400 hover:border-cyan-800 hover:text-slate-200"
                      }`}
                    >
                      <div>
                        <div className="text-[11px] font-semibold text-cyan-300">
                          {ep.survey_pass}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {ep.timestamp_utc.slice(0, 10)} (MJD {ep.mjd.toFixed(1)})
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[11px] text-amber-300 font-semibold">
                          {ep.mean_flux_mjy_sr.toFixed(3)} MJy/sr
                        </div>
                        <div className="text-[9px] text-emerald-400 font-mono">
                          {ep.quality_flags[0]}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* External Catalog Cross-Matches */}
            <div className="space-y-2">
              <h4 className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                <span>External Astronomical Catalogs</span>
              </h4>

              <div className="space-y-2">
                {selectedTarget.catalog_crossmatches.map((cat, i) => (
                  <div
                    key={i}
                    className="bg-[#09152e]/60 border border-slate-800/80 rounded p-2.5 font-mono text-[10px] space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-cyan-300">
                        {cat.catalog_name}
                      </span>
                      <a
                        href={cat.provenance_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-400 hover:text-cyan-300 flex items-center space-x-0.5"
                      >
                        <span>Archive</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    </div>
                    <div className="text-slate-400 truncate">
                      ID: {cat.source_id}
                    </div>
                    <div className="text-slate-300 flex flex-wrap gap-2">
                      {Object.entries(cat.photometry).map(([band, val]) => (
                        <span key={band} className="bg-slate-900 px-1.5 py-0.5 rounded">
                          {band}:{" "}
                          <span className="text-amber-300">
                            {val !== null ? val.toFixed(2) : "N/A"}
                          </span>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="py-12 text-center text-slate-400 space-y-2">
            <Compass className="w-8 h-8 mx-auto text-cyan-500/50" />
            <div className="font-mono text-xs">No Target Selected</div>
            <div className="text-[11px] text-slate-400 max-w-[220px] mx-auto">
              Select one of the 5 NASA verification targets or search specific coordinates to inspect.
            </div>
          </div>
        )}
      </div>

      {/* Footer Provenance Badge */}
      <div className="p-3 border-t border-cyan-950/80 bg-[#08122c]/40 font-mono text-[10px] text-slate-400 flex items-center justify-between">
        <span className="flex items-center space-x-1 text-cyan-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Scientific Metadata Calibrated</span>
        </span>
        <span>NASA / IPAC / CDS</span>
      </div>
    </aside>
  );
}
