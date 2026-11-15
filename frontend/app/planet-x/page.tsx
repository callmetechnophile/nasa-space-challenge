"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, ExternalLink, AlertTriangle, Telescope, HelpCircle, Compass, Search } from "lucide-react";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { Breadcrumbs } from "@/components/landing/Breadcrumbs";
import { SolarSystemViewer } from "@/components/visuals/SolarSystemViewer";
import { PlanetIcon, OrbitIcon, EvidenceIcon } from "@/components/visuals/3d-icons";
import { MathInline, MathDisplay } from "@/components/ui/MathView";

export default function PlanetXPage() {
  return (
    <div className="skytrace-public relative min-h-screen bg-[#02040a] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col overflow-x-hidden">
      <LandingHeader />

      <main className="flex-1 flex flex-col pt-24 pb-20">
        {/* Breadcrumb Navigation */}
        <div className="max-w-7xl mx-auto px-6 w-full pt-4 pb-6">
          <Breadcrumbs items={[{ label: "Planet X / Planet Nine" }]} />
        </div>

        {/* Hero Section */}
        <section className="px-6 py-12 md:py-16 max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-rose-950/40 border border-rose-500/30 text-xs font-mono text-rose-300">
            <PlanetIcon size={20} className="shrink-0" />
            <span>UNRESOLVED DYNAMICAL HYPOTHESIS · STATUS: NOT CONFIRMED</span>
          </div>

          <h1 className="font-aeruno text-4xl sm:text-6xl lg:text-7xl font-bold tracking-normal text-slate-100 leading-[1.08] [text-wrap:balance]">
            A World Beyond Neptune?
          </h1>

          <p className="text-lg sm:text-xl text-slate-300 max-w-[65ch] mx-auto leading-relaxed font-light [text-wrap:pretty]">
            At the edge of the Solar System, orbital patterns have raised a question that astronomers are still investigating: could an undiscovered planet be shaping the distant outer Solar System?
          </p>

          {/* Prominent Scientific Status Label */}
          <div className="pt-2 flex flex-wrap items-center justify-center gap-4 text-xs font-mono">
            <span className="px-3 py-1 rounded bg-amber-950/60 border border-amber-500/30 text-amber-300 font-bold">
              HYPOTHESIS — NOT CONFIRMED
            </span>
            <span className="text-slate-400">
              Predicted mass: <MathInline math="M \sim 5 - 10\,M_{\oplus}" /> · Semi-major axis: <MathInline math="a \sim 300 - 500\,\mathrm{AU}" />
            </span>
          </div>
        </section>

        {/* Section A: What Is Planet X? */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Section A · Scientific Clarification & History
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-normal text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              Distinguishing Historical Planet X from Modern Planet Nine
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-slate-300 leading-relaxed text-sm sm:text-base [text-wrap:pretty]">
              <p>
                In the early 20th century, astronomer Percival Lowell popularized the term <strong>Planet X</strong> to explain apparent discrepancies in the orbits of Uranus and Neptune. When Clyde Tombaugh discovered Pluto in 1930, it was initially hailed as Planet X, though later proven far too small. In 1993, data from Voyager 2 revised Neptune’s mass, eliminating the purported discrepancies and concluding Lowell's specific Planet X search was based on measurement artifacts.
              </p>
              <p>
                The modern <strong>Planet Nine hypothesis</strong>, proposed in 2016 by Konstantin Batygin and Michael Brown at Caltech, is fundamentally different. It is not based on planetary positions, but on the strange, non-random clustering of orbits observed among extreme trans-Neptunian objects (eTNOs) orbiting hundreds of astronomical units beyond Neptune. Its existence remains purely hypothetical and unconfirmed by direct observation.
              </p>
            </div>
          </div>
        </section>

        {/* Section B: Interactive 3D Solar System Beyond Neptune */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#02040a]">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Section B · Interactive Orbital Geometry
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-normal text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              The Solar System Beyond Neptune
            </h2>
            <p className="text-sm sm:text-base text-slate-300 max-w-[65ch] leading-relaxed [text-wrap:pretty]">
              Explore the known planets (Earth to Neptune), the doughnut-shaped Kuiper Belt, and the eccentric orbits of extreme trans-Neptunian objects like Sedna. Toggle the hypothetical Planet Nine orbit to inspect how an inclined, eccentric body could gravitationally shepherd these distant icy worlds.
            </p>

            {/* Interactive 3D Solar System Viewport */}
            <SolarSystemViewer />
          </div>
        </section>

        {/* Section C: Why Do Astronomers Suspect It? */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Section C · Dynamical Motivation & Caveats
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-normal text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              Why Do Astronomers Suspect It?
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-slate-300 leading-relaxed text-sm sm:text-base [text-wrap:pretty]">
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-slate-100 [text-wrap:balance]">
                  The Observational Evidence for Clustering
                </h3>
                <p>
                  Extreme trans-Neptunian objects have semi-major axes <MathInline math="a > 150\,\mathrm{AU}" /> and perihelia well beyond Neptune’s gravitational reach (<MathInline math="q > 30\,\mathrm{AU}" />). If distributed randomly, their orbits should point in all directions evenly.
                </p>
                <p>
                  Instead, a subset of detached eTNOs share closely aligned arguments of perihelion (<MathInline math="\varpi" />) and orbital planes. Batygin &amp; Brown demonstrated that a massive outer planet orbiting eccentrically and anti-aligned to these TNOs could gravitationally maintain this alignment over billions of years through secular resonance.
                </p>
              </div>

              <div className="space-y-4">
                <h3 className="text-xl font-bold text-slate-100 [text-wrap:balance]">
                  Alternative Explanations & Observational Bias
                </h3>
                <p>
                  Not all astrophysicists accept the Planet Nine interpretation. Prominent researchers (such as Shankman et al. with the Outer Solar System Origins Survey - OSSOS) argue that the apparent clustering may be an illusion caused by <strong>observational selection bias</strong>: telescopes in the northern hemisphere can only survey during clear winter skies along specific galactic coordinates.
                </p>
                <p>
                  Other competing dynamical theories propose a collective self-gravity model from a massive primordial disc of icy debris, or statistical anomalies in small sample sizes (<MathInline math="N < 20" /> objects).
                </p>
              </div>
            </div>

            {/* Orbital Mechanics & Inverse-Square Law Equation Callout */}
            <div className="pt-4 max-w-3xl mx-auto">
              <MathDisplay
                math="T^2 = \frac{4\pi^2 a^3}{GM_\odot} \qquad F = \frac{L_\odot A p}{16\pi^2 r^2 \Delta^2} \propto \frac{1}{r^4}"
                label="Orbital Period & Flux Drop"
                caption="Kepler's Third Law governing orbital period T at semi-major axis a, and the 1/r⁴ reflected solar flux fall-off at extreme distances."
              />
            </div>
          </div>
        </section>

        {/* Section D: How Could We Find It? */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#02040a]">
          <div className="max-w-5xl mx-auto space-y-8">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Section D · Observational Challenges
              </div>
              <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-normal text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
                How Could We Find It?
              </h2>
              <p className="text-sm text-slate-300 max-w-[65ch] leading-relaxed mt-2 [text-wrap:pretty]">
                Detecting a planet at <MathInline math="400\,\mathrm{AU}" /> is an extraordinary observational challenge. At this distance, reflected sunlight drops as <MathInline math="1/r^4" />, making the body roughly 10,000 times dimmer than Pluto.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="p-5 rounded-xl bg-[#040814] border border-slate-800 space-y-3">
                <div className="text-xs font-mono text-cyan-400">THERMAL INFRARED</div>
                <h3 className="text-lg font-bold text-slate-100">Thermal Emission Surveys</h3>
                <p className="text-xs text-slate-300 leading-relaxed [text-wrap:pretty]">
                  While sunlight reflection is faint, an internal heat source from planetary contraction emits thermal infrared light. All-sky infrared archives from WISE and NEOWISE rule out Saturn- or Jupiter-mass bodies at these distances, constraining Planet Nine to the sub-Neptune regime (5–10 Earth masses).
                </p>
              </div>

              <div className="p-5 rounded-xl bg-[#040814] border border-slate-800 space-y-3">
                <div className="text-xs font-mono text-cyan-400">OPTICAL SURVEYS</div>
                <h3 className="text-lg font-bold text-slate-100">Subaru Hyper Suprime-Cam</h3>
                <p className="text-xs text-slate-300 leading-relaxed [text-wrap:pretty]">
                  The 8.2-meter Subaru Telescope atop Mauna Kea has conducted targeted deep optical searches along the predicted Planet Nine orbital path, ruling out portions of the orbital trajectory down to visual magnitude $V \sim 25$.
                </p>
              </div>

              <div className="p-5 rounded-xl bg-[#040814] border border-slate-800 space-y-3">
                <div className="text-xs font-mono text-cyan-400">NEXT-GEN DISCOVERY</div>
                <h3 className="text-lg font-bold text-slate-100">Vera C. Rubin Observatory</h3>
                <p className="text-xs text-slate-300 leading-relaxed [text-wrap:pretty]">
                  The Legacy Survey of Space and Time (LSST) at Vera C. Rubin Observatory will survey the entire visible southern sky every few nights with a 3.2-gigapixel camera, capable of either detecting Planet Nine through apparent parallax motion or ruling it out across most parameter space.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Section E: Evidence and Uncertainty Timeline Preview */}
        <section className="px-6 py-16 border-t border-slate-900/80 bg-[#030611]">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Section E · Evidence & Scientific Caution
            </div>
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold tracking-normal text-slate-100 max-w-3xl leading-[1.12] [text-wrap:balance]">
              A Hypothesis Is Not a Discovery
            </h2>
            <p className="text-sm sm:text-base text-slate-300 max-w-[65ch] leading-relaxed [text-wrap:pretty]">
              Until an actual object is imaged directly and its orbital parameters confirmed by independent observatories, Planet Nine remains a mathematical model. Science proceeds by testing hypotheses against evidence, not by assuming existence.
            </p>

            <div className="p-6 rounded-2xl bg-[#02040a] border border-amber-500/20 space-y-3 text-xs font-mono">
              <div className="flex items-center gap-2 text-amber-300 font-bold">
                <AlertTriangle className="w-4 h-4" />
                <span>SCIENTIFIC VERDICT: UNCONFIRMED HYPOTHESIS</span>
              </div>
              <p className="text-slate-300 leading-relaxed [text-wrap:pretty]">
                Neither NASA, JPL, the International Astronomical Union (IAU), nor the peer-reviewed astronomical community has confirmed the existence of Planet Nine. No direct optical, infrared, or radio detection has occurred.
              </p>
            </div>
          </div>
        </section>

        {/* Section F: The Search Continues (CTA) */}
        <section className="px-6 py-16 border-t border-slate-800/80 bg-[#020308] text-center">
          <div className="max-w-3xl mx-auto space-y-6">
            <h2 className="font-aeruno text-3xl sm:text-5xl font-bold text-slate-100 [text-wrap:balance]">
              A hypothesis is not a discovery. It is a question worth testing.
            </h2>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-[65ch] mx-auto [text-wrap:pretty]">
              Inspect the peer-reviewed research papers, examine the archival search limits from WISE, and explore the complete observational timeline.
            </p>
            <div className="flex items-center justify-center pt-2">
              <Link
                href="/planet-x/evidence"
                className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-xl text-base font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-md shadow-black/70 group"
              >
                <span>Explore the scientific evidence →</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <LandingFooter />
    </div>
  );
}
