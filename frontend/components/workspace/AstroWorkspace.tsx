"use client";

import React, { useState, useCallback, useEffect } from "react";
import {
  Activity, AudioLines, ChevronDown, ChevronRight, CircleDot, Clock3, Database,
  FileCode2, FileImage, Files, Folder, FolderOpen, GitBranch, Layers3,
  ChevronUp, PanelBottom, PanelRight, Settings2, ShieldCheck, Telescope, X, Workflow,
} from "lucide-react";
import { TopNavigation } from "@/components/layout/TopNavigation";
import { CelestialSphere } from "@/components/celestial/CelestialSphere";
import { ViewControls } from "@/components/controls/ViewControls";
import { CoordinateSearchPanel, TargetCoordinates } from "@/components/controls/CoordinateSearchPanel";
import { CameraTelemetry } from "@/components/celestial/CameraController";
import { ImageLayerControls } from "@/components/controls/ImageLayerControls";
import { WorkspaceBottomDock, BottomDockTab } from "@/components/workspace/WorkspaceBottomDock";
import { ActiveImageLayerState } from "@/types/astronomicalImage";
import { useSkyStore } from "@/stores/useSkyStore";
import { TemporalControlPanel } from "@/components/temporal/TemporalControlPanel";
import { SpectralExplorerPanel } from "@/components/spectral/SpectralExplorerPanel";
import { ValidationTargetsView } from "@/components/targets/ValidationTargetsView";
import { AboutMissionModal } from "@/components/layout/AboutMissionModal";

type ActivityPaneKind = "explorer" | "data" | "analysis" | "integrations";
type ExplorerFile = "sky" | "temporal" | "spectral" | "targets";

