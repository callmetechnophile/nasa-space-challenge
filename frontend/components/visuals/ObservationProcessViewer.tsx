"use client";

import React, { useState } from "react";
import { ArrowRight, Layers, Scan, CheckCircle2 } from "lucide-react";

interface StepInfo {
  step: number;
  title: string;
  subtitle: string;
  description: string;
  mechanism: string;
}

const STEPS: StepInfo[] = [
  {
    step: 1,
    title: "1. Pointing at Celestial Target",
    subtitle: "Wide-Field 3.5° × 11.3° Stare",
    description:
      "SPHEREx halts its roll motion and stares at an astronomical field for an exposure duration of approximately 97 seconds. Photons from thousands of stars and background galaxies enter the 20 cm aperture.",
    mechanism: "Spacecraft attitude control locks orientation with sub-arcsecond gyro stability.",
  },
  {
    step: 2,
    title: "2. Linear-Variable Filter (LVF) Dispersion",
    subtitle: "Spatial-Wavelength Gradient Mapping",
    description:
      "Unlike a conventional spectrometer with a narrow slit, SPHEREx mounts Linear Variable Filters directly above the detector arrays. The transmitted wavelength varies continuously across the detector in the dispersion direction.",
    mechanism: "Each physical pixel column on the detector transmits a strictly defined, narrow infrared band.",
  },
  {
    step: 3,
    title: "3. Stepped Small-Angle Slews",
    subtitle: "Translating Sources Across the Filter Gradient",
    description:
      "The spacecraft slews by a calibrated fraction of a degree. In the next exposure, the same astronomical target falls onto a different pixel column—and is therefore measured in a completely different infrared wavelength.",
    mechanism: "Repeated small-angle step repointings shift astronomical sources across all 102 filter bands.",
  },
  {
    step: 4,
    title: "4. Multi-Exposure Spectral Reconstruction",
    subtitle: "Synthesizing Complete 102-Band Spectra",
    description:
      "By combining successive stepped exposures, astronomers extract a full 102-channel infrared spectrum for every resolved source in the field, with resolving power R = 41 to 135.",
    mechanism: "Pipeline performs astrometric registration and extracts calibrated multi-wavelength flux vectors.",
  },
  {
    step: 5,
    title: "5. All-Sky Spectral Map",
    subtitle: "Four Independent All-Sky Surveys in 2 Years",
    description:
      "As Earth orbits the Sun, the observatory precesses along the day/night terminator. In 6 months, SPHEREx completes a full 4π steradian celestial sphere survey, repeating the coverage four times over two years.",
    mechanism: "Creates a 3D spectral data cube containing 450+ million galaxies and 100+ million Milky Way stars.",
  },
];

