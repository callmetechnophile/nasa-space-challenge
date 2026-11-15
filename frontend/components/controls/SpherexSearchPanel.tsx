"use client";

import React, { useState } from "react";
import {
  Search,
  Satellite,
  Download,
  Eye,
  Compass,
  FileCheck2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Database,
  CheckCircle2,
  Layers,
  Sparkles,
  RefreshCw,
  X,
  ExternalLink,
} from "lucide-react";
import {
  SpherexObservationRecord,
  SpherexSearchResponse,
  SpherexMefInspection,
} from "@/types/spherex";
import { ActiveImageLayerState, DisplayStretchType } from "@/types/astronomicalImage";
import { SpherexService } from "@/services/spherexService";

interface PresetTarget {
  name: string;
  ra: number;
  dec: number;
  radius: number;
  collection: string;
}

const PRESET_TARGETS: PresetTarget[] = [
  { name: "WISE 0855", ra: 133.795129, dec: -7.245147, radius: 0.1, collection: "spherex_qr3" },
  { name: "South Pole", ra: 0.0, dec: -89.9, radius: 0.1, collection: "spherex_qr3" },
  { name: "Barnard's Star", ra: 269.452083, dec: 4.693333, radius: 0.1, collection: "spherex_qr3" },
  { name: "Epsilon Indi B", ra: 331.043792, dec: -56.782722, radius: 0.1, collection: "spherex_qr3" },
  { name: "RW Aurigae", ra: 76.956417, dec: 30.401417, radius: 0.1, collection: "spherex_qr3" },
  { name: "R Draconis", ra: 248.167625, dec: 66.755056, radius: 0.1, collection: "spherex_qr3" },
];

export interface SpherexSearchPanelProps {
  onAddLayer: (layer: ActiveImageLayerState) => void;
  onNavigateToCoordinates: (ra: number, dec: number, label?: string) => void;
}

