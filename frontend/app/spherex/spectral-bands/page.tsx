"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, ExternalLink, AudioLines, Sparkles, Filter, Info, ShieldCheck } from "lucide-react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { Breadcrumbs } from "@/components/landing/Breadcrumbs";
import { SpectralBandScrubber } from "@/components/landing/SpectralBandScrubber";
import { SpectralIcon, DetectorIcon } from "@/components/visuals/3d-icons";
import { MathInline, MathDisplay } from "@/components/ui/MathView";

interface DiagnosticFeature {
  wavelength: number;
  name: string;
  chemicalFormula: string;
  regime: string;
  detector: string;
  role: string;
  spectralType: "Absorption" | "Emission" | "Continuum";
}

const NOTABLE_LINES: DiagnosticFeature[] = [
  {
    wavelength: 0.88,
    name: "Paschen-ζ Recombination",
    chemicalFormula: "H I (n=8 → 3)",
    regime: "Near-IR / D1",
    detector: "Array D1 (Ch 8)",
    role: "Stellar continuum calibration and ionization levels in late-type M dwarf photospheres.",
    spectralType: "Absorption",
  },
  {
    wavelength: 1.282,
    name: "Paschen-β Hydrogen Line",
    chemicalFormula: "H I (n=5 → 3)",
    regime: "Near-IR / D2",
    detector: "Array D2 (Ch 23)",
    role: "Traces ionized hydrogen gas in massive H II regions with minimal dust attenuation.",
    spectralType: "Emission",
  },
  {
    wavelength: 2.122,
    name: "Molecular Hydrogen 1-0 S(1)",
    chemicalFormula: "H₂ (v=1-0)",
    regime: "Near-IR / D3",
    detector: "Array D3 (Ch 42)",
    role: "Traces supersonic shocks and bipolar protostellar outflows colliding with dense cold gas.",
    spectralType: "Emission",
  },
  {
    wavelength: 2.65,
    name: "Hot Water Vapor",
    chemicalFormula: "H₂O (Gas)",
    regime: "Mid-IR / D4",
    detector: "Array D4 (Ch 56)",
    role: "Detects sublimating water vapor in circumstellar disks and active cometary comae.",
    spectralType: "Absorption",
  },
  {
    wavelength: 3.05,
    name: "Interstellar Water Ice",
    chemicalFormula: "H₂O (Solid Mantle)",
    regime: "Mid-IR / D4",
    detector: "Array D4 (Ch 61)",
    role: "Primary planetary ingredient: maps solid water ice grain mantles across cold molecular clouds.",
    spectralType: "Absorption",
  },
  {
    wavelength: 3.29,
    name: "PAH C–H Vibrational Stretch",
    chemicalFormula: "C_x H_y Organics",
    regime: "Mid-IR / D4",
    detector: "Array D4 (Ch 65)",
    role: "Fluorescence from complex polycyclic aromatic hydrocarbons excited by ultraviolet starlight.",
    spectralType: "Emission",
  },
  {
    wavelength: 4.052,
    name: "Brackett-α Hydrogen Line",
    chemicalFormula: "H I (n=5 → 4)",
    regime: "Mid-IR / D5",
    detector: "Array D5 (Ch 77)",
    role: "Deepest penetration into embedded starburst regions; highest-flux infrared hydrogen transition.",
    spectralType: "Emission",
  },
  {
    wavelength: 4.27,
    name: "Carbon Dioxide Ice Band",
    chemicalFormula: "CO₂ (Solid)",
    regime: "Deep-IR / D5",
    detector: "Array D5 (Ch 81)",
    role: "Diagnostic of planetary chemical origins: traces CO₂ freezing in protoplanetary envelopes.",
    spectralType: "Absorption",
  },
  {
    wavelength: 4.67,
    name: "Carbon Monoxide Fundamental",
    chemicalFormula: "CO (Solid & Gas)",
    regime: "Deep-IR / D6",
    detector: "Array D6 (Ch 93)",
    role: "Essential carbon reservoir mapping in cold circumstellar disks and external galaxy nuclei.",
    spectralType: "Absorption",
  },
];

