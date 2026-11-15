"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, ChevronDown, Telescope } from "lucide-react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { HeroStarfield } from "@/components/landing/HeroStarfield";
import { MultiSpectralViewer } from "@/components/landing/MultiSpectralViewer";
import { TemporalEpochComparison } from "@/components/landing/TemporalEpochComparison";
import { SpectralBandScrubber } from "@/components/landing/SpectralBandScrubber";
import { WorkspaceShowcase } from "@/components/landing/WorkspaceShowcase";
import { MathInline } from "@/components/ui/MathView";

export default function SkyTraceLandingPage() {
  return (
    <div className="skytrace-public relative min-h-screen bg-[#02040a] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col overflow-x-hidden">
      <LandingHeader />

      <main className="flex-1 flex flex-col">
        {/* =========================================================================
            ACT I — THE FIRST IMPRESSION
            ========================================================================= */}
        <section className="relative min-h-[92vh] flex items-center justify-center pt-24 pb-16 px-6 overflow-hidden">
          <HeroStarfield />

          <div className="relative z-10 max-w-5xl mx-auto text-center space-y-8">
            {/* Mission status pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-xs font-mono text-cyan-300 backdrop-blur-md">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              <span>SPHEREx ALL-SKY INFRARED SURVEY · 102 SPECTRAL BANDS</span>
            </div>

            {/* Aeruno Display Headline */}
            <h1 className="font-aeruno text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-slate-100 max-w-4xl mx-auto leading-[1.08] [text-wrap:balance]">
              The universe leaves a trace.
            </h1>

            {/* Supporting Narrative */}
            <p className="text-lg sm:text-xl text-slate-300 max-w-prose mx-auto leading-relaxed font-light [text-wrap:pretty]">
              Every star, galaxy, and distant cosmic structure leaves information in the light that reaches us. Much of that story exists beyond the limits of human&nbsp;vision.
            </p>

            <p className="text-sm sm:text-base text-slate-300 max-w-prose mx-auto leading-relaxed [text-wrap:pretty]">
              SkyTrace is an interactive scientific environment for exploring the infrared sky, examining observations across time, and investigating the spectral signatures hidden within astronomical data.
            </p>

            {/* CTAs */}
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/workspace"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl text-sm font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-lg shadow-black/70 hover:brightness-105 active:scale-[0.98] group"
              >
                <span>Explore the Universe</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <a
                href="#invisible-universe"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 transition-all"
              >
                <span>Discover the Science</span>
                <ChevronDown className="w-4 h-4 text-slate-400" />
              </a>
            </div>

            {/* Astronomical Telemetry Grid */}
            <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto text-left">
              <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/70">
                <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">SURVEY COVERAGE</div>
                <div className="text-base font-bold text-slate-100 mt-0.5">
                  All-Sky <MathInline math="4\pi\text{ sr}" />
                </div>
                <div className="text-xs text-slate-300 mt-0.5">450+ million galaxies</div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/70">
                <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">SPECTRAL BANDS</div>
                <div className="text-base font-bold text-slate-100 mt-0.5">102 Channels</div>
                <div className="text-xs text-slate-300 mt-0.5">
                  <MathInline math="0.75 - 5.00\,\mu\mathrm{m}" />
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/70">
                <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">DETECTOR ARRAYS</div>
                <div className="text-base font-bold text-slate-100 mt-0.5">6 LVF Focal Planes</div>
                <div className="text-xs text-slate-300 mt-0.5">D1–D6 HgCdTe</div>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/70">
                <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">SURVEY CADENCE</div>
                <div className="text-base font-bold text-slate-100 mt-0.5">Every 6 Months</div>
                <div className="text-xs text-slate-300 mt-0.5">Multi-epoch time domain</div>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================================================
            ACT II — THE INVISIBLE UNIVERSE
            ========================================================================= */}
        <section id="invisible-universe" className="py-24 px-6 border-t border-slate-900/80 bg-[#030611] relative">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Act II · The Electromagnetic Horizon
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              There is more to the universe than visible light.
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-slate-300 leading-relaxed text-sm sm:text-base pt-2">
              <p className="[text-wrap:pretty]">
                Human vision evolved to capture a tiny slice of the electromagnetic spectrum: wavelengths between <MathInline math="0.4" /> and <MathInline math="0.7\,\mu\mathrm{m}" />. But the cosmos does not restrict itself to the optical regime. Interstellar dust clouds throughout the Milky Way scatter and absorb optical light, veiling the very regions where stars and planetary systems are&nbsp;born.
              </p>
              <p className="[text-wrap:pretty]">
                NASA’s SPHEREx mission peers directly through this veil. Operating across 102 contiguous infrared bands from <MathInline math="0.75" /> to <MathInline math="5.00\,\mu\mathrm{m}" />, SPHEREx detects infrared emission from the earliest galaxies in the universe, traces the distribution of cosmic light, and unmasks the chemical fingerprints of water ice and biogenic molecules in interstellar&nbsp;space.
              </p>
            </div>

            {/* Interactive Multi-Spectral Viewer Component */}
            <MultiSpectralViewer />
          </div>
        </section>

        {/* =========================================================================
            ACT III — A SKY THAT CHANGES
            ========================================================================= */}
        <section id="temporal" className="py-24 px-6 border-t border-slate-900/80 bg-[#02040a] relative">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Act III · Temporal Astronomy
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              One position. Different moments in time.
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-slate-300 leading-relaxed text-sm sm:text-base pt-2">
              <p className="[text-wrap:pretty]">
                The universe is not static. Stars pulse, supernovae detonate, active galactic nuclei flicker, and Solar System asteroids streak silently across the celestial sphere. To discover these phenomena, astronomers must return to the exact same coordinates across&nbsp;time.
              </p>
              <p className="[text-wrap:pretty]">
                SkyTrace implements high-precision difference imaging (<MathInline math="D = I_{\mathrm{search}} - I_{\mathrm{ref}}" />): subtracting an earlier reference observation from a newly captured survey frame eliminates millions of invariant background stars. Any non-zero residual immediately unmasks genuine temporal&nbsp;variability.
              </p>
            </div>

            {/* Interactive Temporal Difference Engine Component */}
            <TemporalEpochComparison />
          </div>
        </section>

        {/* =========================================================================
            ACT IV — READING THE LIGHT
            ========================================================================= */}
        <section id="spectral" className="py-24 px-6 border-t border-slate-900/80 bg-[#030611] relative">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Act IV · 102 Spectral Channels
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              Every wavelength tells another part of the story.
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-slate-300 leading-relaxed text-sm sm:text-base pt-2">
              <p className="[text-wrap:pretty]">
                A standard telescope image tells you where light originates. A spectrum tells you what that light is made of. By dispersing infrared photons into 102 contiguous spectral bands, SPHEREx transforms every pixel on the sky into a rich physical energy distribution.
              </p>
              <p className="[text-wrap:pretty]">
                Specific wavelengths correspond to quantum transitions: interstellar water ice at <MathInline math="3.05\,\mu\mathrm{m}" />, polycyclic aromatic hydrocarbons at <MathInline math="3.30\,\mu\mathrm{m}" />, and carbon dioxide ice at <MathInline math="4.27\,\mu\mathrm{m}" />. By scanning through channels, astronomers decode the chemistry of stellar nurseries.
              </p>
            </div>

            {/* Interactive 102-Band Scrubber Component */}
            <SpectralBandScrubber />
          </div>
        </section>

        {/* =========================================================================
            ACT V — FROM DISCOVERY TO INVESTIGATION
            ========================================================================= */}
        <section id="investigation" className="py-24 px-6 border-t border-slate-900/80 bg-[#02040a] relative">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Act V · The Scientific Workflow
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              The next question is yours.
            </h2>
            <p className="text-slate-300 leading-relaxed text-sm sm:text-base max-w-prose pt-2 [text-wrap:pretty]">
              Discovery occurs at the intersection of three dimensions: WHERE a source resides on the celestial sphere, WHEN its emission changed, and WHAT its multi-wavelength spectrum reveals. SkyTrace provides the operational scientific environment to investigate all three simultaneously.
            </p>

            {/* IDE Capabilities Showcase */}
            <WorkspaceShowcase />
          </div>
        </section>

        {/* =========================================================================
            ACT VI — ENTER SKYTRACE
            ========================================================================= */}
        <section id="enter-skytrace" className="py-28 px-6 border-t border-slate-800/80 bg-[#020308] relative overflow-hidden text-center">
          <div className="relative z-10 max-w-3xl mx-auto space-y-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-500/20">
              <Telescope className="w-3.5 h-3.5" />
              <span>ACT VI · INVESTIGATION PORTAL</span>
            </div>

            <h2 className="font-aeruno text-4xl sm:text-6xl font-bold tracking-tight text-slate-100 leading-[1.1] [text-wrap:balance]">
              The sky is waiting to be investigated.
            </h2>

            <p className="text-base sm:text-lg text-slate-300 leading-relaxed font-light max-w-[65ch] mx-auto [text-wrap:pretty]">
              Move beyond observation. Explore the coordinates, compare the evidence, and investigate the infrared signatures of the universe.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/workspace"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-xl text-base font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-lg shadow-black/70 hover:brightness-105 active:scale-[0.98] group"
              >
                <span>Launch SkyTrace Workspace →</span>
              </Link>
            </div>

            {/* Fast jump routes */}
            <div className="pt-8 flex flex-wrap items-center justify-center gap-6 text-xs font-mono text-slate-300">
              <Link href="/workspace?tab=sky" className="hover:text-cyan-300 transition-colors">
                ▪ Sky Explorer View
              </Link>
              <Link href="/workspace?tab=temporal" className="hover:text-cyan-300 transition-colors">
                ▪ Time Domain Mode
              </Link>
              <Link href="/workspace?tab=spectral" className="hover:text-cyan-300 transition-colors">
                ▪ Spectral Lab
              </Link>
              <Link href="/workspace?tab=targets" className="hover:text-cyan-300 transition-colors">
                ▪ Target Validation
              </Link>
            </div>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
}