export function ObservationProcessViewer() {
  const [activeStep, setActiveStep] = useState<number>(1);
  const current = STEPS[activeStep - 1];

  return (
    <div className="w-full border border-slate-800/80 rounded-2xl bg-[#040814]/90 backdrop-blur-sm overflow-hidden shadow-2xl my-8">
      {/* Telemetry bar */}
      <div className="px-6 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4 bg-[#02050f]/90">
        <div className="flex items-center gap-2.5">
          <Scan className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200">
            Observation Mechanics: Slitless Spectroscopy vs Imaging
          </span>
        </div>
        <div className="text-xs font-mono text-cyan-300">
          Step {activeStep} of 5
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[460px]">
        {/* Animated Process Visual SVG */}
        <div className="lg:col-span-7 relative flex items-center justify-center p-8 bg-[#02040a] min-h-[340px]">
          <div className="relative w-full max-w-md h-72 sm:h-80 p-2 flex flex-col justify-between overflow-hidden">
            {/* Stage Visualization Header */}
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 border-b border-slate-800/60 pb-2">
              <span>FOV: 3.5° × 11.3°</span>
              <span className="text-cyan-400 font-semibold">{current.subtitle}</span>
            </div>

            {/* Dynamic Step SVG Scene */}
            <div className="relative flex-1 flex items-center justify-center py-4">
              <svg viewBox="0 0 400 220" className="w-full h-full" role="img" aria-label={`Observation step ${activeStep} diagram`}>
                <defs>
                  {/* Linear Variable Filter Gradient */}
                  <linearGradient id="lvfGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.9" />
                    <stop offset="25%" stopColor="#2dd4bf" stopOpacity="0.9" />
                    <stop offset="50%" stopColor="#a78bfa" stopOpacity="0.9" />
                    <stop offset="75%" stopColor="#f43f5e" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#f97316" stopOpacity="0.9" />
                  </linearGradient>
                </defs>

                {/* Detector grid outline */}
                <rect x="50" y="30" width="300" height="150" rx="8" fill="#0f172a" stroke="#334155" strokeWidth="1.5" />

                {/* LVF Filter coating bands */}
                <rect x="55" y="35" width="290" height="30" rx="4" fill="url(#lvfGrad)" opacity="0.8" />
                <text x="200" y="55" textAnchor="middle" fill="#02040a" fontSize="12" fontFamily="monospace" fontWeight="bold">
                  LINEAR VARIABLE FILTER (0.75 µm → 5.0 µm)
                </text>

                {/* Step specific action visualization */}
                {activeStep === 1 && (
                  <g className="transition-all duration-500">
                    <circle cx="100" cy="120" r="6" fill="#ffffff" />
                    <circle cx="100" cy="120" r="16" stroke="#38bdf8" strokeWidth="1" strokeDasharray="3 3" fill="none" />
                    <line x1="100" y1="65" x2="100" y2="100" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="4 2" />
                    <text x="100" y="150" textAnchor="middle" fill="#38bdf8" fontSize="12" fontFamily="monospace">
                      Target Star (Pos 1)
                    </text>
                  </g>
                )}

                {activeStep === 2 && (
                  <g className="transition-all duration-500">
                    <circle cx="100" cy="120" r="6" fill="#38bdf8" />
                    <text x="100" y="150" textAnchor="middle" fill="#38bdf8" fontSize="12" fontFamily="monospace">
                      λ₁ = 0.92 µm Transmitted
                    </text>
                    <path d="M100,65 L100,110" stroke="#38bdf8" strokeWidth="2" />
                  </g>
                )}

                {activeStep === 3 && (
                  <g className="transition-all duration-500">
                    {/* Previous position faded */}
                    <circle cx="100" cy="120" r="4" fill="#64748b" opacity="0.4" />
                    {/* Slew arrow */}
                    <path d="M115,120 L185,120" stroke="#2dd4bf" strokeWidth="2" markerEnd="url(#arrow)" />
                    {/* New stepped position */}
                    <circle cx="200" cy="120" r="6" fill="#2dd4bf" />
                    <circle cx="200" cy="120" r="16" stroke="#2dd4bf" strokeWidth="1" strokeDasharray="3 3" fill="none" />
                    <text x="200" y="150" textAnchor="middle" fill="#2dd4bf" fontSize="12" fontFamily="monospace">
                      Slew Step: λ₂ = 2.45 µm
                    </text>
                  </g>
                )}

                {activeStep === 4 && (
                  <g className="transition-all duration-500">
                    {/* Multi-point reconstruction curve */}
                    <path
                      d="M 60,130 Q 120,90 180,105 T 260,85 Q 300,120 340,140"
                      fill="none"
                      stroke="url(#lvfGrad)"
                      strokeWidth="3"
                    />
                    <circle cx="100" cy="100" r="4" fill="#38bdf8" />
                    <circle cx="180" cy="105" r="4" fill="#2dd4bf" />
                    <circle cx="260" cy="85" r="4" fill="#a78bfa" />
                    <circle cx="320" cy="130" r="4" fill="#f43f5e" />
                    <text x="200" y="165" textAnchor="middle" fill="#e2e8f0" fontSize="12" fontFamily="monospace">
                      Continuous SED Spectrum Extracted
                    </text>
                  </g>
                )}

                {activeStep === 5 && (
                  <g className="transition-all duration-500">
                    <circle cx="200" cy="110" r="60" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="4 4" fill="none" />
                    <circle cx="200" cy="110" r="40" stroke="#2dd4bf" strokeWidth="1" fill="none" />
                    <ellipse cx="200" cy="110" rx="60" ry="24" stroke="#a78bfa" strokeWidth="1" fill="none" />
                    <text x="200" y="115" textAnchor="middle" fill="#38bdf8" fontSize="12" fontFamily="monospace" fontWeight="bold">
                      ALL-SKY 4π sr
                    </text>
                    <text x="200" y="195" textAnchor="middle" fill="#94a3b8" fontSize="12" fontFamily="monospace">
                      4 Complete Surveys (Every 6 Months)
                    </text>
                  </g>
                )}
              </svg>
            </div>

            {/* Bottom step switcher controls */}
            <div className="flex items-center justify-between border-t border-slate-800/60 pt-2 text-xs font-mono">
              <span className="text-slate-400">Step {activeStep} / 5</span>
              <div className="flex items-center gap-1.5">
                {[1, 2, 3, 4, 5].map((s) => (
                  <button
                    key={s}
                    onClick={() => setActiveStep(s)}
                    className={`w-6 h-6 rounded flex items-center justify-center transition-colors ${
                      s === activeStep
                        ? "bg-cyan-500 text-slate-950 font-bold"
                        : "bg-slate-800 text-slate-400 hover:text-slate-100"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Narrative Description & Imaging vs Spectroscopy Analysis */}
        <div className="lg:col-span-5 p-6 lg:p-8 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-slate-800/80 bg-[#030611]">
          <div className="space-y-4">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Observation Mechanics
              </div>
              <h3 className="text-2xl font-bold text-slate-100 tracking-tight [text-wrap:balance]">
                {current.title}
              </h3>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
              {current.description}
            </p>

            <div className="pl-3.5 border-l-2 border-cyan-500/50 text-xs text-slate-300 space-y-1">
              <span className="font-semibold text-cyan-300 block">Instrument Operation</span>
              <p className="text-slate-300 leading-relaxed [text-wrap:pretty]">{current.mechanism}</p>
            </div>

            {/* Distinction between Imaging & Spectroscopy */}
            <div className="pt-2 border-t border-slate-800/80 text-xs space-y-2">
              <span className="font-semibold text-slate-200 block uppercase font-mono">
                Imaging vs Spectroscopy
              </span>
              <p className="text-slate-300 leading-relaxed [text-wrap:pretty]">
                A conventional astronomical camera collapses all photons into a broad filter channel, answering <em>where</em> light originates. SPHEREx spectroscopy isolates narrow wavelength bins across every spatial pixel, answering <em>what</em> physical processes and chemical bonds produce the emission.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between mt-6">
            <button
              onClick={() => setActiveStep((prev) => (prev % 5) + 1)}
              className="inline-flex items-center gap-2 text-xs font-semibold text-cyan-400 hover:text-cyan-300 group transition-colors"
            >
              <span>Next Observation Phase</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
