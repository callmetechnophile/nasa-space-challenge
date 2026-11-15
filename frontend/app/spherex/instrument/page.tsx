"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, ExternalLink, ShieldCheck, Cpu, Layers, Sun, Snowflake, Eye } from "lucide-react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { Breadcrumbs } from "@/components/landing/Breadcrumbs";
import { SpacecraftViewer } from "@/components/visuals/SpacecraftViewer";
import { TelescopeIcon, DetectorIcon, SpectralIcon } from "@/components/visuals/3d-icons";
import { MathInline, MathDisplay } from "@/components/ui/MathView";

export default function SpherexInstrumentPage() {
  return (
    <div className="skytrace-public relative min-h-screen bg-[#02040a] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col overflow-x-hidden">
      <LandingHeader />

      <main className="flex-1 flex flex-col pt-24 pb-20">
        {/* Breadcrumb Navigation */}
        <div className="max-w-7xl mx-auto px-6 w-full pt-4 pb-6">
          <Breadcrumbs
            items={[
              { label: "SPHEREx", href: "/spherex" },
              { label: "Instrument Architecture" },
            ]}
          />
        </div>

        {/* Hero Section */}
        <section className="px-6 py-12 max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-xs font-mono text-cyan-300">
            <TelescopeIcon size={20} className="shrink-0" />
            <span>OPTICAL & CRYOGENIC ARCHITECTURE</span>
          </div>

          <h1 className="font-aeruno text-4xl sm:text-6xl font-bold tracking-tight text-slate-100 leading-[1.08] [text-wrap:balance]">
            Precision Slitless Infrared Spectroscopy
          </h1>

          <p className="text-lg text-slate-300 max-w-[65ch] mx-auto leading-relaxed font-light [text-wrap:pretty]">
            An all-aluminum, three-mirror anastigmat wide-field telescope passively cooled to 80 Kelvin, capturing 102 spectral bands simultaneously without moving mechanisms.
          </p>
        </section>

        {/* CAD Spacecraft Model Exploration */}
        <section className="px-6 py-12 max-w-5xl mx-auto w-full space-y-4">
          <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
            Interactive Subsystem Inspection
          </div>
          <h2 className="font-aeruno text-2xl sm:text-4xl font-bold tracking-tight text-slate-100">
            3D Spacecraft & Instrument CAD Architecture
          </h2>
          <SpacecraftViewer />
        </section>

        {/* Deep-Dive Subsystems */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-12">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Hardware Engineering
              </div>
              <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
                Subsystem Specifications & Physics
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Optical Assembly */}
              <div className="p-6 rounded-2xl bg-[#040814] border border-slate-800 space-y-4">
                <div className="flex items-center gap-3">
                  <TelescopeIcon size={28} className="shrink-0 text-cyan-400" />
                  <div>
                    <h3 className="text-xl font-bold text-slate-100">All-Aluminum TMA Telescope</h3>
                    <div className="text-xs font-mono text-cyan-400">Three-Mirror Anastigmat</div>
                  </div>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
                  Constructed entirely from a single aluminum alloy (6061-T6) for both mirrors and structural housing. As the telescope cools from room temperature (293 K) down to cryogenic operating temperature (80 K), all optical elements shrink at identical rates, preserving diffraction-limited alignment without mechanical focus actuators.
                </p>
                <div className="pt-2 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs font-mono">
                  <div><span className="text-slate-400 block">Clear Aperture:</span> <span className="text-slate-100 font-semibold"><MathInline math="D = 20.0\,\mathrm{cm}" /></span></div>
                  <div><span className="text-slate-400 block">Focal Ratio:</span> <span className="text-slate-100 font-semibold"><MathInline math="F/3\ (f = 60.0\,\mathrm{cm})" /></span></div>
                  <div><span className="text-slate-400 block">Field of View:</span> <span className="text-cyan-300 font-semibold"><MathInline math="3.5^\circ \times 11.3^\circ" /></span></div>
                  <div><span className="text-slate-400 block">Pixel Scale:</span> <span className="text-slate-100 font-semibold"><MathInline math="6.2''/\mathrm{pixel}" /></span></div>
                </div>
              </div>

              {/* Thermal V-Groove Shields */}
              <div className="p-6 rounded-2xl bg-[#040814] border border-slate-800 space-y-4">
                <div className="flex items-center gap-3">
                  <Snowflake className="w-6 h-6 shrink-0 text-cyan-400" />
                  <div>
                    <h3 className="text-xl font-bold text-slate-100">Passive Cryogenic Cooling</h3>
                    <div className="text-xs font-mono text-cyan-400">3-Stage Conical V-Groove Shields</div>
                  </div>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
                  SPHEREx operates without active mechanical cryocoolers or liquid cryogens. Three concentric, nested aluminum cones reject thermal radiation from the solar arrays and spacecraft bus. Radiation bounces between the specular cone surfaces and is directed out into deep space, dropping stage temperatures from 300 K to 150 K, 100 K, and finally &lt;80 K at the telescope.
                </p>
                <div className="pt-2 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs font-mono">
                  <div><span className="text-slate-400 block">Telescope Temp:</span> <span className="text-slate-100 font-semibold"><MathInline math="T < 80\,\mathrm{K}" /></span></div>
                  <div><span className="text-slate-400 block">D5/D6 Array Temp:</span> <span className="text-cyan-300 font-semibold"><MathInline math="T < 55\,\mathrm{K}" /></span></div>
                  <div><span className="text-slate-400 block">Cryogen Need:</span> <span className="text-slate-100 font-semibold">0 liters (100% passive)</span></div>
                  <div><span className="text-slate-400 block">Mission Lifetime:</span> <span className="text-slate-100 font-semibold">2+ Years (unlimited by cryogens)</span></div>
                </div>
              </div>

              {/* Beam Separation & Dichroics */}
              <div className="p-6 rounded-2xl bg-[#040814] border border-slate-800 space-y-4">
                <div className="flex items-center gap-3">
                  <Layers className="w-6 h-6 shrink-0 text-cyan-400" />
                  <div>
                    <h3 className="text-xl font-bold text-slate-100">Dichroic Beam Splitter</h3>
                    <div className="text-xs font-mono text-cyan-400">Short & Long Wavelength Channels</div>
                  </div>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
                  Following the tertiary mirror, a high-efficiency dielectric dichroic beam splitter reflects wavelengths shorter than 2.42 µm to the Short Wavelength focal plane (Detectors D1, D2, D3) while transmitting wavelengths longer than 2.42 µm to the Long Wavelength focal plane (Detectors D4, D5, D6).
                </p>
                <div className="pt-2 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs font-mono">
                  <div><span className="text-slate-400 block">SW Cutoff:</span> <span className="text-slate-100 font-semibold"><MathInline math="\lambda < 2.42\,\mu\mathrm{m}" /></span></div>
                  <div><span className="text-slate-400 block">LW Range:</span> <span className="text-cyan-300 font-semibold"><MathInline math="\lambda \ge 2.42\,\mu\mathrm{m}" /></span></div>
                  <div><span className="text-slate-400 block">Transmission:</span> <span className="text-slate-100 font-semibold"><MathInline math="\eta > 95\%" /></span></div>
                  <div><span className="text-slate-400 block">Optical Channels:</span> <span className="text-slate-100 font-semibold">2 Simultaneous Channels</span></div>
                </div>
              </div>

              {/* Linear Variable Filters */}
              <div className="p-6 rounded-2xl bg-[#040814] border border-slate-800 space-y-4">
                <div className="flex items-center gap-3">
                  <SpectralIcon size={28} className="shrink-0 text-cyan-400" />
                  <div>
                    <h3 className="text-xl font-bold text-slate-100">Linear Variable Filters (LVF)</h3>
                    <div className="text-xs font-mono text-cyan-400">Slitless Spectroscopy Assembly</div>
                  </div>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
                  Directly cemented above the six H2RG detectors are dielectric multilayer interference filters whose passband center varies continuously along one spatial axis. Each detector hosts 17 discrete spectral sub-bands, producing a total of 102 contiguous channels without gratings, prisms, or rotating mechanisms.
                </p>
                <div className="pt-2 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs font-mono">
                  <div><span className="text-slate-400 block">Channels / Array:</span> <span className="text-slate-100 font-semibold">17 bands</span></div>
                  <div><span className="text-slate-400 block">Total Channels:</span> <span className="text-cyan-300 font-semibold">102 bands</span></div>
                  <div><span className="text-slate-400 block">Resolving Power:</span> <span className="text-slate-100 font-semibold"><MathInline math="R \approx 41\text{ (SW)} / 135\text{ (LW)}" /></span></div>
                  <div><span className="text-slate-400 block">Wavelength Span:</span> <span className="text-slate-100 font-semibold"><MathInline math="0.75 - 5.00\,\mu\mathrm{m}" /></span></div>
                </div>
              </div>
            </div>

            {/* Orbit & Scanning Strategy Section */}
            <div className="p-8 rounded-2xl bg-[#02040a] border border-slate-800 space-y-6">
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
                Observational Trajectory
              </div>
              <h3 className="text-2xl font-bold text-slate-100 [text-wrap:balance]">
                Sun-Synchronous Polar Terminator Orbit
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed max-w-[65ch] [text-wrap:pretty]">
                SPHEREx orbits at an altitude of approximately 700 km with an orbital period of 97 minutes, matching Earth's day/night terminator. The solar panels always face the Sun at a fixed 90° orientation while the telescope observes perpendicular to the Sun-spacecraft vector, continuously sweeping out great circles on the celestial sphere.
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-3 border-y border-slate-800 text-xs font-mono">
                <div>
                  <span className="text-slate-400 block">Orbit Altitude</span>
                  <span className="text-slate-100 font-bold text-sm"><MathInline math="h \approx 700\,\mathrm{km}" /></span>
                </div>
                <div>
                  <span className="text-slate-400 block">Inclination</span>
                  <span className="text-slate-100 font-bold text-sm"><MathInline math="i = 98.2^\circ" /> (Polar)</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Full Sky Coverage</span>
                  <span className="text-cyan-300 font-bold text-sm"><MathInline math="4\pi\text{ sr every 6 mo}" /></span>
                </div>
                <div>
                  <span className="text-slate-400 block">Total Surveys</span>
                  <span className="text-slate-100 font-bold text-sm"><MathInline math="N_{\text{survey}} = 4" /></span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Action Bar */}
        <section className="px-6 py-12 border-t border-slate-800/80 bg-[#020308] text-center">
          <div className="max-w-2xl mx-auto space-y-6">
            <h3 className="font-aeruno text-2xl sm:text-3xl font-bold text-slate-100 [text-wrap:balance]">
              Explore the 102 Spectral Bands in Action
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
              Inspect how the six linear variable filter arrays break down the infrared universe channel by channel.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/spherex/spectral-bands"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-md shadow-black/60"
              >
                <span>Open Spectral Explorer →</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
}