export default function SpherexSpectralBandsPage() {
  const [selectedFeature, setSelectedFeature] = useState<DiagnosticFeature>(NOTABLE_LINES[4]);

  return (
    <div className="skytrace-public relative min-h-screen bg-[#02040a] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col overflow-x-hidden">
      <LandingHeader />

      <main className="flex-1 flex flex-col pt-24 pb-20">
        {/* Breadcrumb Navigation */}
        <div className="max-w-7xl mx-auto px-6 w-full pt-4 pb-6">
          <Breadcrumbs
            items={[
              { label: "SPHEREx", href: "/spherex" },
              { label: "Spectral Explorer" },
            ]}
          />
        </div>

        {/* Hero Section */}
        <section className="px-6 py-12 max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-xs font-mono text-cyan-300">
            <SpectralIcon size={20} className="shrink-0" />
            <span>102 CONTIGUOUS INFRARED CHANNELS (0.75 – 5.00 µm)</span>
          </div>

          <h1 className="font-aeruno text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-slate-100 leading-[1.08] [text-wrap:balance]">
            One Universe. 102 Infrared Windows.
          </h1>

          <p className="text-lg text-slate-300 max-w-[65ch] mx-auto leading-relaxed font-light [text-wrap:pretty]">
            Every wavelength reveals distinct physical processes. Explore how SPHEREx splits the infrared cosmos across six detector arrays and 102 narrow spectral windows.
          </p>

          {/* Scientific Disclaimer Pill */}
          <div className="pt-2 flex flex-wrap items-center justify-center gap-4 text-xs font-mono text-slate-400">
            <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
              Detector Mapping: <MathInline math="6\text{ Arrays} \times 17\text{ Bands} = 102\text{ Spectral Channels}" />
            </span>
            <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
              Resolving Power: <MathInline math="R = \lambda/\Delta\lambda \approx 41\text{ (Ch 1–51)}" />, <MathInline math="R \approx 135\text{ (Ch 52–102)}" />
            </span>
          </div>

          {/* Mathematical Definition Equation Callout */}
          <div className="max-w-2xl mx-auto pt-2">
            <MathDisplay
              math="R = \frac{\lambda}{\Delta\lambda} \qquad \lambda = \frac{c}{\nu} \qquad E = h\nu = \frac{hc}{\lambda}"
              label="Spectroscopy Relations"
              caption="Linear Variable Filter spectral resolving power R, electromagnetic wavelength-frequency relation, and photon energy."
            />
          </div>
        </section>

        {/* Interactive 102-Band Scrubber & Spectral Plot */}
        <section className="px-6 py-8 max-w-5xl mx-auto w-full">
          <SpectralBandScrubber />
        </section>

        {/* Detailed Channel Allocation Grid */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-10">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Focal Plane Allocation
              </div>
              <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
                Six Detectors with 17 Channels Each
              </h2>
              <p className="text-sm sm:text-base text-slate-300 max-w-[65ch] leading-relaxed mt-2 [text-wrap:pretty]">
                Each detector array carries an interference filter with a linear thickness gradient. As light enters, each detector column isolates a 17-part spectral division.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                { id: "D1", name: "Array 1 (D1)", span: "0.75 – 1.11 µm", ch: "1 – 17", r: "R ≈ 41", key: "Cosmic optical boundary, Paschen recombination lines" },
                { id: "D2", name: "Array 2 (D2)", span: "1.11 – 1.64 µm", ch: "18 – 34", r: "R ≈ 41", key: "1.6 µm stellar opacity bump, photometric redshifts" },
                { id: "D3", name: "Array 3 (D3)", span: "1.64 – 2.42 µm", ch: "35 – 51", r: "R ≈ 41", key: "Molecular hydrogen H₂ (2.12 µm), Brackett-γ" },
                { id: "D4", name: "Array 4 (D4)", span: "2.42 – 3.82 µm", ch: "52 – 68", r: "R ≈ 135", key: "Water ice (3.05 µm), PAH organics (3.29 µm)" },
                { id: "D5", name: "Array 5 (D5)", span: "3.82 – 4.42 µm", ch: "69 – 85", r: "R ≈ 135", key: "Carbon dioxide ice (4.27 µm), Brackett-α (4.05 µm)" },
                { id: "D6", name: "Array 6 (D6)", span: "4.42 – 5.00 µm", ch: "86 – 102", r: "R ≈ 135", key: "Carbon monoxide ice (4.67 µm), deep continuum" },
              ].map((arr) => (
                <div key={arr.id} className="p-5 rounded-2xl bg-[#040814] border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-cyan-300 text-sm">{arr.id}</span>
                    <span className="text-xs font-mono text-cyan-400 font-semibold">
                      {arr.r}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-100">{arr.name}</h3>
                    <div className="text-xs font-mono text-slate-400 mt-0.5">{arr.span} (Channels {arr.ch})</div>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed [text-wrap:pretty]">
                    {arr.key}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Notable Diagnostic Absorption & Emission Signatures */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#02040a]">
          <div className="max-w-5xl mx-auto space-y-8">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Astrophysical Chemistry
              </div>
              <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
                Primary Diagnostic Spectral Signatures
              </h2>
              <p className="text-sm text-slate-300 max-w-[65ch] leading-relaxed mt-2 [text-wrap:pretty]">
                Specific infrared wavelengths match quantum vibrational states of molecules and atomic recombining transitions in gas. Select a signature to view its astrophysical diagnostic utility:
              </p>
            </div>

            {/* Interactive Feature Table */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              <div className="lg:col-span-7 space-y-2">
                {NOTABLE_LINES.map((feat) => {
                  const isSelected = feat.name === selectedFeature.name;
                  return (
                    <button
                      key={feat.name}
                      onClick={() => setSelectedFeature(feat)}
                      className={`w-full p-3.5 rounded-xl text-left transition-all border flex items-center justify-between ${
                        isSelected
                          ? "bg-cyan-950/80 text-cyan-200 border-cyan-500/50 shadow-sm"
                          : "bg-slate-900/40 text-slate-300 border-slate-800 hover:text-slate-100 hover:bg-slate-800/40"
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="font-bold text-sm text-slate-100">{feat.name}</div>
                        <div className="text-xs font-mono text-slate-400">{feat.chemicalFormula} · {feat.regime}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-sm font-semibold text-cyan-300">{feat.wavelength} µm</div>
                        <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                          feat.spectralType === "Emission" ? "bg-amber-950/60 text-amber-300" : "bg-cyan-950/60 text-cyan-300"
                        }`}>
                          {feat.spectralType}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Detailed Inspector Card */}
              <div className="lg:col-span-5 p-6 rounded-2xl bg-[#040814] border border-slate-800 flex flex-col justify-between space-y-6">
                <div className="space-y-4">
                  <div>
                    <span className="text-xs font-mono text-cyan-400 block uppercase tracking-wider mb-1">
                      {selectedFeature.detector}
                    </span>
                    <h3 className="text-2xl font-bold text-slate-100 [text-wrap:balance]">
                      {selectedFeature.name}
                    </h3>
                    <div className="text-sm font-mono text-cyan-300 mt-1">
                      Wavelength: {selectedFeature.wavelength} µm · {selectedFeature.chemicalFormula}
                    </div>
                  </div>

                  <div className="py-2.5 border-y border-slate-800 text-xs font-mono space-y-1">
                    <span className="text-slate-400 block">Transition Type:</span>
                    <span className="text-slate-100 font-semibold">{selectedFeature.spectralType} Feature</span>
                  </div>

                  <div className="pt-3 border-t border-slate-800/60 text-xs text-slate-300 space-y-1">
                    <span className="font-semibold text-cyan-300 block">Diagnostic Science Utility</span>
                    <p className="text-slate-300 leading-relaxed [text-wrap:pretty]">{selectedFeature.role}</p>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-800">
                  <div className="text-xs font-mono text-slate-400">
                    Provenance Note: Wavelength values reflect laboratory transmission centers and calibrated SPHEREx FITS Level 2 spectral products.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA to Actual Workspace */}
        <section className="px-6 py-16 border-t border-slate-800/80 bg-[#020308] text-center">
          <div className="max-w-3xl mx-auto space-y-6">
            <h2 className="font-aeruno text-3xl sm:text-4xl font-bold text-slate-100 [text-wrap:balance]">
              Open the Operational Spectral Laboratory
            </h2>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-[65ch] mx-auto [text-wrap:pretty]">
              Explore calibrated Level 2 FITS spectral cubes for authentic astronomical targets, measure absorption optical depths, and extract spectral energy distributions.
            </p>
            <div className="flex items-center justify-center pt-2">
              <Link
                href="/workspace?tab=spectral"
                className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-xl text-base font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-md shadow-black/70 group"
              >
                <span>Open Spectral Laboratory →</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
}
