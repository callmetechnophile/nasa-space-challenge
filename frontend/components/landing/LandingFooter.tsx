"use client";

import React from "react";
import Link from "next/link";
import { Atom, ExternalLink, Code2, Telescope } from "lucide-react";

export function LandingFooter() {
  return (
    <footer className="w-full border-t border-slate-800/80 bg-[#020308] text-slate-300 py-16 px-6 relative z-10">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-10">
        {/* Col 1: Brand & Mission summary */}
        <div className="md:col-span-4 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-cyan-950/80 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Atom className="w-4 h-4" />
            </div>
            <span className="font-corpta text-2xl tracking-wider text-slate-100">
              SkyTrace
            </span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed max-w-sm [text-wrap:pretty]">
            An interactive scientific environment for exploring the infrared sky, examining observations across time, and investigating the spectral signatures hidden within astronomical data.
          </p>
          <div className="text-xs font-mono text-slate-400">
            SYS: SPHEREx All-Sky Infrared Survey · 102 Spectral Bands
          </div>
        </div>

        {/* Col 2: SPHEREx Mission Exploration */}
        <div className="md:col-span-3 space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-slate-200">
            SPHEREx Mission
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            <li>
              <Link href="/spherex" className="hover:text-cyan-300 transition-colors">
                Mission Overview
              </Link>
            </li>
            <li>
              <Link href="/spherex/instrument" className="hover:text-cyan-300 transition-colors">
                Instrument &amp; Optics Architecture
              </Link>
            </li>
            <li>
              <Link href="/spherex/spectral-bands" className="hover:text-cyan-300 transition-colors">
                Spectral Explorer (102 Bands)
              </Link>
            </li>
            <li>
              <Link href="/workspace?tab=spectral" className="hover:text-cyan-300 transition-colors text-slate-400">
                Workspace Spectral Lab →
              </Link>
            </li>
          </ul>
        </div>

        {/* Col 3: Planet X & Science */}
        <div className="md:col-span-2 space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-slate-200">
            Outer Solar System
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            <li>
              <Link href="/planet-x" className="hover:text-cyan-300 transition-colors">
                Planet X Mystery
              </Link>
            </li>
            <li>
              <Link href="/planet-x/evidence" className="hover:text-cyan-300 transition-colors">
                Evidence &amp; Search Record
              </Link>
            </li>
            <li>
              <Link href="/science" className="hover:text-cyan-300 transition-colors">
                Science &amp; Methodology
              </Link>
            </li>
            <li>
              <Link href="/workspace" className="hover:text-cyan-300 transition-colors text-cyan-400 font-semibold">
                Launch Workspace →
              </Link>
            </li>
          </ul>
        </div>

        {/* Col 4: Provenance & Attribution */}
        <div className="md:col-span-3 space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-slate-200">
            Font &amp; Mission Provenance
          </div>
          <div className="text-xs text-slate-300 space-y-2 leading-relaxed [text-wrap:pretty]">
            <p>
              Display typography uses <strong className="text-slate-100 font-semibold">AERUNO</strong> by Omzen Type and wordmark uses <strong className="text-slate-100 font-semibold">CORPTA</strong> by Pandeka Foundry (1001Fonts Free for Personal Use&nbsp;License).
            </p>
            <p className="text-slate-400">
              Astronomical pipeline processes calibrated SPHEREx Level 2 FITS products. Independent research project; not an official NASA, JPL, or Caltech product.
            </p>
          </div>
          <div className="pt-2">
            <a
              href="https://github.com/astrogreg/nasa"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-xs font-mono text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Source Repository</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto pt-12 mt-12 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-400">
        <div>© 2026 SkyTrace Research Initiative. All rights reserved.</div>
        <div className="flex items-center gap-2 text-slate-400">
          <Telescope className="w-3.5 h-3.5 text-cyan-400" />
          <span>Infrared Astronomy · Time-Domain · Multi-Spectral</span>
        </div>
      </div>
    </footer>
  );
}
