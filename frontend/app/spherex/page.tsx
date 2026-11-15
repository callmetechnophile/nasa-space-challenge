"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, ExternalLink, Sparkles, Globe, Orbit, ShieldCheck, Telescope } from "lucide-react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { Breadcrumbs } from "@/components/landing/Breadcrumbs";
import { SpacecraftViewer } from "@/components/visuals/SpacecraftViewer";
import { ObservationProcessViewer } from "@/components/visuals/ObservationProcessViewer";
import { DetectorArrayViewer } from "@/components/visuals/DetectorArrayViewer";
import { TelescopeIcon, SpectralIcon, DetectorIcon, CoordinateIcon } from "@/components/visuals/3d-icons";
import { MathInline, MathDisplay } from "@/components/ui/MathView";

export default function SpherexMissionPage() {
  return (
    <div className="skytrace-public relative min-h-screen bg-[#02040a] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col overflow-x-hidden">
      <LandingHeader />

      <main className="flex-1 flex flex-col pt-24 pb-20">
        {/* Breadcrumb Navigation */}
        <div className="max-w-7xl mx-auto px-6 w-full pt-4 pb-6">
          <Breadcrumbs items={[{ label: "SPHEREx Mission" }]} />
        </div>

        {/* Hero Section */}
        <section className="px-6 py-12 md:py-16 max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-xs font-mono text-cyan-300">
            <TelescopeIcon size={20} className="shrink-0" />
            <span>NASA ASTROPHYSICS MID-SCALE EXPLORER (MIDEX)</span>
          </div>

          <h1 className="font-aeruno text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-slate-100 leading-[1.08] [text-wrap:balance]">
            Mapping the Universe in Infrared.
          </h1>

          <p className="text-lg sm:text-xl text-slate-300 max-w-[65ch] mx-auto leading-relaxed font-light [text-wrap:pretty]">
            SPHEREx reveals a richer picture of the universe by surveying the entire sky across 102 infrared wavelengths.
          </p>

          <div className="pt-2 flex flex-wrap items-center justify-center gap-4 text-xs font-mono text-slate-400">
            <span>FULL NAME: Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer</span>
          </div>
        </section>

        {/* Section A: Mission Overview */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Section A · Mission Overview & Scientific Rationale
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              An All-Sky Infrared Spectroscopic Map
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-slate-300 leading-relaxed text-sm sm:text-base [text-wrap:pretty]">
              <p>
                NASA selected SPHEREx to address core astronomical questions that cannot be solved by narrow pencil-beam observatories alone. While telescopes like Hubble and James Webb investigate small patches of deep space at high magnification, SPHEREx maps the entire <MathInline math="4\pi" /> celestial sphere, observing over 450 million galaxies and 100 million Milky Way stars in 102 contiguous infrared bands.
              </p>
              <p>
                Infrared light passes through interstellar cosmic dust clouds that scatter visible wavelengths. By measuring spectra continuously from <MathInline math="0.75" /> to <MathInline math="5.0\,\mu\mathrm{m}" />, SPHEREx unmasks early cosmic inflation through galaxy clustering, traces the history of light from the first stars, and charts the distribution of biogenic water ice and organic compounds throughout protoplanetary systems.
              </p>
            </div>

            {/* Quick Mission Pillars */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-xs space-y-1.5">
                <span className="font-mono text-cyan-400 uppercase block font-semibold">Survey Cadence</span>
                <span className="text-sm font-bold text-slate-100 block">Every 6 Months</span>
                <span className="text-slate-400 block">4 complete all-sky passes over 2-year baseline mission.</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-xs space-y-1.5">
                <span className="font-mono text-cyan-400 uppercase block font-semibold">Spectral Bandwidth</span>
                <span className="text-sm font-bold text-slate-100 block">102 Contiguous Bands</span>
                <span className="text-slate-400 block">0.75 µm to 5.00 µm with resolving power R = 41 to 135.</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-xs space-y-1.5">
                <span className="font-mono text-cyan-400 uppercase block font-semibold">Statistical Reach</span>
                <span className="text-sm font-bold text-slate-100 block">450M+ Galaxies</span>
                <span className="text-slate-400 block">Redshift survey measuring cosmic inflation across large scales.</span>
              </div>
            </div>
          </div>
        </section>

        {/* Section B: The Spacecraft */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#02040a]">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Section B · Spacecraft Architecture
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              Passive Cryogenic Engineering in Orbit
            </h2>
            <p className="text-sm sm:text-base text-slate-300 max-w-[65ch] leading-relaxed [text-wrap:pretty]">
              SPHEREx carries no active liquid helium cryogens. Instead, three nested conical V-groove photon shields reflect sunlight and spacecraft bus heat out into deep space, cooling the aluminum telescope below 80 K entirely passively.
            </p>

            {/* Interactive Spacecraft 3D CAD Component */}
            <SpacecraftViewer />

            <div className="pt-2">
              <Link
                href="/spherex/instrument"
                className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                <span>Explore complete instrument architecture & optics →</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Section C: How SPHEREx Sees the Sky */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Section C · Observation Mechanics
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              How SPHEREx Sees the Sky
            </h2>
            <p className="text-sm sm:text-base text-slate-300 max-w-[65ch] leading-relaxed [text-wrap:pretty]">
              Unlike conventional astronomical cameras that require mechanical filter wheels, SPHEREx uses Linear Variable Filters and stepped slews to turn each pixel on the sky into an intact 102-point spectrum.
            </p>

            {/* Observation Process Viewer */}
            <ObservationProcessViewer />
          </div>
        </section>

        {/* Section D: The Six Detector Arrays */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#02040a]">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Section D · The Six Focal Plane Arrays
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              Six Detectors. 102 Spectral Channels.
            </h2>
            <p className="text-sm sm:text-base text-slate-300 max-w-[65ch] leading-relaxed [text-wrap:pretty]">
              The focal plane assembly incorporates six independent Teledyne Hawaii-2RG (H2RG) HgCdTe arrays, each allocated 17 discrete spectral bands spanning 0.75 to 5.00 microns.
            </p>

            {/* Detector Array Viewer */}
            <DetectorArrayViewer />

            <div className="pt-2">
              <Link
                href="/spherex/spectral-bands"
                className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                <span>Launch the interactive 102-band spectral explorer →</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Section E: The Three Science Goals */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-10">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Section E · Primary Science Objectives
              </div>
              <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
                Three Pillars of Astronomical Investigation
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Pillar 1: Cosmic History */}
              <div className="p-6 rounded-2xl bg-[#040814] border border-slate-800 space-y-4 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <Globe className="w-5 h-5 text-cyan-400 shrink-0" />
                    <h3 className="text-xl font-bold text-slate-100 [text-wrap:balance]">
                      1. Cosmic History & Inflation
                    </h3>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
                    In the first fractions of a second after the Big Bang, cosmic inflation stretched quantum fluctuations into the large-scale distribution of galaxies. By measuring 3D coordinates for over 450 million galaxies across the universe, SPHEREx tests models of non-Gaussianity and early cosmic acceleration.
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-800 text-xs font-mono text-cyan-300">
                  Metric: Galaxy clustering power spectrum <MathInline math="P(k) = \langle |\delta_g(\mathbf{k})|^2 \rangle" />
                </div>
              </div>

              {/* Pillar 2: Galactic Light */}
              <div className="p-6 rounded-2xl bg-[#040814] border border-slate-800 space-y-4 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-cyan-400 shrink-0" />
                    <h3 className="text-xl font-bold text-slate-100 [text-wrap:balance]">
                      2. Origin of Cosmic Light
                    </h3>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
                    By analyzing the diffuse Extra-Galactic Background Light (EBL) fluctuations between galaxies, SPHEREx isolates the aggregate light produced by the very first stars and proto-galaxies that formed during cosmic dawn, as well as faint stars ejected into intergalactic space.
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-800 text-xs font-mono text-cyan-300">
                  Metric: EBL spatial angular power spectrum <MathInline math="C_\ell" />
                </div>
              </div>

              {/* Pillar 3: Ingredients for New Worlds */}
              <div className="p-6 rounded-2xl bg-[#040814] border border-slate-800 space-y-4 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <Orbit className="w-5 h-5 text-cyan-400 shrink-0" />
                    <h3 className="text-xl font-bold text-slate-100 [text-wrap:balance]">
                      3. Ingredients for New Worlds
                    </h3>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
                    Water ice (H₂O), carbon dioxide (CO₂), and carbon monoxide (CO) freeze onto interstellar dust grains inside molecular clouds. SPHEREx maps these biogenic ice absorption features toward hundreds of thousands of stellar nurseries, tracking the chemical ingredients that seed habitable planetary systems.
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-800 text-xs font-mono text-cyan-300">
                  Metric: Ice optical depth <MathInline math="\tau(\lambda) = -\ln(I/I_0)" /> (3.05 µm H₂O, 4.27 µm CO₂)
                </div>
              </div>
            </div>

            {/* Authoritative NASA / Caltech Reference Links */}
            <div className="pt-6 border-t border-slate-800/80 flex flex-wrap items-center gap-6 text-xs font-mono text-slate-300">
              <span className="text-slate-400">Authoritative References:</span>
              <a
                href="https://science.nasa.gov/mission/spherex/"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-cyan-300 transition-colors inline-flex items-center gap-1"
              >
                <span>NASA SPHEREx Mission Page</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <a
                href="https://spherex.caltech.edu/page/survey"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-cyan-300 transition-colors inline-flex items-center gap-1"
              >
                <span>Caltech SPHEREx Science Center</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <a
                href="https://irsa.ipac.caltech.edu/Missions/spherex.html"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-cyan-300 transition-colors inline-flex items-center gap-1"
              >
                <span>NASA/IPAC IRSA Archive</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
}
