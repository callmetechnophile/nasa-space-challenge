"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Compass, Clock3, AudioLines, ShieldCheck, Layers, Eye, Activity, Cpu } from "lucide-react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { Breadcrumbs } from "@/components/landing/Breadcrumbs";
import { CoordinateIcon, SpectralIcon, TelescopeIcon, DetectorIcon, EvidenceIcon } from "@/components/visuals/3d-icons";
import { MathInline, MathDisplay } from "@/components/ui/MathView";

interface ConceptCard {
  id: string;
  category: string;
  title: string;
  subtitle: React.ReactNode;
  conceptDescription: React.ReactNode;
  equation: string;
  astronomyApplication: React.ReactNode;
  workspaceLinkText: string;
  workspaceHref: string;
}

const CONCEPTS: ConceptCard[] = [
  {
    id: "coordinates",
    category: "Astrometry & Positioning",
    title: "Celestial Coordinates & WCS",
    subtitle: (
      <span>
        Right Ascension (<MathInline math="\alpha" />) and Declination (<MathInline math="\delta" />)
      </span>
    ),
    conceptDescription: (
      <span>
        Astronomers project positions on the sky using equatorial coordinates tied to Earth&apos;s equator and equinoxes. The International Celestial Reference System (ICRS) defines these axes with microarcsecond precision.
      </span>
    ),
    equation: "\\begin{pmatrix} \\xi \\\\ \\eta \\end{pmatrix} = \\begin{pmatrix} \\mathrm{CD}_{1,1} & \\mathrm{CD}_{1,2} \\\\ \\mathrm{CD}_{2,1} & \\mathrm{CD}_{2,2} \\end{pmatrix} \\begin{pmatrix} x - x_0 \\\\ y - y_0 \\end{pmatrix}",
    astronomyApplication: (
      <span>
        The World Coordinate System (WCS) FITS standard translates physical detector pixel coordinates <MathInline math="(x, y)" /> into celestial coordinates <MathInline math="(\alpha, \delta)" /> using tangential gnomonic projections (<MathInline math="\mathrm{TAN}" />) and CD astrometric transformation matrices with sub-pixel closure.
      </span>
    ),
    workspaceLinkText: "Explore Celestial Coordinates in Sky Explorer",
    workspaceHref: "/workspace?tab=sky",
  },
  {
    id: "spectroscopy",
    category: "Physical Chemistry",
    title: "Infrared Spectroscopy & Bandpasses",
    subtitle: (
      <span>
        Resolving Power <MathInline math="R = \lambda / \Delta\lambda" /> across 102 Channels
      </span>
    ),
    conceptDescription: (
      <span>
        While an image measures light intensity integrated across a broad filter, a spectrum decomposes photons into discrete wavelength intervals. Spectral features correspond to molecular vibrations and atomic transitions.
      </span>
    ),
    equation: "\\lambda = \\frac{c}{\\nu} \\qquad E = h\\nu = \\frac{hc}{\\lambda} \\qquad R = \\frac{\\lambda}{\\Delta\\lambda}",
    astronomyApplication: (
      <span>
        SPHEREx samples 102 contiguous channels between <MathInline math="0.75" /> and <MathInline math="5.00\,\mu\mathrm{m}" /> with resolving power <MathInline math="R \approx 41" /> (near-IR) to <MathInline math="R \approx 135" /> (mid-IR), mapping water ice (<MathInline math="3.05\,\mu\mathrm{m}" />), PAH organics (<MathInline math="3.29\,\mu\mathrm{m}" />), and <MathInline math="\mathrm{CO}_2" /> ice (<MathInline math="4.27\,\mu\mathrm{m}" />).
      </span>
    ),
    workspaceLinkText: "Inspect 102 Spectral Bands in Spectral Lab",
    workspaceHref: "/workspace?tab=spectral",
  },
  {
    id: "difference-imaging",
    category: "Time Domain",
    title: "Temporal Difference Imaging",
    subtitle: (
      <span>
        Subtractive Astrometry (<MathInline math="D = I_{\mathrm{search}} - I_{\mathrm{ref}}" />)
      </span>
    ),
    conceptDescription: (
      <span>
        To discover transient events (supernovae, variable stars, fast-moving asteroids) amidst millions of static background stars, astronomers subtract a calibrated reference observation from a search epoch.
      </span>
    ),
    equation: "D(x,y) = I_{\\mathrm{search}}(x,y) - I_{\\mathrm{ref}}(x,y) \\qquad \\sigma_D^2 = \\sigma_{\\mathrm{search}}^2 + \\sigma_{\\mathrm{ref}}^2",
    astronomyApplication: (
      <span>
        SkyTrace aligns multi-epoch FITS frames with sub-pixel WCS registration, subtracts background variance, and generates clean residual difference images <MathInline math="D(x,y)" /> where invariant stars vanish and high proper motion sources stand out.
      </span>
    ),
    workspaceLinkText: "Launch Difference Engine in Time Domain",
    workspaceHref: "/workspace?tab=temporal",
  },
  {
    id: "snr",
    category: "Signal Processing",
    title: "Signal-to-Noise Ratio (SNR)",
    subtitle: "Matched-Filter Detection & Native ePSF",
    conceptDescription: (
      <span>
        The statistical significance of an astronomical source measures whether a flux peak is an authentic physical signal or a random noise fluctuation. A standard <MathInline math="5\sigma" /> threshold corresponds to a false-positive probability of <MathInline math="3 \\times 10^{-7}" />.
      </span>
    ),
    equation: "\\mathrm{SNR} = F \\sqrt{\\sum_{i} \\frac{P_i^2}{V_i}} \\ge 5\\sigma",
    astronomyApplication: (
      <span>
        Convolving difference images with the detector-position effective Point Spread Function (<MathInline math="P_i" />) against local pixel variance (<MathInline math="V_i" />) achieves optimal matched-filter significance, delivering rigorous statistical validation.
      </span>
    ),
    workspaceLinkText: "Verify Point Source SNR in Target Lab",
    workspaceHref: "/workspace?tab=targets",
  },
  {
    id: "photometry",
    category: "Quantitative Optics",
    title: "Infrared Photometry & Flux Calibration",
    subtitle: "Aperture Integration vs Point Spread Function Fitting",
    conceptDescription: (
      <span>
        Photometry quantifies the flux density of celestial bodies in physical units (MegaJanskys per steradian or Janskys). Precise calibration accounts for detector gain, non-linearity, and thermal dark current.
      </span>
    ),
    equation: "m = -2.5 \\log_{10}(F) + \\mathrm{ZP} \\qquad F = \\int_{\\Omega} I_\\nu \\, d\\Omega",
    astronomyApplication: (
      <span>
        Calibrated SPHEREx Level 2 products provide variance and flag arrays per pixel in <MathInline math="\\mathrm{MJy}/\\mathrm{sr}" />, isolating cosmic ray hits, dead pixels, and saturation trails before photometric extraction.
      </span>
    ),
    workspaceLinkText: "Inspect FITS Headers & Calibration",
    workspaceHref: "/workspace?tab=sky",
  },
  {
    id: "provenance",
    category: "Scientific Integrity",
    title: "Observation Provenance & Reproducibility",
    subtitle: "End-to-End Cryptographic & Archival Traceability",
    conceptDescription: (
      <span>
        Scientific credibility requires that every data point can be traced back to its raw instrument telemetry, pipeline calibration version, and exact UTC observation timestamp without data fabrication.
      </span>
    ),
    equation: "\\Delta\\theta = \\sqrt{(\\Delta\\alpha \\cos\\delta)^2 + (\\Delta\\delta)^2} < 0.05''",
    astronomyApplication: (
      <span>
        Every cutout, spectrum, and difference image in SkyTrace displays its authentic FITS header metadata, IRSA origin, DATE-OBS epoch, and software pipeline commit SHA with astrometric precision <MathInline math="\\Delta\\theta < 0.05''" />.
      </span>
    ),
    workspaceLinkText: "View Target Provenance in Workspace",
    workspaceHref: "/workspace?tab=targets",
  },
];

