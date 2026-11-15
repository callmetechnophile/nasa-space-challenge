"use client";

import React, { useState, useCallback, useEffect } from "react";
import { TopNavigation } from "@/components/layout/TopNavigation";
import { CelestialSphere } from "@/components/celestial/CelestialSphere";
import { ViewControls } from "@/components/controls/ViewControls";
import { StatusPanel } from "@/components/layout/StatusPanel";
import {
  CoordinateSearchPanel,
  TargetCoordinates,
} from "@/components/controls/CoordinateSearchPanel";
import { CameraTelemetry } from "@/components/celestial/CameraController";
import { ImageLayerControls } from "@/components/controls/ImageLayerControls";
import { SpherexSearchPanel } from "@/components/controls/SpherexSearchPanel";
import { ActiveImageLayerState } from "@/types/astronomicalImage";
import { useSkyStore } from "@/stores/useSkyStore";
import { TemporalControlPanel } from "@/components/temporal/TemporalControlPanel";
import { SpectralExplorerPanel } from "@/components/spectral/SpectralExplorerPanel";
import { ValidationTargetsView } from "@/components/targets/ValidationTargetsView";
import { AboutMissionModal } from "@/components/layout/AboutMissionModal";

export default function CelestialExplorerMilestone2() {
  // Layer visibility toggles
  const [showGrid, setShowGrid] = useState(true);
  const [showStars, setShowStars] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  // Camera triggers
  const [resetTrigger, setResetTrigger] = useState(0);
  const [zoomInTrigger, setZoomInTrigger] = useState(0);
  const [zoomOutTrigger, setZoomOutTrigger] = useState(0);

  // M2: Target coordinates & Camera navigation
  const [activeTarget, setActiveTarget] = useState<TargetCoordinates | null>(null);
  const [targetCoords, setTargetCoords] = useState<{ ra: number; dec: number } | null>(null);
  const [targetCoordsTrigger, setTargetCoordsTrigger] = useState(0);
  const [currentFov, setCurrentFov] = useState<number>(60);

  // M3: Astronomical Image Layers
  const [imageLayers, setImageLayers] = useState<ActiveImageLayerState[]>([]);

  // M4 & M5: SkyStore integration
  const activeTab = useSkyStore((s) => s.activeTab);
  const storeRa = useSkyStore((s) => s.raDeg);
  const storeDec = useSkyStore((s) => s.decDeg);
  const cameraFlightTrigger = useSkyStore((s) => s.cameraFlightTrigger);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const setBottomPanelCollapsed = useSkyStore((s) => s.setBottomPanelCollapsed);

  // Initialize store on mount
  useEffect(() => {
    useSkyStore.getState().initializeStore();
  }, []);

  // When tab switches to temporal, ensure temporal comparison panel is open
  useEffect(() => {
    if (activeTab === "temporal") {
      setBottomPanelCollapsed(false);
    }
  }, [activeTab, setBottomPanelCollapsed]);

  // Sync store target navigation with 3D camera
  useEffect(() => {
    if (cameraFlightTrigger > 0) {
      setTargetCoords({ ra: storeRa, dec: storeDec });
      setTargetCoordsTrigger((prev) => prev + 1);
      setActiveTarget({
        ra: storeRa,
        dec: storeDec,
        format: "decimal",
        rawRa: storeRa.toFixed(6),
        rawDec: storeDec.toFixed(6),
        sourceLabel: selectedTarget ? selectedTarget.name : "STORE TARGET",
      });
    }
  }, [cameraFlightTrigger, storeRa, storeDec, selectedTarget]);

  // Real-time telemetry from CameraController
  const [telemetry, setTelemetry] = useState<CameraTelemetry | null>(null);

  const handleTelemetryUpdate = useCallback((t: CameraTelemetry) => {
    setTelemetry(t);
  }, []);

  const handleZoomIn = useCallback(() => {
    setZoomInTrigger((prev) => prev + 1);
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomOutTrigger((prev) => prev + 1);
  }, []);

  const handleResetView = useCallback(() => {
    setResetTrigger((prev) => prev + 1);
    setActiveTarget(null);
    setTargetCoords(null);
    setCurrentFov(60);

    // Update URL to remove query parameters
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.delete("ra");
      url.searchParams.delete("dec");
      url.searchParams.delete("fov");
      window.history.pushState({}, "", url.toString());
    }
  }, []);

  // M2: Search & Coordinate Flight
  const handleSearch = useCallback(
    (target: TargetCoordinates) => {
      setActiveTarget(target);
      setTargetCoords({ ra: target.ra, dec: target.dec });
      setTargetCoordsTrigger((prev) => prev + 1);

      // URL synchronization with pushState
      if (typeof window !== "undefined") {
        const url = new URL(window.location.href);
        url.searchParams.set("ra", target.ra.toFixed(6));
        url.searchParams.set("dec", target.dec.toFixed(6));
        url.searchParams.set("fov", currentFov.toString());
        window.history.pushState({}, "", url.toString());
      }
    },
    [currentFov]
  );

  // M3: Image Layer Handlers
  const handleAddLayer = useCallback((layer: ActiveImageLayerState) => {
    setImageLayers((prev) => [...prev, layer]);
  }, []);

  const handleUpdateLayer = useCallback(
    (layerId: string, updates: Partial<ActiveImageLayerState>) => {
      setImageLayers((prev) =>
        prev.map((l) => (l.layer_id === layerId ? { ...l, ...updates } : l))
      );
    },
    []
  );

  const handleRemoveLayer = useCallback((layerId: string) => {
    setImageLayers((prev) => prev.filter((l) => l.layer_id !== layerId));
  }, []);

  const handleNavigateToImageCenter = useCallback(
    (ra: number, dec: number, label?: string) => {
      const target: TargetCoordinates = {
        ra,
        dec,
        format: "decimal",
        rawRa: ra.toFixed(6),
        rawDec: dec.toFixed(6),
        sourceLabel: label || "IMAGE WCS CENTER",
      };
      handleSearch(target);
    },
    [handleSearch]
  );

  const handleClearTarget = useCallback(() => {
    setActiveTarget(null);
    setTargetCoords(null);

    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.delete("ra");
      url.searchParams.delete("dec");
      window.history.pushState({}, "", url.toString());
    }
  }, []);

  const handleFovChange = useCallback((newFov: number) => {
    setCurrentFov(newFov);

    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("fov", newFov.toString());
      window.history.replaceState({}, "", url.toString());
    }
  }, []);

  // Initialize and synchronize with URL parameters on mount
  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const raParam = params.get("ra");
    const decParam = params.get("dec");
    const fovParam = params.get("fov");

    if (raParam !== null && decParam !== null) {
      const ra = parseFloat(raParam);
      const dec = parseFloat(decParam);
      if (!isNaN(ra) && !isNaN(dec) && ra >= 0 && ra < 360 && dec >= -90 && dec <= 90) {
        const target: TargetCoordinates = {
          ra,
          dec,
          format: "decimal",
          rawRa: raParam,
          rawDec: decParam,
          sourceLabel: "URL RESTORED TARGET",
        };
        setActiveTarget(target);
        setTargetCoords({ ra, dec });
        setTargetCoordsTrigger((prev) => prev + 1);
      }
    }

    if (fovParam !== null) {
      const parsedFov = parseFloat(fovParam);
      if (!isNaN(parsedFov) && parsedFov >= 0.05 && parsedFov <= 120) {
        setCurrentFov(parsedFov);
      }
    }

    // Handle browser back and forward history buttons
    const handlePopState = () => {
      const currentParams = new URLSearchParams(window.location.search);
      const curRa = currentParams.get("ra");
      const curDec = currentParams.get("dec");
      const curFov = currentParams.get("fov");

      if (curRa !== null && curDec !== null) {
        const ra = parseFloat(curRa);
        const dec = parseFloat(curDec);
        if (!isNaN(ra) && !isNaN(dec) && ra >= 0 && ra < 360 && dec >= -90 && dec <= 90) {
          setActiveTarget({
            ra,
            dec,
            format: "decimal",
            rawRa: curRa,
            rawDec: curDec,
            sourceLabel: "HISTORY RESTORED TARGET",
          });
          setTargetCoords({ ra, dec });
          setTargetCoordsTrigger((prev) => prev + 1);
        }
      } else {
        setActiveTarget(null);
        setTargetCoords(null);
      }

      if (curFov !== null) {
        const fov = parseFloat(curFov);
        if (!isNaN(fov) && fov >= 0.05 && fov <= 120) {
          setCurrentFov(fov);
        }
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  return (
    <div className="relative w-full h-full flex flex-col bg-[#02040a] overflow-hidden select-none">
      {/* 1. Minimal Scientific Top Navigation */}
      <TopNavigation />

      {/* 2. Main 3D Celestial Visualization Environment */}
      <main className="relative flex-1 w-full h-full overflow-hidden">
        {/* R3F WebGL Celestial Coordinate Sphere with Target Marker & Image Layers */}
        <CelestialSphere
          showGrid={showGrid}
          showStars={showStars}
          showLabels={showLabels}
          onTelemetryUpdate={handleTelemetryUpdate}
          resetTrigger={resetTrigger}
          zoomInTrigger={zoomInTrigger}
          zoomOutTrigger={zoomOutTrigger}
          targetCoords={targetCoords}
          targetCoordsTrigger={targetCoordsTrigger}
          targetLabel={activeTarget?.sourceLabel || "SEARCH TARGET"}
          fov={currentFov}
          imageLayers={imageLayers}
        />

        {/* Floating View Controls (Top-Left) */}
        <div className="absolute top-4 left-4 z-20 pointer-events-auto max-w-[260px] w-full">
          <ViewControls
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onResetView={handleResetView}
            showGrid={showGrid}
            onToggleGrid={() => setShowGrid((v) => !v)}
            showStars={showStars}
            onToggleStars={() => setShowStars((v) => !v)}
            showLabels={showLabels}
            onToggleLabels={() => setShowLabels((v) => !v)}
          />
        </div>

        {/* Floating Right Control Column: Coordinate Search & Image Layer Controls */}
        <div className="absolute top-4 right-4 z-20 pointer-events-auto max-w-[340px] w-full flex flex-col gap-3 max-h-[calc(100vh-2rem)] overflow-y-auto pr-1">
          <CoordinateSearchPanel
            onSearch={handleSearch}
            onClearTarget={handleClearTarget}
            onResetCamera={handleResetView}
            onFovChange={handleFovChange}
            activeTarget={activeTarget}
            currentFov={currentFov}
          />

          <SpherexSearchPanel
            onAddLayer={handleAddLayer}
            onNavigateToCoordinates={handleNavigateToImageCenter}
          />

          <ImageLayerControls
            layers={imageLayers}
            onAddLayer={handleAddLayer}
            onUpdateLayer={handleUpdateLayer}
            onRemoveLayer={handleRemoveLayer}
            onNavigateToCoordinates={handleNavigateToImageCenter}
          />
        </div>

        {/* Floating Status & Telemetry Panel (Bottom-Left) */}
        <div className="absolute bottom-4 left-4 z-20 pointer-events-auto max-w-[340px] w-full">
          <StatusPanel
            telemetry={telemetry}
            starCount={showStars ? 4500 : 0}
            targetCoords={targetCoords}
          />
        </div>

        {/* Minimal Interaction Hint (Bottom-Right) */}
        <div className="absolute bottom-4 right-4 z-10 pointer-events-none hidden md:block">
          <div className="bg-[#050b1a]/70 border border-cyan-950/60 rounded-lg px-3 py-1.5 font-mono text-[10px] text-slate-400 space-x-2">
            <span>Left-drag: Orbit</span>
            <span>•</span>
            <span>Scroll: Zoom</span>
            <span>•</span>
            <span>Right-drag: Pan</span>
            <span>•</span>
            <span>Double-click: Reset</span>
          </div>
        </div>

        {/* Milestone 4: Temporal Observation Timeline & Comparator Dock */}
        {(activeTab === "sky" || activeTab === "temporal") && (
          <TemporalControlPanel />
        )}

        {/* 102-Band Near-Infrared Spectral Explorer Overlay */}
        {activeTab === "spectral" && <SpectralExplorerPanel />}

        {/* NASA 5-Target Scientific Validation Suite Overlay */}
        {activeTab === "targets" && <ValidationTargetsView />}

        {/* SPHEREx Mission Architecture Documentation Modal */}
        {activeTab === "about" && <AboutMissionModal />}
      </main>
    </div>
  );
}
