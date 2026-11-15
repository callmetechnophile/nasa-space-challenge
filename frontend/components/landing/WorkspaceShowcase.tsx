"use client";

import React from "react";
import Link from "next/link";
import { Compass, Clock3, AudioLines, ShieldCheck, ArrowRight } from "lucide-react";

export function WorkspaceShowcase() {
  return (
    <div className="w-full max-w-5xl mx-auto my-12 space-y-12">
      {/* 3 Pillars of Discovery */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-gradient-to-b from-[#081226]/80 to-[#030611]/80 border border-slate-800/80 hover:border-cyan-500/40 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-4">
            <Compass className="w-5 h-5" />
          </div>
          <div className="text-xs font-mono text-cyan-400 mb-1">DIMENSION 1</div>
          <h3 className="text-lg font-bold text-slate-100 mb-2 [text-wrap:balance]">WHERE — Coordinates</h3>
          <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
            Locate and navigate astronomical positions across the full celestial sphere. Project authentic SPHEREx Level 2 FITS cutouts onto ICRS coordinates with sub-arcsecond WCS precision.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-gradient-to-b from-[#081226]/80 to-[#030611]/80 border border-slate-800/80 hover:border-cyan-500/40 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-4">
            <Clock3 className="w-5 h-5" />
          </div>
          <div className="text-xs font-mono text-cyan-400 mb-1">DIMENSION 2</div>
          <h3 className="text-lg font-bold text-slate-100 mb-2 [text-wrap:balance]">WHEN — Epochs</h3>
          <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
            Investigate temporal variability across observation epochs. Perform pixel-matched difference imaging and convolve with detector-position ePSF templates to extract transient candidates.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-gradient-to-b from-[#081226]/80 to-[#030611]/80 border border-slate-800/80 hover:border-cyan-500/40 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-4">
            <AudioLines className="w-5 h-5" />
          </div>
          <div className="text-xs font-mono text-cyan-400 mb-1">DIMENSION 3</div>
          <h3 className="text-lg font-bold text-slate-100 mb-2 [text-wrap:balance]">WHAT — Spectra</h3>
          <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
            Unpack the physical composition across 102 contiguous spectral bands from 0.75 to 5.0 µm. Measure absorption depths, emission lines, and redshift diagnostics in the interactive Spectral Lab.
          </p>
        </div>
      </div>

      {/* High-Fidelity IDE Visual Interface Showcase */}
      <div className="relative rounded-2xl border border-slate-700/80 bg-[#17191e] overflow-hidden shadow-2xl">
        {/* Mock IDE Titlebar */}
        <div className="h-10 px-4 bg-[#17191e] border-b border-[#30343d] flex items-center justify-between text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-rose-500/70 inline-block" />
            <span className="w-3 h-3 rounded-full bg-amber-500/70 inline-block" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/70 inline-block" />
            <span className="ml-3 font-corpta text-slate-200 tracking-wider">SkyTrace</span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-300 font-mono text-xs">spherex-research</span>
          </div>
          <div className="px-3 py-1 rounded bg-[#22252c] border border-[#343943] text-xs font-mono text-slate-300 hidden sm:block">
            ⌘K Open workspace or command
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-300">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>RESEARCH ENVIRONMENT</span>
          </div>
        </div>

        {/* Mock IDE Tabstrip */}
        <div className="h-9 px-2 bg-[#1d2026] border-b border-[#30343d] flex items-center gap-1 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-t bg-[#17191e] border-t border-cyan-400 text-slate-200 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>sky_viewer.fits</span>
          </div>
          <div className="px-3 py-1.5 text-slate-400 hover:text-slate-200 cursor-pointer flex items-center gap-2">
            <Clock3 className="w-3.5 h-3.5 text-slate-400" />
            <span>epoch_compare</span>
          </div>
          <div className="px-3 py-1.5 text-slate-400 hover:text-slate-200 cursor-pointer flex items-center gap-2">
            <AudioLines className="w-3.5 h-3.5 text-slate-400" />
            <span>spectral_cube</span>
          </div>
          <div className="px-3 py-1.5 text-slate-400 hover:text-slate-200 cursor-pointer hidden md:flex items-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
            <span>validation_targets</span>
          </div>
        </div>

        {/* Mock IDE Body Grid */}
        <div className="grid grid-cols-12 h-80 sm:h-96 bg-[#050912] relative overflow-hidden">
          {/* Mock Sidebar */}
          <div className="col-span-3 sm:col-span-3 border-r border-[#30343d] bg-[#1e2128] p-3 hidden sm:block text-xs font-mono text-slate-300 space-y-3">
            <div className="text-slate-400 uppercase tracking-wider text-xs">EXPLORER: SPHEREx</div>
            <div className="space-y-1.5 pl-2">
              <div className="text-cyan-300 flex items-center gap-1.5">
                <span>▾ observations</span>
              </div>
              <div className="pl-3 space-y-1 text-slate-300">
                <div className="text-cyan-400 font-medium">▪ sky_viewer.fits</div>
                <div>▫ level2_2026W31.fits</div>
                <div>▫ level2_2026W32.fits</div>
              </div>
              <div className="text-slate-300 flex items-center gap-1.5 pt-2">
                <span>▸ spectral_data</span>
              </div>
              <div className="text-slate-300 flex items-center gap-1.5">
                <span>▸ time_domain</span>
              </div>
              <div className="text-slate-300 flex items-center gap-1.5">
                <span>▸ validation_targets</span>
              </div>
            </div>
          </div>

          {/* Main Visual Viewport Mock */}
          <div className="col-span-12 sm:col-span-9 relative flex items-center justify-center p-6 bg-gradient-to-br from-[#060c1d] via-[#040816] to-[#02050f]">
            {/* Celestial sphere representation */}
            <div className="relative w-56 h-56 sm:w-72 sm:h-72 rounded-full border border-cyan-500/30 bg-[#030612] flex items-center justify-center shadow-2xl">
              <div className="absolute inset-4 rounded-full border border-dashed border-cyan-500/20 animate-spin" style={{ animationDuration: "120s" }} />
              <div className="absolute inset-12 rounded-full border border-slate-700/40" />
              
              {/* Star dots */}
              <div className="absolute top-1/4 left-1/3 w-1.5 h-1.5 rounded-full bg-cyan-200" />
              <div className="absolute top-1/2 right-1/4 w-2 h-2 rounded-full bg-amber-300" />
              <div className="absolute bottom-1/3 left-1/4 w-1.5 h-1.5 rounded-full bg-rose-300" />
              
              {/* Reticle target */}
              <div className="w-16 h-16 border border-cyan-400/60 rounded flex items-center justify-center">
                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full" />
              </div>

              {/* Float HUD widget */}
              <div className="absolute -bottom-2 right-2 px-3 py-1.5 rounded-lg bg-black/85 border border-slate-700 text-xs font-mono text-cyan-300 shadow-md">
                RA: 132.748° · DEC: -5.621°
              </div>
            </div>

            {/* Quick action buttons overlay */}
            <div className="absolute bottom-4 left-6 flex items-center gap-3">
              <Link
                href="/workspace"
                className="px-4 py-2 rounded-lg bg-cyan-500 text-slate-950 text-xs font-semibold hover:bg-cyan-400 transition-colors shadow-md flex items-center gap-2"
              >
                <span>Launch Workspace</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>

        {/* Mock IDE Statusbar */}
        <div className="h-6 px-3 bg-[#1e485e] text-white flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-3">
            <span>skytrace (main)</span>
            <span>• Workspace ready</span>
          </div>
          <div className="flex items-center gap-4 hidden sm:flex">
            <span>RA 132.7481°</span>
            <span>DEC -05.6214°</span>
            <span>FOV 60.00°</span>
            <span>CHANNEL 61/102</span>
          </div>
        </div>
      </div>
    </div>
  );
}
