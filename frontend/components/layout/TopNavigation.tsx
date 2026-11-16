"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  AudioLines, ChevronDown, Clock3, Compass, Database, Info, Search, ShieldCheck,
} from "lucide-react";
import { useSkyStore } from "@/stores/useSkyStore";
import { StatusPanel } from "@/components/layout/StatusPanel";
import { SkyTraceBrandMark } from "@/components/layout/SkyTraceBrandMark";
import { CameraTelemetry } from "@/components/celestial/CameraController";
import { ProvenanceState } from "@/types/astronomy";

const navItems = [
  { id: "sky" as const, label: "Sky Explorer", shortcut: "⌘1", icon: Compass },
  { id: "temporal" as const, label: "Time Domain", shortcut: "⌘2", icon: Clock3 },
  { id: "spectral" as const, label: "Spectral Lab", shortcut: "⌘3", icon: AudioLines },
  { id: "targets" as const, label: "Targets", shortcut: "⌘4", icon: ShieldCheck },
];

export interface TopNavigationProps {
  telemetry?: CameraTelemetry | null;
  starCount?: number;
  targetCoords?: { ra: number; dec: number } | null;
  provenanceState?: ProvenanceState;
}

export function TopNavigation({
  telemetry = null,
  starCount = 4500,
  targetCoords = null,
  provenanceState = "SYNTHETIC_DEMO",
}: TopNavigationProps = {}) {
  const activeTab = useSkyStore((s) => s.activeTab);
  const setActiveTab = useSkyStore((s) => s.setActiveTab);
  const [searchOpen, setSearchOpen] = useState(false);
  const [statusOpen, setStatusOpen] = useState(false);

  const statusContainerRef = useRef<HTMLDivElement>(null);
  const statusButtonRef = useRef<HTMLButtonElement>(null);

  // Keyboard navigation & global shortcuts
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
      if (event.key === "Escape") {
        if (searchOpen) setSearchOpen(false);
        if (statusOpen) {
          setStatusOpen(false);
          statusButtonRef.current?.focus();
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [searchOpen, statusOpen]);

  // Click outside listener for the status popover
  useEffect(() => {
    if (!statusOpen) return;

    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (
        statusContainerRef.current &&
        !statusContainerRef.current.contains(event.target as Node)
      ) {
        setStatusOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
    };
  }, [statusOpen]);

  return (
    <header className="astro-titlebar">
      <div className="astro-brand">
        {/* Single interactive Home link containing custom brand mark and wordmark */}
        <Link
          href="/"
          className="astro-brand-link"
          aria-label="SkyTrace Home"
          title="SkyTrace Home"
        >
          <div className="astro-brand-mark">
            <SkyTraceBrandMark size={24} />
          </div>
          <span className="astro-brand-name font-corpta tracking-wider text-sm">
            SkyTrace
          </span>
        </Link>

        <span className="astro-title-divider" />

        {/* Independent workspace/project selector button */}
        <button
          type="button"
          className="astro-project-switch"
          onClick={() => setActiveTab("sky")}
          title="Switch to Sky Explorer workspace"
          aria-label="Switch to Sky Explorer workspace"
        >
          <span>skytrace</span> <ChevronDown size={12} />
        </button>
      </div>

      <button className="astro-command-search" onClick={() => setSearchOpen((v) => !v)}>
        <Search size={13} />
        <span>Open a workspace or command</span>
        <kbd>⌘ K</kbd>
      </button>

      <div className="astro-title-actions">
        {/* Clickable STATUS control and anchored Telemetry popover */}
        <div className="astro-status-container" ref={statusContainerRef}>
          <button
            ref={statusButtonRef}
            type="button"
            onClick={() => setStatusOpen((v) => !v)}
            className={`astro-status-trigger ${statusOpen ? "active" : ""}`}
            aria-expanded={statusOpen}
            aria-haspopup="dialog"
            aria-controls="telemetry-popover"
            aria-label="System status and telemetry"
            title="System status & telemetry"
          >
            <span className="astro-status-dot" aria-hidden="true" />
            <span className="astro-status-label">STATUS</span>
            <ChevronDown
              size={11}
              className={`astro-status-chevron ${statusOpen ? "open" : ""}`}
            />
          </button>

          {statusOpen && (
            <div
              id="telemetry-popover"
              role="dialog"
              aria-label="System Status & Telemetry"
              className="astro-status-popover"
            >
              <StatusPanel
                telemetry={telemetry}
                starCount={starCount}
                targetCoords={targetCoords}
                provenanceState={provenanceState}
                onClose={() => {
                  setStatusOpen(false);
                  statusButtonRef.current?.focus();
                }}
              />
            </div>
          )}
        </div>

        <span className="astro-title-divider" />
        <button
          className="astro-title-icon"
          title="Mission information"
          onClick={() => setActiveTab(activeTab === "about" ? "sky" : "about")}
        >
          <Info size={15} />
        </button>
      </div>

      {searchOpen && (
        <div className="astro-quick-menu">
          <div className="astro-quick-title">OPEN WORKSPACE</div>
          {navItems.map(({ id, label, shortcut, icon: Icon }) => (
            <button
              key={id}
              onClick={() => {
                setActiveTab(id);
                setSearchOpen(false);
              }}
            >
              <Icon size={14} />
              <span>{label}</span>
              <kbd>{shortcut}</kbd>
            </button>
          ))}
          <div className="astro-quick-note">
            Coordinate search is available in the Explorer panel.
          </div>
        </div>
      )}
    </header>
  );
}

export function AstroWorkspaceTabs() {
  const activeTab = useSkyStore((s) => s.activeTab);
  const setActiveTab = useSkyStore((s) => s.setActiveTab);
  return (
    <nav className="astro-workspace-tabs" aria-label="Scientific workspaces">
      {navItems.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          className={
            activeTab === id
              ? "astro-workspace-tab active"
              : "astro-workspace-tab"
          }
          onClick={() => setActiveTab(id)}
        >
          <Icon size={13} />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}