export default function ScienceMethodologyPage() {
  return (
    <div className="skytrace-public relative min-h-screen bg-[#02040a] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col overflow-x-hidden">
      <LandingHeader />

      <main className="flex-1 flex flex-col pt-24 pb-20">
        {/* Breadcrumb Navigation */}
        <div className="max-w-7xl mx-auto px-6 w-full pt-4 pb-6">
          <Breadcrumbs items={[{ label: "Science & Methodology" }]} />
        </div>

        {/* Hero Section */}
        <section className="px-6 py-12 md:py-16 max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-xs font-mono text-cyan-300">
            <CoordinateIcon size={20} className="shrink-0" />
            <span>ASTRONOMICAL METHODS & OBSERVATIONAL PHYSICS</span>
          </div>

          <h1 className="font-aeruno text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-slate-100 leading-[1.08] [text-wrap:balance]">
            Science &amp; Methodology
          </h1>

          <p className="text-lg sm:text-xl text-slate-300 max-w-[65ch] mx-auto leading-relaxed font-light [text-wrap:pretty]">
            The principles of astronomical observation, from coordinate geometry and linear variable filter spectroscopy to difference imaging and statistical signal verification.
          </p>

          <div className="pt-2 flex flex-wrap items-center justify-center gap-4 text-xs font-mono text-slate-400">
            <span>Every concept connects directly to an operational analysis mode in the SkyTrace Workspace.</span>
          </div>
        </section>

        {/* Concept Grid Connecting to Workspace Tools */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-12">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Core Foundations
              </div>
              <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-tight text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
                How Modern Astronomy Decodes the Sky
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {CONCEPTS.map((concept) => (
                <div
                  key={concept.id}
                  className="p-6 rounded-2xl bg-[#040814] border border-slate-800 space-y-5 flex flex-col justify-between hover:border-slate-700 transition-colors"
                >
                  <div className="space-y-4">
                    <div>
                      <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 block mb-1">
                        {concept.category}
                      </span>
                      <h3 className="text-2xl font-bold text-slate-100 [text-wrap:balance]">
                        {concept.title}
                      </h3>
                      <div className="text-xs font-mono text-slate-400 mt-1">{concept.subtitle}</div>
                    </div>

                    <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
                      {concept.conceptDescription}
                    </p>

                    <div className="overflow-x-auto py-2 text-cyan-200 text-center">
                      <MathDisplay
                        math={concept.equation}
                        className="text-xs sm:text-sm inline-block"
                      />
                    </div>

                    <div className="pt-3 border-t border-slate-800/60 text-xs text-slate-300 space-y-1">
                      <span className="font-semibold text-cyan-300 block">Observational Application</span>
                      <p className="text-slate-300 leading-relaxed [text-wrap:pretty]">{concept.astronomyApplication}</p>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-800">
                    <Link
                      href={concept.workspaceHref}
                      className="inline-flex items-center gap-2 text-xs font-semibold text-cyan-400 hover:text-cyan-300 group transition-colors"
                    >
                      <span>{concept.workspaceLinkText}</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Synthesis CTA */}
        <section className="px-6 py-16 border-t border-slate-800/80 bg-[#020308] text-center">
          <div className="max-w-3xl mx-auto space-y-6">
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold text-slate-100 [text-wrap:balance]">
              Move from Theory to Investigation
            </h2>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-[65ch] mx-auto [text-wrap:pretty]">
              Launch the research environment to apply these methodologies directly to calibrated SPHEREx FITS Level 2 survey observations.
            </p>
            <div className="flex items-center justify-center pt-2">
              <Link
                href="/workspace"
                className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-xl text-base font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-md shadow-black/70 group"
              >
                <span>Launch SkyTrace Workspace →</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
}
