"use client";

import React, { useState } from "react";
import {
  Activity, AudioLines, Atom, ChevronDown, Clock3, Command, Compass,
  Database, FlaskConical, Info, PanelLeft, Search, ShieldCheck, Telescope,
} from "lucide-react";
import { useSkyStore } from "@/stores/useSkyStore";

const navItems = [
  { id: "sky" as const, label: "Sky Explorer", shortcut: "⌘1", icon: Compass },
  { id: "temporal" as const, label: "Time Domain", shortcut: "⌘2", icon: Clock3 },
  { id: "spectral" as const, label: "Spectral Lab", shortcut: "⌘3", icon: AudioLines },
  { id: "targets" as const, label: "Targets", shortcut: "⌘4", icon: ShieldCheck },
];

export function TopNavigation() {
  const activeTab = useSkyStore((s) => s.activeTab);
  const setActiveTab = useSkyStore((s) => s.setActiveTab);
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <header className="astro-titlebar">
      <div className="astro-brand">
        <div className="astro-brand-mark"><Atom size={16} /></div>
        <span className="astro-brand-name">ASTRO<span>CODE</span></span>
        <span className="astro-title-divider" />
        <button className="astro-project-switch" onClick={() => setActiveTab("sky")}>
          spherex-research <ChevronDown size={12} />
        </button>
      </div>

      <button className="astro-command-search" onClick={() => setSearchOpen((v) => !v)}>
        <Search size={13} />
        <span>Search files, coordinates, datasets, commands</span>
        <kbd>⌘ K</kbd>
      </button>

      <div className="astro-title-actions">
        <span className="astro-demo-pill"><span /> DEMONSTRATION MODE</span>
        <span className="astro-title-divider" />
        <button className="astro-title-icon" title="Mission information" onClick={() => setActiveTab(activeTab === "about" ? "sky" : "about")}><Info size={15}/></button>
      </div>

      {searchOpen && (
        <div className="astro-quick-menu">
          <div className="astro-quick-title">OPEN WORKSPACE</div>
          {navItems.map(({id,label,shortcut,icon:Icon}) => (
            <button key={id} onClick={() => {setActiveTab(id);setSearchOpen(false);}}>
              <Icon size={14}/><span>{label}</span><kbd>{shortcut}</kbd>
            </button>
          ))}
          <div className="astro-quick-note">Coordinate search is available in the Explorer panel.</div>
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
      {navItems.map(({id,label,icon:Icon}) => (
        <button key={id} className={activeTab === id ? "astro-workspace-tab active" : "astro-workspace-tab"} onClick={() => setActiveTab(id)}>
          <Icon size={13}/><span>{label}</span>
        </button>
      ))}
    </nav>
  );
}