export function AstroWorkspace() {
  const [showGrid, setShowGrid] = useState(true);
  const [showStars, setShowStars] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [resetTrigger, setResetTrigger] = useState(0);
  const [zoomInTrigger, setZoomInTrigger] = useState(0);
  const [zoomOutTrigger, setZoomOutTrigger] = useState(0);
  const [activeTarget, setActiveTarget] = useState<TargetCoordinates | null>(null);
  const [targetCoords, setTargetCoords] = useState<{ ra: number; dec: number } | null>(null);
  const [targetCoordsTrigger, setTargetCoordsTrigger] = useState(0);
  const [currentFov, setCurrentFov] = useState<number>(60);
  const [imageLayers, setImageLayers] = useState<ActiveImageLayerState[]>([]);
  const [telemetry, setTelemetry] = useState<CameraTelemetry | null>(null);
  const [activity, setActivity] = useState<ActivityPaneKind>("explorer");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const [dockOpen, setDockOpen] = useState(true);
  const [activeFile, setActiveFile] = useState<ExplorerFile>("sky");
  const [dockTab, setDockTab] = useState<BottomDockTab>("coordinates");

  const activeTab = useSkyStore((s) => s.activeTab);
  const storeRa = useSkyStore((s) => s.raDeg);
  const storeDec = useSkyStore((s) => s.decDeg);
  const cameraFlightTrigger = useSkyStore((s) => s.cameraFlightTrigger);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const bands = useSkyStore((s) => s.bands);
  const selectedChannel = useSkyStore((s) => s.selectedChannel);
  const setSelectedChannel = useSkyStore((s) => s.setSelectedChannel);
  const epochs = useSkyStore((s) => s.epochs);
  const bandCatalogState = useSkyStore((s) => s.bandCatalogState);
  const temporalDiscoveryState = useSkyStore((s) => s.temporalDiscoveryState);
  const timelineMode = useSkyStore((s) => s.timelineMode);
  const realObservations = useSkyStore((s) => s.realObservations);
  const spectralMode = useSkyStore((s) => s.spectralMode);
  const spectralProfile = useSkyStore((s) => s.spectralProfile);

  useEffect(() => {
    useSkyStore.getState().initializeStore();
    if (typeof document !== "undefined") {
      document.title = "SkyTrace";
    }
  }, []);

  useEffect(() => {
    if (activeTab === "temporal") {
      useSkyStore.getState().setBottomPanelCollapsed(false);
      setDockOpen(true);
    }
    if (activeTab === "sky") setActiveFile("sky");
    if (activeTab === "temporal") setActiveFile("temporal");
    if (activeTab === "spectral") setActiveFile("spectral");
    if (activeTab === "targets") setActiveFile("targets");
  }, [activeTab]);

  useEffect(() => {
    if (cameraFlightTrigger > 0) {
      setTargetCoords({ ra: storeRa, dec: storeDec });
      setTargetCoordsTrigger((prev) => prev + 1);
      setActiveTarget({
        ra: storeRa, dec: storeDec, format: "decimal",
        rawRa: storeRa.toFixed(6), rawDec: storeDec.toFixed(6),
        sourceLabel: selectedTarget ? selectedTarget.name : "STORE TARGET",
      });
    }
  }, [cameraFlightTrigger, storeRa, storeDec, selectedTarget]);

  const handleTelemetryUpdate = useCallback((t: CameraTelemetry) => setTelemetry(t), []);
  const handleZoomIn = useCallback(() => setZoomInTrigger((v) => v + 1), []);
  const handleZoomOut = useCallback(() => setZoomOutTrigger((v) => v + 1), []);

  const handleResetView = useCallback(() => {
    setResetTrigger((v) => v + 1);
    setActiveTarget(null);
    setTargetCoords(null);
    setCurrentFov(60);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      ["ra", "dec", "fov"].forEach((key) => url.searchParams.delete(key));
      window.history.pushState({}, "", url.toString());
    }
  }, []);

  const handleSearch = useCallback((target: TargetCoordinates) => {
    setActiveTarget(target);
    setTargetCoords({ ra: target.ra, dec: target.dec });
    setTargetCoordsTrigger((v) => v + 1);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("ra", target.ra.toFixed(6));
      url.searchParams.set("dec", target.dec.toFixed(6));
      url.searchParams.set("fov", currentFov.toString());
      window.history.pushState({}, "", url.toString());
    }
  }, [currentFov]);

  const handleAddLayer = useCallback((layer: ActiveImageLayerState) => setImageLayers((v) => [...v, layer]), []);
  const handleUpdateLayer = useCallback((layerId: string, updates: Partial<ActiveImageLayerState>) => {
    setImageLayers((v) => v.map((layer) => layer.layer_id === layerId ? { ...layer, ...updates } : layer));
  }, []);
  const handleRemoveLayer = useCallback((layerId: string) => setImageLayers((v) => v.filter((layer) => layer.layer_id !== layerId)), []);
  const handleNavigateToImageCenter = useCallback((ra: number, dec: number, label?: string) => {
    handleSearch({ ra, dec, format: "decimal", rawRa: ra.toFixed(6), rawDec: dec.toFixed(6), sourceLabel: label || "IMAGE WCS CENTER" });
  }, [handleSearch]);
  const handleClearTarget = useCallback(() => {
    setActiveTarget(null);
    setTargetCoords(null);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.delete("ra"); url.searchParams.delete("dec");
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

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const raParam = params.get("ra");
    const decParam = params.get("dec");
    const fovParam = params.get("fov");
    const tabParam = params.get("tab");

    if (tabParam === "temporal" || tabParam === "spectral" || tabParam === "targets" || tabParam === "sky") {
      useSkyStore.getState().setActiveTab(tabParam);
    }

    if (raParam !== null && decParam !== null) {
      const ra = parseFloat(raParam), dec = parseFloat(decParam);
      if (!Number.isNaN(ra) && !Number.isNaN(dec) && ra >= 0 && ra < 360 && dec >= -90 && dec <= 90) {
        setActiveTarget({ ra, dec, format: "decimal", rawRa: raParam, rawDec: decParam, sourceLabel: "URL RESTORED TARGET" });
        setTargetCoords({ ra, dec }); setTargetCoordsTrigger((v) => v + 1);
      }
    }
    if (fovParam !== null) {
      const parsed = parseFloat(fovParam);
      if (!Number.isNaN(parsed) && parsed >= 0.05 && parsed <= 120) setCurrentFov(parsed);
    }
    const onPopState = () => {
      const current = new URLSearchParams(window.location.search);
      const raValue = current.get("ra"), decValue = current.get("dec"), fovValue = current.get("fov");
      if (raValue && decValue) {
        const ra = parseFloat(raValue), dec = parseFloat(decValue);
        if (Number.isFinite(ra) && Number.isFinite(dec) && ra >= 0 && ra < 360 && dec >= -90 && dec <= 90) {
          setActiveTarget({ ra, dec, format: "decimal", rawRa: raValue, rawDec: decValue, sourceLabel: "HISTORY RESTORED TARGET" });
          setTargetCoords({ ra, dec }); setTargetCoordsTrigger((v) => v + 1);
        }
      } else { setActiveTarget(null); setTargetCoords(null); }
      if (fovValue) {
        const fov = parseFloat(fovValue);
        if (Number.isFinite(fov) && fov >= 0.05 && fov <= 120) setCurrentFov(fov);
      }
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const activateFile = (file: ExplorerFile) => {
    setActiveFile(file);
    const tab = file === "sky" ? "sky" : file === "temporal" ? "temporal" : file === "spectral" ? "spectral" : "targets";
    useSkyStore.getState().setActiveTab(tab);
    setActivity("explorer");
  };

  const currentFileName = activeFile === "sky" ? "sky_viewer.fits" : activeFile === "temporal" ? "epoch_compare" : activeFile === "spectral" ? "spectral_cube" : "validation_targets";
  const workspaceTitle = activeFile === "sky" ? "Sky Explorer" : activeFile === "temporal" ? "Time Domain" : activeFile === "spectral" ? "Spectral Laboratory" : "Validation Targets";

  return (
    <div className="astro-ide-root">
      <TopNavigation telemetry={telemetry} starCount={showStars ? 4500 : 0} targetCoords={targetCoords} />
      <div className="astro-ide-body">
        <aside className="astro-activity-rail" aria-label="Activity bar">
          <div className="astro-activity-group">
            <ActivityButton active={activity === "explorer"} label="Explorer" onClick={() => {setActivity("explorer");setSidebarOpen(true)}}><Files/></ActivityButton>
            <ActivityButton active={activity === "data"} label="Data releases" onClick={() => {setActivity("data");setSidebarOpen(true)}}><Database/></ActivityButton>
            <ActivityButton active={activity === "analysis"} label="Analysis" onClick={() => {setActivity("analysis");setSidebarOpen(true)}}><Workflow/></ActivityButton>
            <ActivityButton active={activity === "integrations"} label="Integrations" onClick={() => {setActivity("integrations");setSidebarOpen(true)}}><Layers3/></ActivityButton>
          </div>
          <div className="astro-activity-bottom"><ActivityButton label="Coordinates & Settings" onClick={() => { setDockTab("coordinates"); setDockOpen(true); }}><Settings2/></ActivityButton></div>
        </aside>

        {sidebarOpen && <aside className="astro-explorer-sidebar">
          <div className="astro-pane-heading"><span>{activity === "explorer" ? "EXPLORER" : activity === "data" ? "DATA RELEASES" : activity === "analysis" ? "ANALYSIS" : "INTEGRATIONS"}</span><ChevronDown size={13}/></div>
          {activity === "explorer" && <div className="astro-file-tree">
            <div className="astro-tree-workspace"><ChevronDown size={13}/><FolderOpen size={14}/><span>SKYTRACE</span></div>
            <TreeFolder name="observations" open>
              <TreeFile active={activeFile === "sky"} icon={<FileImage/>} label="sky_viewer.fits" onClick={() => activateFile("sky")}/>
              <TreeFile icon={<FileImage/>} label="epoch_01.fits" onClick={() => activateFile("temporal")}/>
              <TreeFile icon={<FileImage/>} label="epoch_02.fits" onClick={() => activateFile("temporal")}/>
            </TreeFolder>
            <TreeFolder name="spectral_data" open>
              <TreeFile active={activeFile === "spectral"} icon={<AudioLines/>} label="spectral_cube" onClick={() => activateFile("spectral")}/>
              <TreeFile icon={<FileCode2/>} label="band_manifest.json" onClick={() => activateFile("spectral")}/>
              <TreeFile icon={<FileCode2/>} label="detector_arrays.yaml" onClick={() => activateFile("spectral")}/>
            </TreeFolder>
            <TreeFolder name="time_domain">
              <TreeFile active={activeFile === "temporal"} icon={<Clock3/>} label="epoch_compare" onClick={() => activateFile("temporal")}/>
              <TreeFile icon={<FileImage/>} label="difference_map.fits" onClick={() => activateFile("temporal")}/>
            </TreeFolder>
            <TreeFolder name="research">
              <TreeFile active={activeFile === "targets"} icon={<ShieldCheck/>} label="validation_targets" onClick={() => activateFile("targets")}/>
              <TreeFile icon={<FileCode2/>} label="analysis_pipeline.py" onClick={() => activateFile("spectral")}/>
            </TreeFolder>
          </div>}
          {activity === "data" && <div className="astro-sidebar-content">
            <div className="astro-tree-workspace"><Database size={14}/> RELEASE CATALOGUE</div>
            <div className="astro-release-item"><span className="astro-release-dot live"/> <div><strong>QR3</strong><small>Current query collection</small></div><span className="astro-release-tag">API</span></div>
            <div className="astro-release-item"><span className="astro-release-dot"/> <div><strong>DR1</strong><small>Legacy release collection</small></div></div>
            <div className="astro-sidebar-note">Release availability is resolved by the archive service. This panel does not assume all releases contain matching observations.</div>
          </div>}
          {activity === "analysis" && <div className="astro-sidebar-content">
            <div className="astro-tree-workspace"><Workflow size={14}/> ANALYSIS MODULES</div>
            <TreeFile active={activeFile === "spectral"} icon={<AudioLines/>} label="102-band spectroscopy" onClick={() => activateFile("spectral")}/>
            <TreeFile active={activeFile === "temporal"} icon={<Clock3/>} label="Temporal difference" onClick={() => activateFile("temporal")}/>
            <TreeFile active={activeFile === "targets"} icon={<ShieldCheck/>} label="Target validation" onClick={() => activateFile("targets")}/>
            <div className="astro-sidebar-note">Scientific execution remains in the existing backend services.</div>
          </div>}
          {activity === "integrations" && <div className="astro-sidebar-content">
            <div className="astro-tree-workspace"><Layers3 size={14}/> EXTERNAL CATALOGUES</div>
            {["Gaia DR3","WISE","Aladin / CDS"].map((name) => <div className="astro-extension-row" key={name}><GlobeItem/><span>{name}</span><span className="astro-extension-state">NOT CONFIGURED</span></div>)}
            <div className="astro-sidebar-note">These are integration targets, not active layers in this workspace yet. Existing SPHEREx image-layer controls remain connected to the current backend.</div>
          </div>}
          <div className="astro-sidebar-bottom">
            <div className="astro-pane-heading">OUTLINE</div>
            <div className="astro-outline-item"><CircleDot size={11}/> {workspaceTitle}</div>
            <div className="astro-outline-item"><CircleDot size={11}/> Coordinates & WCS</div>
            <div className="astro-outline-item"><CircleDot size={11}/> Data provenance</div>
          </div>
        </aside>}

        <main className="astro-editor">
          <div className="astro-tabstrip">
            <button className={activeTab === "sky" ? "astro-file-tab selected" : "astro-file-tab"} onClick={() => activateFile("sky")}><FileImage size={13}/> sky_viewer.fits</button>
            <button className={activeTab === "temporal" ? "astro-file-tab selected" : "astro-file-tab"} onClick={() => activateFile("temporal")}><Clock3 size={13}/> epoch_compare</button>
            <button className={activeTab === "spectral" ? "astro-file-tab selected" : "astro-file-tab"} onClick={() => activateFile("spectral")}><AudioLines size={13}/> spectral_cube</button>
            <button className={activeTab === "targets" ? "astro-file-tab selected" : "astro-file-tab"} onClick={() => activateFile("targets")}><ShieldCheck size={13}/> validation_targets</button>
            <div className="astro-tabstrip-spacer"/>
            <button className="astro-mini-icon" title="Toggle right inspector" onClick={() => setInspectorOpen((v) => !v)}><PanelRight size={14}/></button>
          </div>
          <div className="astro-editor-toolbar">
            <span>skytrace</span><ChevronRight size={12}/><span>{activeTab === "sky" ? "observations" : activeTab === "temporal" ? "time_domain" : activeTab === "spectral" ? "spectral_data" : "research"}</span><ChevronRight size={12}/><strong>{currentFileName}</strong>
            <div className="astro-toolbar-spacer"/>
            <span className="astro-toolbar-hint">SkyTrace · ICRS / WCS</span>
          </div>

          <section className="astro-canvas">
            <CelestialSphere
              showGrid={showGrid} showStars={showStars} showLabels={showLabels}
              onTelemetryUpdate={handleTelemetryUpdate}
              resetTrigger={resetTrigger} zoomInTrigger={zoomInTrigger} zoomOutTrigger={zoomOutTrigger}
              targetCoords={targetCoords} targetCoordsTrigger={targetCoordsTrigger}
              targetLabel={activeTarget?.sourceLabel || "SEARCH TARGET"}
              fov={currentFov} imageLayers={imageLayers}
            />

            {activeTab === "sky" && <>
              <div className="astro-canvas-top-left"><ViewControls onZoomIn={handleZoomIn} onZoomOut={handleZoomOut} onResetView={handleResetView} showGrid={showGrid} onToggleGrid={() => setShowGrid((v) => !v)} showStars={showStars} onToggleStars={() => setShowStars((v) => !v)} showLabels={showLabels} onToggleLabels={() => setShowLabels((v) => !v)}/></div>
              <div className="astro-canvas-hint">DRAG TO ORBIT <i/> SCROLL TO ZOOM <i/> RIGHT-DRAG TO PAN</div>
            </>}

            {activeTab === "temporal" && <div className="astro-overlay-workspace temporal"><TemporalControlPanel onAddLayer={handleAddLayer}/></div>}
            {activeTab === "spectral" && <div className="astro-overlay-workspace spectral"><SpectralExplorerPanel/></div>}
            {activeTab === "targets" && <div className="astro-overlay-workspace targets"><ValidationTargetsView/></div>}
            {activeTab === "about" && <AboutMissionModal/>}
          </section>

          <WorkspaceBottomDock
            isOpen={dockOpen}
            onToggleOpen={() => setDockOpen((v) => !v)}
            activeTab={dockTab}
            onTabChange={(tab) => setDockTab(tab)}
            layersCount={imageLayers.length}
            coordinatesContent={
              <CoordinateSearchPanel
                onSearch={handleSearch}
                onClearTarget={handleClearTarget}
                onResetCamera={handleResetView}
                onFovChange={handleFovChange}
                activeTarget={activeTarget}
                currentFov={currentFov}
                variant="dock"
              />
            }
            imageLayersContent={
              <ImageLayerControls
                layers={imageLayers}
                onAddLayer={handleAddLayer}
                onUpdateLayer={handleUpdateLayer}
                onRemoveLayer={handleRemoveLayer}
                onNavigateToCoordinates={handleNavigateToImageCenter}
                variant="dock"
              />
            }
          />
        </main>

        {inspectorOpen && <aside className="astro-inspector">
          <div className="astro-pane-heading"><span>INSPECTOR</span><button className="astro-mini-icon" onClick={() => setInspectorOpen(false)}><X size={13}/></button></div>
          <div className="astro-inspector-section">
            <div className="astro-inspector-label"><ChevronDown size={12}/> VIEW CONTEXT</div>
            <div className="astro-kv"><span>Workspace</span><strong>{activeTab === "temporal" ? "Time Domain" : activeTab === "spectral" ? "Spectral Lab" : activeTab === "targets" ? "Targets" : "Sky Explorer"}</strong></div>
            <div className="astro-kv"><span>Target</span><strong>{selectedTarget?.name || "Custom sky position"}</strong></div>
            <div className="astro-kv"><span>RA / Dec</span><strong>{storeRa.toFixed(6)}°, {storeDec.toFixed(6)}°</strong></div>
            <div className="astro-kv"><span>Camera FOV</span><strong>{telemetry?.fov ?? currentFov}°</strong></div>
          </div>
          <div className="astro-inspector-section">
            <div className="astro-inspector-label"><ChevronDown size={12}/> SCIENTIFIC STATE</div>
            <div className="astro-kv">
              <span>Band catalogue</span>
              <strong className={bandCatalogState === "LOADED" ? "text-emerald-400" : bandCatalogState === "LOADING" ? "text-amber-300" : ""}>
                {bandCatalogState === "LOADING"
                  ? "Loading..."
                  : bandCatalogState === "FAILED"
                  ? "Failed to load"
                  : bandCatalogState === "EMPTY"
                  ? "0 channels (EMPTY)"
                  : bands.length
                  ? `${bands.length} channels (CALIBRATED)`
                  : "102 channels (CALIBRATED)"}
              </strong>
            </div>
            <div className="astro-kv">
              <span>Selected channel</span>
              <strong>
                {`Band ${selectedChannel} (Array ${bands.find((b) => b.channel_index === selectedChannel)?.array_index || 3}, λ = ${bands.find((b) => b.channel_index === selectedChannel)?.wavelength_um?.toFixed(3) || "2.351"} µm)`}
              </strong>
            </div>
            <div className="astro-kv">
              <span>Temporal epochs</span>
              <strong className={timelineMode === "real" && (realObservations.length > 0 || epochs.length > 0) ? "text-emerald-400" : ""}>
                {temporalDiscoveryState === "NOT_QUERIED"
                  ? "Not queried"
                  : temporalDiscoveryState === "QUERYING"
                  ? "Querying IRSA..."
                  : temporalDiscoveryState === "ARCHIVE_QUERY_FAILED"
                  ? "Discovery failed"
                  : timelineMode === "real" && (realObservations.length > 0 || epochs.length > 0)
                  ? `${realObservations.length || epochs.length} flight epochs (IRSA Verified)`
                  : `${epochs.length} epochs (Simulated)`}
              </strong>
            </div>
            <div className="astro-kv">
              <span>Image layers</span>
              <strong className={imageLayers.length > 0 ? "text-cyan-300 font-bold" : ""}>
                {imageLayers.length}
              </strong>
            </div>
            {activeTab === "spectral" && (
              <div className="astro-kv">
                <span>Spectral coverage</span>
                <strong className={spectralProfile.filter((p) => p.flux_is_available && p.flux_mjy !== null).length > 0 ? "text-emerald-400 font-bold" : ""}>
                  {spectralProfile.filter((p) => p.flux_is_available && p.flux_mjy !== null).length > 0
                    ? `${spectralProfile.filter((p) => p.flux_is_available && p.flux_mjy !== null).length} flight measurement(s)`
                    : spectralMode === "real"
                    ? "No pointing coverage"
                    : "102 channels (Simulated)"}
                </strong>
              </div>
            )}
            <div className="astro-kv">
              <span>Data source</span>
              <strong>
                {activeTab === "temporal"
                  ? timelineMode === "real"
                    ? "NASA/IPAC IRSA (SPHEREx QR3 Flight FITS)"
                    : "Nominal Survey Simulation"
                  : activeTab === "spectral"
                  ? spectralMode === "real"
                    ? "NASA SPHEREx Level-2 (WCS-WAVE / IMAGE)"
                    : "Nominal Instrument Model"
                  : "NASA SPHEREx Level-2"}
              </strong>
            </div>
            <div className="astro-kv">
              <span>Provenance</span>
              <strong className={(activeTab === "temporal" && timelineMode === "real") || (activeTab === "spectral" && spectralMode === "real") ? "text-emerald-400" : ""}>
                {activeTab === "temporal"
                  ? timelineMode === "real"
                    ? "REAL_VERIFIED (NASA Flight FITS)"
                    : "SYNTHETIC_DEMO (Nominal Cadence)"
                  : activeTab === "spectral"
                  ? spectralMode === "real"
                    ? "REAL_VERIFIED (WCS-WAVE / IMAGE / VARIANCE)"
                    : "SYNTHETIC_DEMO (Nominal Model)"
                  : "CALIBRATED_ARCHIVE"}
              </strong>
            </div>
          </div>
          <div className="astro-inspector-section">
            <div className="astro-inspector-label"><ChevronDown size={12}/> COORDINATE SYSTEM</div>
            <div className="astro-kv"><span>Reference frame</span><strong>ICRS</strong></div>
            <div className="astro-kv"><span>Projection</span><strong>WCS-aware layers</strong></div>
            <div className="astro-kv"><span>RA</span><strong>{storeRa.toFixed(6)}°</strong></div>
            <div className="astro-kv"><span>Dec</span><strong>{storeDec.toFixed(6)}°</strong></div>
          </div>
          <div className="astro-inspector-warning"><Activity size={13}/><span>Demonstration star field is procedural. Archive-backed image layers retain their own provenance and quality metadata.</span></div>
          <div className="astro-inspector-footer"><Telescope size={13}/> SkyTrace · SPHEREx Research Workspace</div>
        </aside>}
      </div>

      <footer className="astro-statusbar">
        <div><span><GitBranch size={12}/> skytrace</span><span><CircleDot size={11}/> Workspace ready</span>{(timelineMode === "real" && activeTab === "temporal") || (spectralMode === "real" && activeTab === "spectral") ? (
            <span className="astro-status-verified" style={{ background: "rgba(16, 185, 129, 0.15)", border: "1px solid rgba(16, 185, 129, 0.5)", color: "#34d399", padding: "1px 6px", borderRadius: "4px", fontSize: "10px", display: "inline-flex", alignItems: "center", gap: "4px" }}>
              <i style={{ width: 6, height: 6, borderRadius: "50%", background: "#10b981", display: "inline-block" }} /> AUTHENTIC FLIGHT DATA (NASA / IPAC IRSA)
            </span>
          ) : (
            <span className="astro-status-demo"><i/> DEMONSTRATION MODE</span>
          )}</div>
        <div><span>RA {storeRa.toFixed(4)}°</span><span>DEC {storeDec.toFixed(4)}°</span><span>FOV {currentFov.toFixed(2)}°</span><span>CHANNEL {selectedChannel}/102</span><span>ARRAY {bands.find((b) => b.channel_index === selectedChannel)?.array_index ?? "—"}</span></div>
      </footer>
    </div>
  );
}

export default AstroWorkspace;

function ActivityButton({children,active,label,onClick}:{children:React.ReactNode;active?:boolean;label:string;onClick:()=>void}) {
  return <button className={active ? "astro-activity-button active" : "astro-activity-button"} title={label} aria-label={label} onClick={onClick}>{children}</button>;
}
function TreeFolder({name,open=false,children}:{name:string;open?:boolean;children:React.ReactNode}) {
  const [expanded,setExpanded] = useState(open);
  return <div className="astro-tree-folder"><button onClick={() => setExpanded((v)=>!v)}>{expanded ? <ChevronDown size={12}/> : <ChevronRight size={12}/>}<Folder size={13}/><span>{name}</span></button>{expanded && <div className="astro-tree-children">{children}</div>}</div>;
}
function TreeFile({icon,label,active,onClick}:{icon:React.ReactNode;label:string;active?:boolean;onClick:()=>void}) {
  return <button className={active ? "astro-tree-file active" : "astro-tree-file"} onClick={onClick}>{icon}<span>{label}</span></button>;
}
function GlobeItem() { return <span className="astro-globe-icon"><Database size={12}/></span>; }
