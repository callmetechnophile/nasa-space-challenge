"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight, Menu, X, ChevronDown } from "lucide-react";
import { SkyTraceBrandMark } from "@/components/layout/SkyTraceBrandMark";
import { TelescopeIcon, PlanetIcon, SpectralIcon, CoordinateIcon } from "@/components/visuals/3d-icons";

export function LandingHeader() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [spherexDropdownOpen, setSpherexDropdownOpen] = useState(false);
  const [planetXDropdownOpen, setPlanetXDropdownOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const isSpherexActive = pathname.startsWith("/spherex");
  const isPlanetXActive = pathname.startsWith("/planet-x");
  const isScienceActive = pathname === "/science";
  const isHomeActive = pathname === "/";

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#02040a]/95 backdrop-blur-md border-b border-slate-800/80 py-2.5 shadow-xl"
          : "bg-[#02040a]/70 backdrop-blur-sm py-4 border-b border-slate-900/50"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        {/* Brand identity */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:border-cyan-400/60 transition-colors">
            <SkyTraceBrandMark size={24} />
          </div>
          <div className="flex flex-col">
            <span className="font-corpta text-2xl tracking-wider text-slate-100 group-hover:text-cyan-300 transition-colors">
              SkyTrace
            </span>
          </div>
          <span className="hidden lg:inline-flex items-center gap-1.5 ml-2 px-2.5 py-0.5 rounded-full text-xs font-mono bg-cyan-950/60 border border-cyan-500/20 text-cyan-300">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            SPHEREx Survey
          </span>
        </Link>

        {/* Desktop Navigation links */}
        <nav className="hidden md:flex items-center gap-1 lg:gap-2 text-xs lg:text-sm font-medium text-slate-300">
          {/* Home */}
          <Link
            href="/"
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              isHomeActive
                ? "text-cyan-300 font-semibold bg-cyan-950/40 border border-cyan-500/30"
                : "hover:text-cyan-300 hover:bg-slate-900/40"
            }`}
          >
            Home
          </Link>

          {/* SPHEREx Dropdown */}
          <div
            className="relative"
            onMouseEnter={() => setSpherexDropdownOpen(true)}
            onMouseLeave={() => setSpherexDropdownOpen(false)}
          >
            <Link
              href="/spherex"
              className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg transition-colors ${
                isSpherexActive
                  ? "text-cyan-300 font-semibold bg-cyan-950/40 border border-cyan-500/30"
                  : "hover:text-cyan-300 hover:bg-slate-900/40"
              }`}
            >
              <span>SPHEREx</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </Link>

            {spherexDropdownOpen && (
              <div className="absolute top-full left-0 w-64 pt-2 z-50">
                <div className="rounded-xl border border-slate-800 bg-[#040814] p-2 shadow-2xl space-y-1">
                  <Link
                    href="/spherex"
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-slate-200 hover:bg-slate-900 hover:text-cyan-300 transition-colors"
                  >
                    <TelescopeIcon size={24} className="shrink-0" />
                    <div>
                      <div className="font-semibold text-slate-100">Mission Overview</div>
                      <div className="text-[11px] text-slate-400 font-mono">Infrared all-sky survey</div>
                    </div>
                  </Link>
                  <Link
                    href="/spherex/instrument"
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-slate-200 hover:bg-slate-900 hover:text-cyan-300 transition-colors"
                  >
                    <TelescopeIcon size={24} className="shrink-0" />
                    <div>
                      <div className="font-semibold text-slate-100">Instrument Architecture</div>
                      <div className="text-[11px] text-slate-400 font-mono">Telescope & optics</div>
                    </div>
                  </Link>
                  <Link
                    href="/spherex/spectral-bands"
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-slate-200 hover:bg-slate-900 hover:text-cyan-300 transition-colors"
                  >
                    <SpectralIcon size={24} className="shrink-0" />
                    <div>
                      <div className="font-semibold text-slate-100">Spectral Explorer</div>
                      <div className="text-[11px] text-slate-400 font-mono">102 infrared windows</div>
                    </div>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Planet X Dropdown */}
          <div
            className="relative"
            onMouseEnter={() => setPlanetXDropdownOpen(true)}
            onMouseLeave={() => setPlanetXDropdownOpen(false)}
          >
            <Link
              href="/planet-x"
              className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg transition-colors ${
                isPlanetXActive
                  ? "text-cyan-300 font-semibold bg-cyan-950/40 border border-cyan-500/30"
                  : "hover:text-cyan-300 hover:bg-slate-900/40"
              }`}
            >
              <span>Planet X</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </Link>

            {planetXDropdownOpen && (
              <div className="absolute top-full left-0 w-64 pt-2 z-50">
                <div className="rounded-xl border border-slate-800 bg-[#040814] p-2 shadow-2xl space-y-1">
                  <Link
                    href="/planet-x"
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-slate-200 hover:bg-slate-900 hover:text-cyan-300 transition-colors"
                  >
                    <PlanetIcon size={24} className="shrink-0" />
                    <div>
                      <div className="font-semibold text-slate-100">The Outer Solar System</div>
                      <div className="text-[11px] text-slate-400 font-mono">Hypothesis & orbit</div>
                    </div>
                  </Link>
                  <Link
                    href="/planet-x/evidence"
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-slate-200 hover:bg-slate-900 hover:text-cyan-300 transition-colors"
                  >
                    <PlanetIcon size={24} className="shrink-0" />
                    <div>
                      <div className="font-semibold text-slate-100">Evidence & Search</div>
                      <div className="text-[11px] text-slate-400 font-mono">Observation history & data</div>
                    </div>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Science & Methodology */}
          <Link
            href="/science"
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              isScienceActive
                ? "text-cyan-300 font-semibold bg-cyan-950/40 border border-cyan-500/30"
                : "hover:text-cyan-300 hover:bg-slate-900/40"
            }`}
          >
            Science & Methodology
          </Link>
        </nav>

        {/* Direct Action */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/workspace"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-md shadow-black/60 hover:brightness-105 active:scale-[0.98]"
          >
            <span>Launch Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden p-2 text-slate-300 hover:text-slate-100"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-800 bg-[#040814] px-6 py-5 space-y-4 shadow-2xl">
          <div className="space-y-1">
            <Link
              href="/"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm ${
                isHomeActive ? "text-cyan-300 bg-cyan-950/40 font-semibold" : "text-slate-200"
              }`}
            >
              Home
            </Link>
          </div>

          <div className="border-t border-slate-800/80 pt-3 space-y-1">
            <div className="px-3 text-xs font-mono uppercase tracking-wider text-cyan-400">
              SPHEREx Mission
            </div>
            <Link
              href="/spherex"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm ${
                pathname === "/spherex" ? "text-cyan-300 bg-cyan-950/40 font-semibold" : "text-slate-200"
              }`}
            >
              Mission Overview
            </Link>
            <Link
              href="/spherex/instrument"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm ${
                pathname === "/spherex/instrument" ? "text-cyan-300 bg-cyan-950/40 font-semibold" : "text-slate-200"
              }`}
            >
              Instrument Architecture
            </Link>
            <Link
              href="/spherex/spectral-bands"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm ${
                pathname === "/spherex/spectral-bands" ? "text-cyan-300 bg-cyan-950/40 font-semibold" : "text-slate-200"
              }`}
            >
              Spectral Explorer (102 Bands)
            </Link>
          </div>

          <div className="border-t border-slate-800/80 pt-3 space-y-1">
            <div className="px-3 text-xs font-mono uppercase tracking-wider text-cyan-400">
              Planet X Mystery
            </div>
            <Link
              href="/planet-x"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm ${
                pathname === "/planet-x" ? "text-cyan-300 bg-cyan-950/40 font-semibold" : "text-slate-200"
              }`}
            >
              Outer Solar System & Orbit
            </Link>
            <Link
              href="/planet-x/evidence"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm ${
                pathname === "/planet-x/evidence" ? "text-cyan-300 bg-cyan-950/40 font-semibold" : "text-slate-200"
              }`}
            >
              Evidence & Search History
            </Link>
          </div>

          <div className="border-t border-slate-800/80 pt-3 space-y-1">
            <Link
              href="/science"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-sm ${
                isScienceActive ? "text-cyan-300 bg-cyan-950/40 font-semibold" : "text-slate-200"
              }`}
            >
              Science & Methodology
            </Link>
          </div>

          <div className="pt-3 border-t border-slate-800">
            <Link
              href="/workspace"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-xs font-semibold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all shadow-md"
            >
              <span>Launch Research Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
