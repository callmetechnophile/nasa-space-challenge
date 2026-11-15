"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, ExternalLink, Calendar, Filter, FileText, CheckCircle2, XCircle, AlertCircle, Bookmark } from "lucide-react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { Breadcrumbs } from "@/components/landing/Breadcrumbs";
import { EvidenceIcon, PlanetIcon, OrbitIcon } from "@/components/visuals/3d-icons";
import { MathInline, MathDisplay } from "@/components/ui/MathView";

type EvidenceCategory = "all" | "hypothesis" | "predicted-parameters" | "candidate" | "non-detection" | "confirmed";

interface TimelineEvent {
  id: string;
  year: number;
  dateStr: string;
  title: string;
  researchers: string;
  publication: string;
  category: "hypothesis" | "predicted-parameters" | "candidate" | "non-detection" | "confirmed";
  observationalMethod: string;
  dataSource: string;
  result: string;
  limitations: string;
  paperUrl?: string;
}

const TIMELINE_EVENTS: TimelineEvent[] = [
  {
    id: "lowell-1906",
    year: 1906,
    dateStr: "1906 – 1915",
    title: "Historical Planet X Hypothesis",
    researchers: "Percival Lowell",
    publication: "Memoirs of the American Academy of Arts and Sciences",
    category: "hypothesis",
    observationalMethod: "Orbital perturbation calculation of Uranus & Neptune",
    dataSource: "19th century optical transit observations",
    result: "Predicted a 7-Earth-mass planet at 43 AU. Prompted the discovery of Pluto in 1930.",
    limitations: "Later disproven in 1993: Voyager 2 radio tracking revealed Neptune was 0.5% less massive than believed; discrepancies were calculational artifacts.",
    paperUrl: "https://science.nasa.gov/solar-system/planet-x/",
  },
  {
    id: "sedna-2003",
    year: 2003,
    dateStr: "Nov 2003",
    title: "Discovery of 90377 Sedna",
    researchers: "Michael Brown, Chad Trujillo, David Rabinowitz",
    publication: "The Astrophysical Journal, 617:645–649",
    category: "candidate",
    observationalMethod: "Wide-field optical search (Samuel Oschin Telescope)",
    dataSource: "Palomar Observatory 48-inch Schmidt Telescope",
    result: "First extreme detached trans-Neptunian object discovered with perihelion at 76 AU, completely decoupled from Neptune.",
    limitations: "Single object; could not determine whether orbit was perturbed by passing star or undiscovered inner Oort cloud population.",
    paperUrl: "https://iopscience.iop.org/article/10.1086/422095",
  },
  {
    id: "trujillo-2014",
    year: 2014,
    dateStr: "Mar 2014",
    title: "Discovery of 2012 VP113 & Argument of Perihelion Clustering",
    researchers: "Chad Trujillo & Scott Sheppard",
    publication: "Nature 507, 471–474",
    category: "hypothesis",
    observationalMethod: "Dark Energy Camera (DECam) wide-field survey",
    dataSource: "NOIRLab Blanco 4-meter Telescope (Chile)",
    result: "Discovered second Sednoid (2012 VP113). Pointed out that all known eTNOs clustered with argument of perihelion ω ≈ 0°.",
    limitations: "Small sample size (12 objects); potential observational selection bias from seasonal observing windows.",
    paperUrl: "https://www.nature.com/articles/nature13156",
  },
  {
    id: "batygin-brown-2016",
    year: 2016,
    dateStr: "Jan 2016",
    title: "Evidence for a Distant Giant Planet in the Solar System",
    researchers: "Konstantin Batygin & Michael E. Brown",
    publication: "The Astronomical Journal, 151:22",
    category: "predicted-parameters",
    observationalMethod: "N-body secular gravitational perturbation simulations",
    dataSource: "Orbits of 6 extreme detached TNOs",
    result: "Formalized the modern 'Planet Nine' hypothesis: predicted ~10 Earth mass planet at a ≈ 700 AU, e ≈ 0.6, inclination i ≈ 30°.",
    limitations: "Purely dynamical model with no direct photons detected. Dependent on physical reality of eTNO alignment.",
    paperUrl: "https://iopscience.iop.org/article/10.3847/0004-6256/151/2/22",
  },
  {
    id: "ossos-bias-2017",
    year: 2017,
    dateStr: "Jun 2017",
    title: "OSSOS Survey Bias Audit (Alternative Interpretation)",
    researchers: "Cory Shankman, Brett Gladman, et al.",
    publication: "The Astronomical Journal, 154:50",
    category: "non-detection",
    observationalMethod: "Rigorous synthetic survey simulator of detection biases",
    dataSource: "Outer Solar System Origins Survey (OSSOS, CFHT)",
    result: "Demonstrated that OSSOS discoveries are fully consistent with an isotropic, random uniform distribution once directional selection bias is modeled.",
    limitations: "OSSOS covered eight specific sky pointings; cannot definitively exclude all clustering in external survey callsets.",
    paperUrl: "https://iopscience.iop.org/article/10.3847/1538-3881/aa7aed",
  },
  {
    id: "wise-limits-2017",
    year: 2017,
    dateStr: "2017 – 2019",
    title: "Archival All-Sky Thermal Infrared Limits",
    researchers: "Kevin Luhman, et al.",
    publication: "The Astrophysical Journal, 781:4",
    category: "non-detection",
    observationalMethod: "All-sky parallax and proper-motion search in W1/W2/W3 bands",
    dataSource: "NASA Wide-field Infrared Survey Explorer (WISE / NEOWISE)",
    result: "Ruled out Saturn-mass objects out to 10,000 AU and Jupiter-mass objects out to 26,000 AU. Constrains Planet Nine to sub-Neptune regimes.",
    limitations: "WISE 12 µm and 22 µm sensitivity drops sharply for bodies cooler than ~40 K and masses below 10 Earth masses.",
    paperUrl: "https://iopscience.iop.org/article/10.1088/0004-637X/781/1/4",
  },
  {
    id: "batygin-2021",
    year: 2021,
    dateStr: "Aug 2021",
    title: "The Orbit of Planet Nine Updated Parameters",
    researchers: "Michael E. Brown & Konstantin Batygin",
    publication: "The Astronomical Journal, 162:219",
    category: "predicted-parameters",
    observationalMethod: "Bayesian orbit estimation incorporating observational bias",
    dataSource: "Expanded sample of detached TNOs",
    result: "Revised parameters: mass closer to 6.2 (+2.2/-1.3) Earth masses, semi-major axis a ≈ 380 (+140/-80) AU, perihelion q ≈ 300 AU.",
    limitations: "Still unconfirmed; predicted location sits closer to the galactic plane where background stellar contamination is dense.",
    paperUrl: "https://iopscience.iop.org/article/10.3847/1538-3881/ac2056",
  },
  {
    id: "rubin-future-2026",
    year: 2026,
    dateStr: "2025 – 2026",
    title: "Legacy Survey of Space and Time (LSST) Search Horizon",
    researchers: "Vera C. Rubin Observatory Collaboration",
    publication: "Astrophysical Journal Supplement Series (LSST Overview)",
    category: "hypothesis",
    observationalMethod: "Deep optical 10-year survey with 3.2-gigapixel camera",
    dataSource: "Simonyi Survey Telescope (Cerro Pachón, Chile)",
    result: "Capable of detecting moving solar system objects down to r ~ 24.5 in single visits and coadded r ~ 27.5, covering ~90% of proposed parameter space.",
    limitations: "Commissioning phase; definitive multi-year search coverage requires multi-epoch cadence.",
    paperUrl: "https://www.lsst.org/",
  },
];