export function SpherexSearchPanel({
  onAddLayer,
  onNavigateToCoordinates,
}: SpherexSearchPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [raInput, setRaInput] = useState<string>("133.795129");
  const [decInput, setDecInput] = useState<string>("-7.245147");
  const [radiusInput, setRadiusInput] = useState<string>("0.1");
  const [selectedCollection, setSelectedCollection] = useState<string>("spherex_qr3");
  const [allowFallback, setAllowFallback] = useState<boolean>(true);
  const [stretch, setStretch] = useState<DisplayStretchType>("asinh");

  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SpherexSearchResponse | null>(null);

  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [actionStatusText, setActionStatusText] = useState<string | null>(null);
  const [inspectionData, setInspectionData] = useState<SpherexMefInspection | null>(null);
  const [inspectModalOpen, setInspectModalOpen] = useState(false);

  // Handle Escape key to close inspection modal
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setInspectModalOpen(false);
    };
    if (inspectModalOpen) {
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [inspectModalOpen]);
  const [cachedProducts, setCachedProducts] = useState<Array<{ filename: string; size_mb: number; obs_id?: string; detector?: string }>>([]);

  // Fetch local cache inventory on mount
  React.useEffect(() => {
    SpherexService.getCacheStatus()
      .then(async (statusData) => {
        if (statusData.cached_products && statusData.cached_products.length > 0) {
          const detailed = await Promise.all(
            statusData.cached_products.map(async (cp) => {
              try {
                const insp = await SpherexService.inspectProduct(cp.filename);
                return {
                  filename: cp.filename,
                  size_mb: cp.size_mb,
                  obs_id: insp.observation_id,
                  detector: insp.detector,
                };
              } catch {
                return { filename: cp.filename, size_mb: cp.size_mb };
              }
            })
          );
          setCachedProducts(detailed);
        }
      })
      .catch((err) => console.warn("Failed to fetch SPHEREx cache status:", err));
  }, []);

  // Apply a preset target
  const applyPreset = (preset: PresetTarget) => {
    setRaInput(preset.ra.toString());
    setDecInput(preset.dec.toString());
    setRadiusInput(preset.radius.toString());
    setSelectedCollection(preset.collection);
  };

  // Execute IRSA SIA2 search
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const ra = parseFloat(raInput);
    const dec = parseFloat(decInput);
    const radius = parseFloat(radiusInput) || 0.05;

    if (isNaN(ra) || isNaN(dec)) {
      setSearchError("Please enter valid decimal coordinates for RA and Dec.");
      return;
    }

    setIsSearching(true);
    setSearchError(null);
    try {
      const response = await SpherexService.searchObservations({
        ra,
        dec,
        radius_deg: radius,
        collection: selectedCollection,
        allow_fallback: allowFallback,
      });
      setSearchResults(response);
    } catch (err: any) {
      setSearchError(err?.message || "Search failed");
    } finally {
      setIsSearching(false);
    }
  };

  // Inspect cached MEF product
  const handleInspect = async (filename: string) => {
    setActionLoadingId(filename);
    setActionStatusText("Inspecting MEF HDUs & WCS-SIP...");
    try {
      const data = await SpherexService.inspectProduct(filename);
      setInspectionData(data);
      setInspectModalOpen(true);
    } catch (err: any) {
      alert(`Inspection failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
      setActionStatusText(null);
    }
  };

  // Direct load for locally cached products
  const handleLoadDirectCached = async (filename: string) => {
    setActionLoadingId(filename);
    setActionStatusText("Synthesizing WCS spherical mesh & texture...");
    try {
      const layerPayload = await SpherexService.loadLayer({
        filename,
        stretch,
        radius: 98.0,
      });

      const activeLayer: ActiveImageLayerState = {
        layer_id: layerPayload.layer_id,
        title: layerPayload.title,
        provenance: layerPayload.provenance,
        is_real_data: true,
        observation_id: layerPayload.observation_id,
        detector: layerPayload.detector,
        metadata: layerPayload.metadata,
        mesh: layerPayload.mesh,
        texture_data_uri: layerPayload.texture_data_uri,
        stretch: layerPayload.stretch,
        brightness: layerPayload.brightness,
        contrast: layerPayload.contrast,
        visible: true,
        opacity: 0.9,
      };

      onAddLayer(activeLayer);
      if (layerPayload.mesh && layerPayload.mesh.center_radec) {
        onNavigateToCoordinates(
          layerPayload.mesh.center_radec[0],
          layerPayload.mesh.center_radec[1],
          layerPayload.title
        );
      }
    } catch (err: any) {
      alert(`Failed to load cached layer: ${err.message}`);
    } finally {
      setActionLoadingId(null);
      setActionStatusText(null);
    }
  };

  // Load an observation as a layer
  const handleLoadObservation = async (obs: SpherexObservationRecord) => {
    const loadingKey = obs.obs_id;
    setActionLoadingId(loadingKey);
    try {
      let filename = obs.local_filename;

      // 1. Download if not cached locally
      if (!obs.is_downloaded || !filename) {
        setActionStatusText(`Downloading ${obs.file_size_mb} MB from IRSA SIA...`);
        const dl = await SpherexService.downloadProduct({
          access_url: obs.access_url,
          obs_id: obs.obs_id,
          detector_band: obs.detector_band,
        });
        filename = dl.filename;
        // Update local search results state
        if (searchResults) {
          setSearchResults({
            ...searchResults,
            observations: searchResults.observations.map((o) =>
              o.obs_id === obs.obs_id
                ? { ...o, is_downloaded: true, local_filename: filename }
                : o
            ),
          });
        }
      }

      // 2. Load into 3D celestial sphere layer
      setActionStatusText("Synthesizing WCS spherical mesh & texture...");
      const layerPayload = await SpherexService.loadLayer({
        filename: filename!,
        stretch,
        radius: 98.0,
      });

      const activeLayer: ActiveImageLayerState = {
        layer_id: layerPayload.layer_id,
        title: layerPayload.title,
        provenance: layerPayload.provenance,
        is_real_data: true,
        observation_id: layerPayload.observation_id,
        detector: layerPayload.detector,
        metadata: layerPayload.metadata,
        mesh: layerPayload.mesh,
        texture_data_uri: layerPayload.texture_data_uri,
        stretch: layerPayload.stretch,
        brightness: layerPayload.brightness,
        contrast: layerPayload.contrast,
        visible: true,
        opacity: 0.9,
      };

      onAddLayer(activeLayer);
      // Center camera on observation
      onNavigateToCoordinates(obs.ra_deg, obs.dec_deg, obs.obs_id);
    } catch (err: any) {
      alert(`Failed to load SPHEREx observation: ${err.message}`);
    } finally {
      setActionLoadingId(null);
      setActionStatusText(null);
    }
  };

  return (
    <>
      <div className="bg-[#050b1a]/90 backdrop-blur-md border border-cyan-500/40 rounded-xl shadow-2xl overflow-hidden transition-all duration-200">
        {/* Panel Header */}
        <div
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center justify-between px-3.5 py-2.5 bg-gradient-to-r from-cyan-950/40 via-[#071329]/80 to-blue-950/40 border-b border-cyan-800/40 cursor-pointer hover:bg-cyan-950/60 transition-colors"
        >
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-400/30 text-cyan-400">
              <Satellite className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-xs tracking-wider uppercase text-cyan-200">
                  NASA SPHEREx Archive
                </span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/40">
                  M4 REAL DATA
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono">
                IRSA SIA2 Live Archive Ingestion
              </p>
            </div>
          </div>
          <button className="text-slate-400 hover:text-cyan-300 transition-colors">
            {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </button>
        </div>

        {/* Panel Body */}
        {!isCollapsed && (
          <div className="p-3.5 space-y-3 font-sans text-xs text-slate-300">
            {/* Real Data Provenance Notice */}
            <div className="p-2 rounded-lg bg-cyan-950/30 border border-cyan-700/40 text-[11px] space-y-1">
              <div className="flex items-center text-cyan-300 font-semibold gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span>Genuine NASA/IPAC Level 2 MEF</span>
              </div>
              <p className="text-[10px] text-slate-400 leading-tight">
                Retrieves real 2040×2040 spectral images with 3rd-order SIP distortion, units in <code className="text-cyan-300">MJy/sr</code>.
              </p>
            </div>

            {/* Target Presets */}
            <div>
              <label className="block text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-1.5">
                Quick Verification Presets
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                {PRESET_TARGETS.map((p) => (
                  <button
                    key={p.name}
                    type="button"
                    onClick={() => applyPreset(p)}
                    className="px-2 py-1 bg-slate-900/80 hover:bg-cyan-950/70 border border-slate-700 hover:border-cyan-500/60 rounded text-[11px] font-mono text-left transition-colors flex items-center justify-between"
                  >
                    <span className="text-slate-200">{p.name}</span>
                    <span className="text-[9px] text-cyan-400/80">{p.collection.replace("spherex_", "")}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Downloaded Real Products in Cache */}
            {cachedProducts.length > 0 && (
              <div className="space-y-1.5 p-2 bg-cyan-950/20 border border-cyan-800/40 rounded-lg">
                <div className="flex items-center justify-between text-[10px] font-mono text-cyan-300">
                  <span className="flex items-center gap-1 font-semibold">
                    <Database className="w-3 h-3 text-cyan-400" />
                    Cached Real NASA Products ({cachedProducts.length})
                  </span>
                  <span className="text-[9px] text-slate-400">READY TO LOAD</span>
                </div>
                {cachedProducts.map((cp) => {
                  const isActing = actionLoadingId === cp.filename;
                  return (
                    <div
                      key={cp.filename}
                      className="p-1.5 bg-slate-900/80 border border-slate-800 rounded flex items-center justify-between text-[10px]"
                    >
                      <div className="min-w-0 pr-1">
                        <div className="font-mono text-cyan-200 truncate font-semibold">
                          {cp.detector || "SPHEREx"} • {cp.obs_id || cp.filename}
                        </div>
                        <div className="text-[9px] text-slate-400 font-mono">
                          {cp.size_mb} MB • Genuine MEF
                        </div>
                      </div>
                      <div className="flex items-center space-x-1 shrink-0">
                        <button
                          type="button"
                          disabled={isActing}
                          onClick={() => handleInspect(cp.filename)}
                          className="px-2 py-0.5 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/50 rounded font-mono text-[9px] flex items-center space-x-1 transition-colors"
                        >
                          <FileCheck2 className="w-3 h-3" />
                          <span>Inspect MEF</span>
                        </button>
                        <button
                          type="button"
                          disabled={isActing}
                          onClick={() => handleLoadDirectCached(cp.filename)}
                          className="px-2 py-0.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-mono text-[9px] flex items-center space-x-1 transition-colors shadow"
                        >
                          {isActing ? (
                            <RefreshCw className="w-3 h-3 animate-spin" />
                          ) : (
                            <Eye className="w-3 h-3" />
                          )}
                          <span>Load Layer</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Search Input Form */}
            <form onSubmit={handleSearch} className="space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] uppercase font-mono text-slate-400 mb-0.5">
                    RA (deg)
                  </label>
                  <input
                    type="text"
                    value={raInput}
                    onChange={(e) => setRaInput(e.target.value)}
                    className="w-full px-2 py-1 bg-slate-950/80 border border-slate-700 focus:border-cyan-400 rounded text-cyan-200 font-mono text-xs outline-none"
                    placeholder="133.795129"
                  />
                </div>
                <div>
                  <label className="block text-[10px] uppercase font-mono text-slate-400 mb-0.5">
                    Dec (deg)
                  </label>
                  <input
                    type="text"
                    value={decInput}
                    onChange={(e) => setDecInput(e.target.value)}
                    className="w-full px-2 py-1 bg-slate-950/80 border border-slate-700 focus:border-cyan-400 rounded text-cyan-200 font-mono text-xs outline-none"
                    placeholder="-7.245147"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] uppercase font-mono text-slate-400 mb-0.5">
                    Radius (deg)
                  </label>
                  <input
                    type="text"
                    value={radiusInput}
                    onChange={(e) => setRadiusInput(e.target.value)}
                    className="w-full px-2 py-1 bg-slate-950/80 border border-slate-700 focus:border-cyan-400 rounded text-cyan-200 font-mono text-xs outline-none"
                    placeholder="0.1"
                  />
                </div>
                <div>
                  <label className="block text-[10px] uppercase font-mono text-slate-400 mb-0.5">
                    Collection
                  </label>
                  <select
                    value={selectedCollection}
                    onChange={(e) => setSelectedCollection(e.target.value)}
                    className="w-full px-2 py-1 bg-slate-950/80 border border-slate-700 focus:border-cyan-400 rounded text-cyan-200 font-mono text-xs outline-none"
                  >
                    <option value="spherex_qr3">spherex_qr3 (Deep/Poles)</option>
                    <option value="spherex_qr2">spherex_qr2 (Wide Coverage)</option>
                    <option value="spherex_qr3_deep">spherex_qr3_deep</option>
                    <option value="spherex_qr2_deep">spherex_qr2_deep</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center space-x-1.5 cursor-pointer text-[10px] text-slate-400 hover:text-slate-300">
                  <input
                    type="checkbox"
                    checked={allowFallback}
                    onChange={(e) => setAllowFallback(e.target.checked)}
                    className="rounded border-slate-700 text-cyan-500 focus:ring-0 bg-slate-900"
                  />
                  <span>Auto-fallback (QR3 → QR2)</span>
                </label>

                <div className="flex items-center space-x-1.5 text-[10px]">
                  <span className="text-slate-400">Stretch:</span>
                  <select
                    value={stretch}
                    onChange={(e) => setStretch(e.target.value as DisplayStretchType)}
                    className="bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-cyan-300 font-mono text-[10px]"
                  >
                    <option value="asinh">Asinh</option>
                    <option value="log">Log</option>
                    <option value="sqrt">Sqrt</option>
                    <option value="linear">Linear</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={isSearching}
                className="w-full mt-2 py-1.5 px-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white font-medium rounded-lg shadow-md hover:shadow-cyan-500/20 flex items-center justify-center space-x-2 transition-all font-mono text-xs"
              >
                {isSearching ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Searching IRSA Archive...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-3.5 h-3.5" />
                    <span>Search IRSA Archive</span>
                  </>
                )}
              </button>
            </form>

            {/* Error Message */}
            {searchError && (
              <div className="p-2 rounded bg-rose-950/40 border border-rose-800/50 text-rose-300 text-[11px] flex items-start gap-1.5">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                <span>{searchError}</span>
              </div>
            )}

            {/* Action Status Bar (When downloading / processing) */}
            {actionStatusText && (
              <div className="p-2 rounded bg-cyan-950/60 border border-cyan-500/40 text-cyan-200 text-[11px] flex items-center gap-2 animate-pulse font-mono">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400 shrink-0" />
                <span>{actionStatusText}</span>
              </div>
            )}

            {/* Search Results List */}
            {searchResults && (
              <div className="space-y-2 pt-1 border-t border-slate-800">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>
                    Found <strong className="text-cyan-300">{searchResults.match_count}</strong> observations
                  </span>
                  <div className="flex items-center space-x-1.5 font-mono text-[9px]">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {searchResults.collection_queried}
                    </span>
                    {searchResults.fallback_triggered && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800/60">
                        FALLBACK ACTIVE
                      </span>
                    )}
                  </div>
                </div>

                {searchResults.match_count === 0 ? (
                  <div className="p-3 text-center text-slate-500 text-xs italic bg-slate-950/40 rounded border border-slate-800/60">
                    No observations found at this position. Try increasing radius or selecting spherex_qr2.
                  </div>
                ) : (
                  <div className="max-h-56 overflow-y-auto space-y-1.5 pr-1">
                    {searchResults.observations.slice(0, 15).map((obs) => {
                      const isActing = actionLoadingId === obs.obs_id || actionLoadingId === obs.local_filename;
                      return (
                        <div
                          key={obs.obs_id}
                          className="p-2 bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-lg transition-all space-y-1.5"
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center space-x-1.5">
                                <span className="font-mono font-semibold text-cyan-300 text-[11px]">
                                  {obs.detector_band}
                                </span>
                                <span className="text-[10px] text-slate-400 font-mono">
                                  {obs.obs_id.length > 22 ? obs.obs_id.slice(0, 22) + "…" : obs.obs_id}
                                </span>
                              </div>
                              <div className="text-[10px] text-slate-500 font-mono">
                                RA: {obs.ra_deg.toFixed(4)}° Dec: {obs.dec_deg.toFixed(4)}° • {obs.file_size_mb} MB
                              </div>
                            </div>

                            <span
                              className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                                obs.is_downloaded
                                  ? "bg-emerald-950/80 text-emerald-300 border-emerald-700/50"
                                  : "bg-slate-800 text-slate-400 border-slate-700"
                              }`}
                            >
                              {obs.is_downloaded ? "CACHED" : "ARCHIVE"}
                            </span>
                          </div>

                          <div className="flex items-center justify-end space-x-1.5 pt-0.5">
                            {/* Fly To */}
                            <button
                              type="button"
                              onClick={() => onNavigateToCoordinates(obs.ra_deg, obs.dec_deg, obs.obs_id)}
                              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-mono text-[10px] flex items-center space-x-1 transition-colors"
                              title="Navigate 3D camera to observation center"
                            >
                              <Compass className="w-3 h-3 text-cyan-400" />
                              <span>Center</span>
                            </button>

                            {/* Inspect (if cached) */}
                            {obs.is_downloaded && obs.local_filename && (
                              <button
                                type="button"
                                disabled={isActing}
                                onClick={() => handleInspect(obs.local_filename!)}
                                className="px-2 py-0.5 bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/50 rounded font-mono text-[10px] flex items-center space-x-1 transition-colors disabled:opacity-50"
                              >
                                <FileCheck2 className="w-3 h-3" />
                                <span>Inspect MEF</span>
                              </button>
                            )}

                            {/* Load / Download & Load */}
                            <button
                              type="button"
                              disabled={isActing}
                              onClick={() => handleLoadObservation(obs)}
                              className="px-2.5 py-0.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded font-mono text-[10px] flex items-center space-x-1 shadow transition-colors"
                            >
                              {isActing ? (
                                <RefreshCw className="w-3 h-3 animate-spin" />
                              ) : obs.is_downloaded ? (
                                <Eye className="w-3 h-3" />
                              ) : (
                                <Download className="w-3 h-3" />
                              )}
                              <span>{obs.is_downloaded ? "Load Layer" : "Download & Load"}</span>
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* MEF Inspection Modal */}
      {inspectModalOpen && inspectionData && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/85 backdrop-blur-md"
          onClick={(e) => {
            if (e.target === e.currentTarget) setInspectModalOpen(false);
          }}
        >
          <div className="bg-[#050b1a] border border-cyan-500/50 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-5 space-y-4 shadow-2xl font-sans text-xs text-slate-300">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-cyan-900/60 pb-3">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-cyan-200">
                    NASA SPHEREx MEF Inspection Report
                  </h3>
                  <p className="text-[10px] font-mono text-slate-400">
                    {inspectionData.filename}
                  </p>
                </div>
              </div>
              <button
                id="close-inspection-modal-btn"
                onClick={() => setInspectModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title="Close inspection modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scientific Attributes Banner */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-[9px] uppercase font-mono text-slate-400 block">Detector</span>
                <span className="text-cyan-300 font-semibold">{inspectionData.detector}</span>
              </div>
              <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-[9px] uppercase font-mono text-slate-400 block">Units</span>
                <span className="text-cyan-300 font-mono">{inspectionData.image_units}</span>
              </div>
              <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-[9px] uppercase font-mono text-slate-400 block">WCS SIP Order</span>
                <span className="text-cyan-300 font-mono">
                  {inspectionData.has_sip ? `Order ${inspectionData.sip_order}` : "None"}
                </span>
              </div>
              <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                <span className="text-[9px] uppercase font-mono text-slate-400 block">File Size</span>
                <span className="text-cyan-300 font-mono">
                  {(inspectionData.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
            </div>

            {/* HDU Table */}
            <div>
              <h4 className="font-mono text-[11px] uppercase tracking-wider text-slate-400 mb-1.5">
                Multi-Extension FITS (MEF) HDU Structure
              </h4>
              <div className="border border-slate-800 rounded-lg overflow-hidden">
                <table className="w-full text-left font-mono text-[10px]">
                  <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-1.5 px-2">#</th>
                      <th className="py-1.5 px-2">Name</th>
                      <th className="py-1.5 px-2">HDU Type</th>
                      <th className="py-1.5 px-2">Dimensions</th>
                      <th className="py-1.5 px-2">DType</th>
                      <th className="py-1.5 px-2">BUnit</th>
                      <th className="py-1.5 px-2 text-right">Cards</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-950/60">
                    {inspectionData.hdus.map((hdu) => (
                      <tr key={hdu.index} className="hover:bg-slate-900/50">
                        <td className="py-1 px-2 text-slate-500">{hdu.index}</td>
                        <td className="py-1 px-2 font-semibold text-cyan-300">{hdu.name}</td>
                        <td className="py-1 px-2 text-slate-400">{hdu.hdu_type}</td>
                        <td className="py-1 px-2 text-slate-300">
                          {hdu.shape ? hdu.shape.join(" × ") : "—"}
                        </td>
                        <td className="py-1 px-2 text-slate-400">{hdu.dtype || "—"}</td>
                        <td className="py-1 px-2 text-slate-400">{hdu.bunit || "—"}</td>
                        <td className="py-1 px-2 text-right text-slate-400">{hdu.card_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Scientific Extensions Verification Summary */}
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800 space-y-1">
                <span className="font-mono text-[10px] uppercase text-slate-400 block font-semibold">
                  Pixel Validity & Flags
                </span>
                <div className="space-y-0.5 font-mono text-[10px] text-slate-300">
                  <div>Finite Pixels: <span className="text-emerald-400">{inspectionData.finite_pixels.toLocaleString()}</span></div>
                  <div>NaN Pixels: <span className="text-amber-400">{inspectionData.nan_pixels.toLocaleString()}</span></div>
                  {inspectionData.flags_summary && (
                    <div>Flagged Artifacts: <span className="text-slate-300">{inspectionData.flags_summary.flagged_pixel_count.toLocaleString()} ({(inspectionData.flags_summary.flagged_ratio * 100).toFixed(2)}%)</span></div>
                  )}
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800 space-y-1">
                <span className="font-mono text-[10px] uppercase text-slate-400 block font-semibold">
                  Uncertainty Variance & Zodi
                </span>
                <div className="space-y-0.5 font-mono text-[10px] text-slate-300">
                  {inspectionData.variance_summary ? (
                    <>
                      <div>Var Min: <span className="text-cyan-300">{inspectionData.variance_summary.min}</span></div>
                      <div>Var Median: <span className="text-cyan-300">{inspectionData.variance_summary.median}</span></div>
                      <div>Units: <span className="text-slate-400">{inspectionData.variance_summary.bunit}</span></div>
                    </>
                  ) : (
                    <div>Variance: <span className="text-slate-500">Not present</span></div>
                  )}
                  <div>Zodi Background: <span className="text-emerald-400">{inspectionData.has_zodi ? "Preserved (un-subtracted)" : "None"}</span></div>
                </div>
              </div>
            </div>

            {/* Integrity Hash */}
            <div className="p-2 rounded bg-slate-950 border border-slate-800 space-y-1 font-mono text-[10px]">
              <div className="text-slate-400">SHA-256 Checksum:</div>
              <div className="text-cyan-300 break-all select-all">{inspectionData.sha256}</div>
            </div>

            {/* Footer */}
            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setInspectModalOpen(false)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-mono text-xs transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
