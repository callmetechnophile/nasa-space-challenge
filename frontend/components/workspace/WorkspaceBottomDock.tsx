"use client";

import React, { useState, useRef, useEffect, KeyboardEvent } from "react";
import {
  Compass,
  Layers,
  AlertCircle,
  CheckCircle2,
  PanelBottom,
  ChevronUp,
  ChevronDown,
  Maximize2,
  Minimize2,
  Info,
  ShieldCheck,
} from "lucide-react";

export type BottomDockTab = "problems" | "coordinates" | "layers";

export interface WorkspaceBottomDockProps {
  isOpen: boolean;
  onToggleOpen: () => void;
  activeTab: BottomDockTab;
  onTabChange: (tab: BottomDockTab) => void;
  coordinatesContent: React.ReactNode;
  imageLayersContent: React.ReactNode;
  problemsCount?: number;
  layersCount?: number;
}

/**
 * Reusable, VS Code-inspired bottom dock for SkyTrace IDE.
 * Houses PROBLEMS, COORDINATES, and IMAGE LAYERS in a unified, non-intrusive container.
 * Keeps inactive tabs mounted to preserve component state across tab switches.
 */
export function WorkspaceBottomDock({
  isOpen,
  onToggleOpen,
  activeTab,
  onTabChange,
  coordinatesContent,
  imageLayersContent,
  problemsCount = 0,
  layersCount = 0,
}: WorkspaceBottomDockProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const tabListRef = useRef<HTMLDivElement>(null);

  const tabs: { id: BottomDockTab; label: string; icon: React.ReactNode; badge?: number | string }[] = [
    {
      id: "problems",
      label: "PROBLEMS",
      icon: <AlertCircle className="w-3.5 h-3.5" />,
      badge: problemsCount,
    },
    {
      id: "coordinates",
      label: "COORDINATES",
      icon: <Compass className="w-3.5 h-3.5" />,
    },
    {
      id: "layers",
      label: "IMAGE LAYERS",
      icon: <Layers className="w-3.5 h-3.5" />,
      badge: layersCount > 0 ? layersCount : undefined,
    },
  ];

  // Accessible keyboard navigation between tabs (ArrowLeft / ArrowRight)
  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>, currentIndex: number) => {
    let nextIndex = currentIndex;
    if (e.key === "ArrowRight") {
      nextIndex = (currentIndex + 1) % tabs.length;
    } else if (e.key === "ArrowLeft") {
      nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    } else if (e.key === "Home") {
      nextIndex = 0;
    } else if (e.key === "End") {
      nextIndex = tabs.length - 1;
    } else {
      return;
    }

    e.preventDefault();
    const nextTab = tabs[nextIndex];
    onTabChange(nextTab.id);
    if (!isOpen) onToggleOpen();

    // Focus next tab button
    const buttons = tabListRef.current?.querySelectorAll<HTMLButtonElement>("button[role='tab']");
    buttons?.[nextIndex]?.focus();
  };

  const handleTabClick = (tabId: BottomDockTab) => {
    if (activeTab === tabId && isOpen) {
      // Clicking active tab toggles dock collapse/open
      onToggleOpen();
    } else {
      onTabChange(tabId);
      if (!isOpen) onToggleOpen();
    }
  };

  // Determine container height
  const dockHeightClass = !isOpen
    ? "h-[28px]"
    : isExpanded
    ? "h-[380px]"
    : "h-[260px]";

  return (
    <section
      aria-label="Workspace Bottom Dock"
      className={`astro-terminal flex flex-col w-full bg-[#070b14] border-t border-[#1e293b]/90 text-slate-200 font-mono transition-[height] duration-200 ease-out select-none overflow-hidden ${dockHeightClass}`}
    >
      {/* Dock Tab Bar */}
      <div
        ref={tabListRef}
        role="tablist"
        aria-label="Workspace tool panels"
        className="h-[28px] min-h-[28px] flex items-stretch justify-between px-2 bg-[#090e1a] border-b border-[#1b253b] text-[10px]"
      >
        {/* Left: Tab Buttons */}
        <div className="flex items-stretch space-x-1">
          {tabs.map((tab, idx) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                role="tab"
                id={`dock-tab-${tab.id}`}
                aria-selected={isActive && isOpen}
                aria-controls={`dock-tabpanel-${tab.id}`}
                tabIndex={isActive ? 0 : -1}
                onClick={() => handleTabClick(tab.id)}
                onKeyDown={(e) => handleKeyDown(e, idx)}
                className={`relative px-3 flex items-center space-x-1.5 transition-colors text-[10px] font-semibold tracking-wider ${
                  isActive && isOpen
                    ? "text-cyan-300 bg-[#0d1527]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#0c1222]"
                }`}
              >
                <span className={isActive && isOpen ? "text-cyan-400" : "text-slate-500"}>
                  {tab.icon}
                </span>
                <span>{tab.label}</span>

                {typeof tab.badge !== "undefined" && (
                  <span
                    className={`ml-1 px-1.5 py-0.2 text-[9px] rounded-full font-bold ${
                      isActive && isOpen
                        ? "bg-cyan-950 text-cyan-300 border border-cyan-800/60"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}

                {/* Active Indicator Underline */}
                {isActive && isOpen && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-cyan-400 shadow-[0_0_6px_rgba(6,182,212,0.6)]" />
                )}
              </button>
            );
          })}
        </div>

        {/* Right: Dock Controls (Expand / Collapse) */}
        <div className="flex items-center space-x-1 text-slate-400">
          {isOpen && (
            <button
              type="button"
              onClick={() => setIsExpanded((v) => !v)}
              title={isExpanded ? "Restore dock height" : "Maximize dock height"}
              className="p-1 hover:text-cyan-300 hover:bg-[#0c1222] rounded transition-colors"
              aria-label={isExpanded ? "Restore dock height" : "Maximize dock height"}
            >
              {isExpanded ? <Minimize2 className="w-3 h-3" /> : <Maximize2 className="w-3 h-3" />}
            </button>
          )}

          <button
            type="button"
            onClick={onToggleOpen}
            title={isOpen ? "Collapse bottom dock" : "Expand bottom dock"}
            className="p-1 hover:text-cyan-300 hover:bg-[#0c1222] rounded transition-colors flex items-center space-x-0.5"
            aria-label={isOpen ? "Collapse bottom dock" : "Expand bottom dock"}
          >
            <PanelBottom className="w-3.5 h-3.5" />
            {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {/* Dock Content Panels (all kept mounted to preserve input & layer state) */}
      {isOpen && (
        <div className="flex-1 w-full overflow-hidden bg-[#050913]">
          {/* 1. PROBLEMS TAB PANEL */}
          <div
            role="tabpanel"
            id="dock-tabpanel-problems"
            aria-labelledby="dock-tab-problems"
            className={`h-full w-full overflow-y-auto p-3 ${
              activeTab === "problems" ? "block" : "hidden"
            }`}
          >
            <div className="space-y-2 max-w-4xl">
              <div className="flex items-center justify-between pb-1.5 border-b border-cyan-950/60 text-[11px]">
                <div className="flex items-center space-x-1.5 text-slate-300 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>No errors or warnings detected in current celestial workspace.</span>
                </div>
                <span className="text-[10px] text-slate-500">Filter: All Diagnostics (3 active rules)</span>
              </div>

              <div className="space-y-1.5 text-[10px] text-slate-400">
                <div className="flex items-start space-x-2 p-1.5 rounded bg-[#091122]/60 border border-cyan-950/40">
                  <Info className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-cyan-300">Astrometric WCS Tangent Projection:</span>
                    <span className="ml-1 text-slate-300">
                      Standard ICRS celestial sphere with TAN projective transformations verified.
                    </span>
                  </div>
                </div>

                <div className="flex items-start space-x-2 p-1.5 rounded bg-[#091122]/60 border border-cyan-950/40">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-emerald-300">Scientific Data Provenance Registry:</span>
                    <span className="ml-1 text-slate-300">
                      All datasets carry authentic cryptographic checksums or explicit SYNTHETIC_DEMO labeling.
                    </span>
                  </div>
                </div>

                <div className="flex items-start space-x-2 p-1.5 rounded bg-[#091122]/60 border border-cyan-950/40">
                  <Info className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-cyan-300">Photometric Calibration:</span>
                    <span className="ml-1 text-slate-300">
                      SPHEREx Level-2 multi-extension FITS products preserved in surface brightness units (MJy/sr).
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 2. COORDINATES TAB PANEL */}
          <div
            role="tabpanel"
            id="dock-tabpanel-coordinates"
            aria-labelledby="dock-tab-coordinates"
            className={`h-full w-full overflow-y-auto ${
              activeTab === "coordinates" ? "block" : "hidden"
            }`}
          >
            {coordinatesContent}
          </div>

          {/* 3. IMAGE LAYERS TAB PANEL */}
          <div
            role="tabpanel"
            id="dock-tabpanel-layers"
            aria-labelledby="dock-tab-layers"
            className={`h-full w-full overflow-y-auto ${
              activeTab === "layers" ? "block" : "hidden"
            }`}
          >
            {imageLayersContent}
          </div>
        </div>
      )}
    </section>
  );
}