export default function PlanetXEvidencePage() {
  const [activeCategory, setActiveCategory] = useState<EvidenceCategory>("all");

  const filteredEvents =
    activeCategory === "all"
      ? TIMELINE_EVENTS
      : TIMELINE_EVENTS.filter((e) => e.category === activeCategory);

  const getBadgeStyle = (cat: TimelineEvent["category"]) => {
    switch (cat) {
      case "hypothesis":
        return "bg-slate-800 text-slate-300 border-slate-700";
      case "predicted-parameters":
        return "bg-cyan-950/70 text-cyan-300 border-cyan-500/30";
      case "candidate":
        return "bg-amber-950/70 text-amber-300 border-amber-500/30";
      case "non-detection":
        return "bg-rose-950/70 text-rose-300 border-rose-500/30";
      case "confirmed":
        return "bg-emerald-950/70 text-emerald-300 border-emerald-500/30";
    }
  };

  const getCategoryLabel = (cat: TimelineEvent["category"]) => {
    switch (cat) {
      case "hypothesis":
        return "Hypothesis";
      case "predicted-parameters":
        return "Predicted Parameters";
      case "candidate":
        return "Observational Candidate / Object";
      case "non-detection":
        return "Non-Detection / Upper Limit";
      case "confirmed":
        return "Confirmed Discovery (0)";
    }
  };

  return (
    <div className="skytrace-public relative min-h-screen bg-[#02040a] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col overflow-x-hidden">
      <LandingHeader />

      <main className="flex-1 flex flex-col pt-24 pb-20">
        {/* Breadcrumb Navigation */}
        <div className="max-w-7xl mx-auto px-6 w-full pt-4 pb-6">
          <Breadcrumbs
            items={[
              { label: "Planet X", href: "/planet-x" },
              { label: "Evidence & Search" },
            ]}
          />
        </div>

        {/* Hero Section */}
        <section className="px-6 py-12 max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-xs font-mono text-cyan-300">
            <EvidenceIcon size={20} className="shrink-0" />
            <span>OBSERVATIONAL RESEARCH ARCHIVE & PUBLICATION RECORD</span>
          </div>

          <h1 className="font-aeruno text-4xl sm:text-6xl font-bold tracking-tight text-slate-100 leading-[1.08] [text-wrap:balance]">
            Planet Nine: The Scientific Evidence
          </h1>

          <p className="text-lg text-slate-300 max-w-[65ch] mx-auto leading-relaxed font-light [text-wrap:pretty]">
            An authoritative, date-stamped record of peer-reviewed publications, dynamical simulations, non-detection limits, and competing selection bias audits.
          </p>

          {/* Status Alert Banner */}
          <div className="p-4 rounded-xl bg-[#040814] border border-amber-500/30 max-w-2xl mx-auto text-left flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <span className="font-bold text-amber-300 font-mono block">SCIENTIFIC STATUS DEFINITION</span>
              <p className="text-slate-300 leading-relaxed max-w-[65ch] [text-wrap:pretty]">
                The hypothesis remains unproven. In astronomical classification, an object is only considered discovered once it has been directly imaged at multiple epochs, verified by independent teams, and assigned an official designation by the Minor Planet Center (MPC).
              </p>
            </div>
          </div>
        </section>

        {/* Interactive Filter Controls */}
        <section className="px-6 py-6 max-w-5xl mx-auto w-full">
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
            <div className="flex items-center gap-2 text-slate-300">
              <Filter className="w-4 h-4 text-cyan-400" />
              <span>Filter Research Results:</span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { id: "all", label: "All Records (8)" },
                { id: "hypothesis", label: "Hypotheses" },
                { id: "predicted-parameters", label: "Predicted Parameters" },
                { id: "candidate", label: "Observed Objects" },
                { id: "non-detection", label: "Non-Detections / Limits" },
              ].map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => setActiveCategory(filter.id as EvidenceCategory)}
                  className={`px-3 py-1.5 rounded-lg transition-colors border ${
                    activeCategory === filter.id
                      ? "bg-cyan-950/80 text-cyan-200 border-cyan-500/50 shadow-sm"
                      : "bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200"
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Chronological Research Timeline */}
        <section className="px-6 py-8 max-w-5xl mx-auto w-full">
          <div className="mb-8">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
              Peer-Reviewed Record
            </div>
            <h2 className="font-aeruno text-2xl sm:text-4xl font-bold tracking-tight text-slate-100 [text-wrap:balance]">
              Chronological Research Timeline (1906–2026)
            </h2>
            <div className="pt-2">
              <MathDisplay
                math="T^2 = \frac{4\pi^2 a^3}{GM_\odot} \qquad q = a(1 - e) \qquad Q = a(1 + e) \qquad \varpi = \Omega + \omega"
                label="Orbital Parametrization"
                caption="Keplerian orbital dynamics governing semi-major axis a, perihelion q, aphelion Q, and clustered longitude of perihelion ϖ."
              />
            </div>
          </div>

          <div className="space-y-6">
            {filteredEvents.map((event) => (
              <div
                key={event.id}
                className="p-6 rounded-2xl bg-[#030611] border border-slate-800/80 space-y-4 hover:border-slate-700 transition-colors"
              >
                {/* Event Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xs font-mono text-cyan-400 font-bold">{event.dateStr}</span>
                    <span className="text-slate-600">|</span>
                    <span className="text-xs font-mono text-slate-300">{event.researchers}</span>
                  </div>
                  <span className={`text-xs font-mono px-2 py-0.5 rounded border uppercase ${getBadgeStyle(event.category)}`}>
                    {getCategoryLabel(event.category)}
                  </span>
                </div>

                {/* Title & Publication */}
                <div>
                  <h3 className="text-xl font-bold text-slate-100 [text-wrap:balance]">
                    {event.title}
                  </h3>
                  <div className="text-xs font-mono text-slate-400 mt-0.5">
                    Source: {event.publication}
                  </div>
                </div>

                {/* Methods & Sources Grid - flattened */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 py-3 border-y border-slate-800/70 text-xs font-mono">
                  <div>
                    <span className="text-slate-400 block">Method:</span>
                    <span className="text-slate-200">{event.observationalMethod}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Data Instrument:</span>
                    <span className="text-slate-200">{event.dataSource}</span>
                  </div>
                </div>

                {/* Result Description */}
                <div className="text-sm text-slate-300 leading-relaxed max-w-[75ch] [text-wrap:pretty]">
                  <strong className="text-slate-100 font-semibold">Scientific Result:</strong> {event.result}
                </div>

                {/* Limitations */}
                <div className="pt-3 border-t border-slate-800/60 text-xs text-slate-300 space-y-1">
                  <span className="font-semibold text-amber-300 block">Identified Constraints & Limitations</span>
                  <p className="text-slate-300 leading-relaxed max-w-[75ch] [text-wrap:pretty]">{event.limitations}</p>
                </div>

                {/* Paper link if available */}
                {event.paperUrl && (
                  <div className="pt-2 flex items-center justify-end">
                    <a
                      href={event.paperUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-mono text-cyan-400 hover:text-cyan-300 transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Read Publication Archive</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Methodology Summary */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#02040a]">
          <div className="max-w-5xl mx-auto space-y-8">
            <h2 className="font-aeruno text-2xl sm:text-4xl font-bold text-slate-100 [text-wrap:balance]">
              Parallax-Based Candidate Verification
            </h2>

            <div className="p-4 rounded-xl bg-[#040814] border border-cyan-500/20 space-y-2">
              <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 block">
                Orbital Mechanics & Parallax Formulations
              </span>
              <div className="overflow-x-auto py-1">
                <MathDisplay
                  math="T^2 = \frac{4\pi^2 a^3}{GM_\odot} \qquad q = a(1 - e) \qquad Q = a(1 + e) \qquad \varpi = \Omega + \omega"
                  className="text-cyan-200 text-sm sm:text-base text-center"
                />
              </div>
              <div className="overflow-x-auto py-1 border-t border-slate-800/80 pt-2">
                <MathDisplay
                  math="\varpi_{\mathrm{parallax}} = \frac{1\,\mathrm{AU}}{d} \qquad \Delta\theta_{\mathrm{baseline}} \approx \frac{2\,\mathrm{AU}}{d} \approx 1.5'' - 2.5'' \quad (\text{for } d \approx 400\,\mathrm{AU})"
                  className="text-cyan-300 text-xs sm:text-sm text-center"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
              <p>
                Any true planet orbiting between <MathInline math="300" /> and <MathInline math="500\,\mathrm{AU}" /> must exhibit annual parallax motion of approximately <MathInline math="1.5''" /> to <MathInline math="2.5''" /> when observed from opposite sides of Earth&apos;s orbit around the Sun. Fixed background stars and distant quasars do not exhibit this motion.
              </p>
              <p>
                In the SkyTrace Time Domain mode, astronomers execute pixel-level difference imaging across multi-month epochs. Subtracting baseline frames isolates non-zero flux residuals, providing an automated matched-filter pipeline to detect parallax-displaced candidates.
              </p>
            </div>

            <div className="pt-4">
              <Link
                href="/workspace?tab=temporal"
                className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                <span>Launch Time-Domain difference pipeline in SkyTrace →</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
}
