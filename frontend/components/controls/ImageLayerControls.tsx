"use client";

import React, { useState, useEffect } from "react";
import {
  Layers,
  Eye,
  EyeOff,
  Trash2,
  Upload,
  Info,
  ChevronDown,
  ChevronUp,
  Sliders,
  Compass,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import {
  ActiveImageLayerState,
  SampleImageInfo,
  DisplayStretchType,
} from "@/types/astronomicalImage";
import {
  fetchSampleImages,
  loadSampleImageLayer,
  uploadFitsImageLayer,
  updateImageDisplayStretch,
} from "@/services/imageService";

export interface ImageLayerControlsProps {
  layers: ActiveImageLayerState[];
  onAddLayer: (layer: ActiveImageLayerState) => void;
  onUpdateLayer: (layerId: string, updates: Partial<ActiveImageLayerState>) => void;
  onRemoveLayer: (layerId: string) => void;
  onNavigateToCoordinates: (ra: number, dec: number, label?: string) => void;
}

export function ImageLayerControls({
  layers,
  onAddLayer,
  onUpdateLayer,
  onRemoveLayer,
  onNavigateToCoordinates,
}: ImageLayerControlsProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sampleList, setSampleList] = useState<SampleImageInfo[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>("wise-0855");
  const [selectedStretch, setSelectedStretch] = useState<DisplayStretchType>("asinh");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetadataLayer, setSelectedMetadataLayer] = useState<ActiveImageLayerState | null>(null);

  // Load sample options on mount
  useEffect(() => {
    fetchSampleImages()
      .then((data) => {
        setSampleList(data);
        if (data.length > 0) setSelectedSampleId(data[0].id);
      })
      .catch((err) => {
        console.warn("Could not fetch sample images list from backend:", err.message);
      });
  }, []);

  // Handle Load Sample
  const handleLoadSample = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await loadSampleImageLayer(selectedSampleId, selectedStretch, 1.0, 1.0);
      const newLayer: ActiveImageLayerState = {
        ...data,
        visible: true,
        opacity: 0.85,
      };
      onAddLayer(newLayer);
    } catch (err: any) {
      setError(err?.message || "Failed to load sample image");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);
    try {
      const data = await uploadFitsImageLayer(file, selectedStretch, 1.0, 1.0);
      const newLayer: ActiveImageLayerState = {
        ...data,
        visible: true,
        opacity: 0.85,
      };
      onAddLayer(newLayer);
    } catch (err: any) {
      setError(err?.message || "Failed to upload and process FITS image");
    } finally {
      setIsLoading(false);
      // Reset input value
      e.target.value = "";
    }
  };

  // Handle Stretch change on an active layer
  const handleStretchChange = async (layerId: string, newStretch: DisplayStretchType) => {
    const targetLayer = layers.find((l) => l.layer_id === layerId);
    if (!targetLayer) return;

    onUpdateLayer(layerId, { stretch: newStretch, isLoading: true });
    try {
      const newUri = await updateImageDisplayStretch(
        layerId,
        newStretch,
        targetLayer.brightness,
        targetLayer.contrast
      );
      onUpdateLayer(layerId, { texture_data_uri: newUri, isLoading: false });
    } catch (err) {
      console.error("Failed to update stretch:", err);
      onUpdateLayer(layerId, { isLoading: false });
    }
  };

  // Handle Brightness/Contrast adjustment
  const handleAdjustDisplay = async (layerId: string, brightness: number, contrast: number) => {
    const targetLayer = layers.find((l) => l.layer_id === layerId);
    if (!targetLayer) return;

    onUpdateLayer(layerId, { brightness, contrast });
    try {
      const newUri = await updateImageDisplayStretch(
        layerId,
        targetLayer.stretch,
        brightness,
        contrast
      );
      onUpdateLayer(layerId, { texture_data_uri: newUri });
    } catch (err) {
      console.error("Failed to adjust display:", err);
    }
  };

  return (
    <div className="bg-[#050b1a]/95 backdrop-blur-md border border-cyan-950/80 rounded-xl shadow-2xl font-mono text-xs text-slate-200 select-none overflow-hidden transition-all duration-300">
      {/* Header Bar */}
      <div className="px-3 py-2 bg-[#071026] border-b border-cyan-950/70 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span className="font-semibold text-cyan-200 tracking-wide">
            Astronomical Image Layers
          </span>
          <span className="text-[10px] bg-cyan-950/80 text-cyan-400 border border-cyan-800/50 px-1.5 py-0.2 rounded font-bold">
            M3
          </span>
        </div>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-slate-400 hover:text-cyan-300 transition-colors p-1"
          title={isCollapsed ? "Expand Panel" : "Collapse Panel"}
        >
          {isCollapsed ? (
            <ChevronDown className="w-3.5 h-3.5" />
          ) : (
            <ChevronUp className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {!isCollapsed && (
        <div className="p-3 space-y-3">
          {/* Sample Loader & Upload Section */}
          <div className="space-y-2">
            <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider flex items-center justify-between">
              <span>Load Astronomical Product</span>
            </div>

            {/* Sample Selector */}
            <div className="flex items-center space-x-1.5">
              <select
                value={selectedSampleId}
                onChange={(e) => setSelectedSampleId(e.target.value)}
                disabled={isLoading}
                className="flex-1 px-2 py-1.5 bg-[#02040b] border border-cyan-900/50 rounded-lg text-xs font-mono text-cyan-100 focus:outline-none focus:border-cyan-400"
              >
                {sampleList.length > 0 ? (
                  sampleList.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.title}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="wise-0855">WISE 0855 Field (TAN)</option>
                    <option value="equatorial-cal">Equatorial Cal (RA 0°, Dec 0°)</option>
                    <option value="polar-demonstration">Polar Field (Dec +89.5°)</option>
                    <option value="ra-wraparound">RA Wraparound Field</option>
                  </>
                )}
              </select>

              <button
                type="button"
                onClick={handleLoadSample}
                disabled={isLoading}
                className="px-3 py-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white font-medium rounded-lg text-xs transition-all shadow-[0_0_8px_rgba(6,182,212,0.3)] active:scale-95 flex items-center space-x-1"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{isLoading ? "Loading..." : "Load"}</span>
              </button>
            </div>

            {/* Custom FITS File Upload Button */}
            <div className="relative">
              <input
                type="file"
                accept=".fits,.fit,.fts"
                onChange={handleFileUpload}
                disabled={isLoading}
                id="fits-upload-input"
                className="hidden"
              />
              <label
                htmlFor="fits-upload-input"
                className="w-full py-1.5 px-2 bg-[#09152e] hover:bg-cyan-950/80 border border-cyan-900/60 border-dashed rounded-lg flex items-center justify-center space-x-1.5 text-[11px] text-cyan-300 cursor-pointer transition-colors"
              >
                <Upload className="w-3.5 h-3.5 text-cyan-400" />
                <span>Upload 2D FITS Image (.fits, .fit)</span>
              </label>
            </div>

            {error && (
              <div className="flex items-center space-x-1.5 p-1.5 bg-rose-950/50 border border-rose-800/60 rounded text-[10px] text-rose-300">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* Active Image Layers List */}
          <div className="pt-2 border-t border-cyan-950/60 space-y-2">
            <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider flex items-center justify-between">
              <span>Active Image Layers</span>
              <span className="text-cyan-400 font-bold">{layers.length}</span>
            </div>

            {layers.length === 0 ? (
              <div className="text-[11px] text-slate-500 italic p-2 text-center bg-[#02050f] rounded-lg border border-cyan-950/40">
                No astronomical image layers loaded. Select a demonstration sample above to project onto the celestial sphere.
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
                {layers.map((layer) => (
                  <div
                    key={layer.layer_id}
                    className="p-2 bg-[#04091a] border border-cyan-900/50 rounded-lg space-y-2"
                  >
                    {/* Layer Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0 pr-2">
                        <div className="flex items-center space-x-1.5 mb-0.5">
                          {layer.is_real_data || layer.provenance.includes("NASA") ? (
                            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-500/50 flex items-center gap-1 font-semibold">
                              <CheckCircle2 className="w-2.5 h-2.5 text-cyan-400" />
                              NASA SPHEREx (Real Data)
                            </span>
                          ) : (
                            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-slate-900 text-slate-400 border border-slate-700">
                              Synthetic Test Fixture
                            </span>
                          )}
                        </div>
                        <div className="font-semibold text-cyan-200 text-[11px] truncate" title={layer.title}>
                          {layer.title}
                        </div>
                        <div className="text-[9px] text-amber-300/80 italic truncate">
                          {layer.provenance}
                        </div>
                      </div>

                      <div className="flex items-center space-x-1">
                        {/* Fly to center */}
                        <button
                          type="button"
                          onClick={() =>
                            onNavigateToCoordinates(
                              layer.mesh.center_radec[0],
                              layer.mesh.center_radec[1],
                              layer.title
                            )
                          }
                          title="Fly Camera to Image Center"
                          className="p-1 hover:bg-cyan-950/70 text-slate-400 hover:text-cyan-300 rounded transition-colors"
                        >
                          <Compass className="w-3.5 h-3.5" />
                        </button>

                        {/* Metadata inspect */}
                        <button
                          type="button"
                          onClick={() => setSelectedMetadataLayer(layer)}
                          title="Inspect FITS & WCS Metadata"
                          className="p-1 hover:bg-cyan-950/70 text-slate-400 hover:text-cyan-300 rounded transition-colors"
                        >
                          <Info className="w-3.5 h-3.5" />
                        </button>

                        {/* Visibility toggle */}
                        <button
                          type="button"
                          onClick={() => onUpdateLayer(layer.layer_id, { visible: !layer.visible })}
                          title={layer.visible ? "Hide Layer" : "Show Layer"}
                          className="p-1 hover:bg-cyan-950/70 text-slate-400 hover:text-cyan-300 rounded transition-colors"
                        >
                          {layer.visible ? (
                            <Eye className="w-3.5 h-3.5 text-cyan-400" />
                          ) : (
                            <EyeOff className="w-3.5 h-3.5 text-slate-600" />
                          )}
                        </button>

                        {/* Remove layer */}
                        <button
                          type="button"
                          onClick={() => onRemoveLayer(layer.layer_id)}
                          title="Remove Image Layer"
                          className="p-1 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 rounded transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Display Stretch Selector */}
                    <div>
                      <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                        <span>Display Stretch:</span>
                        <span className="text-cyan-400 uppercase font-semibold text-[9px]">
                          {layer.stretch}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-1">
                        {(["asinh", "log", "linear"] as DisplayStretchType[]).map((st) => (
                          <button
                            key={st}
                            type="button"
                            onClick={() => handleStretchChange(layer.layer_id, st)}
                            className={`py-0.5 rounded text-[10px] font-medium uppercase border transition-colors ${
                              layer.stretch === st
                                ? "bg-cyan-950/90 border-cyan-500 text-cyan-200"
                                : "bg-[#02050f] border-cyan-950/70 text-slate-500 hover:text-slate-300"
                            }`}
                          >
                            {st}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Opacity Slider */}
                    <div>
                      <div className="flex justify-between items-center text-[10px] text-slate-400 mb-0.5">
                        <span>Opacity:</span>
                        <span className="text-cyan-300 font-mono">
                          {Math.round(layer.opacity * 100)}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0.05"
                        max="1.0"
                        step="0.05"
                        value={layer.opacity}
                        onChange={(e) =>
                          onUpdateLayer(layer.layer_id, { opacity: parseFloat(e.target.value) })
                        }
                        className="w-full h-1 bg-[#02040b] rounded-lg appearance-none cursor-pointer accent-cyan-400"
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Metadata Inspector Drawer / Modal */}
      {selectedMetadataLayer && (
        <div className="p-3 bg-[#030714] border-t border-cyan-900/50 space-y-2 text-[10px]">
          <div className="flex items-center justify-between pb-1 border-b border-cyan-950/60 font-semibold text-cyan-300">
            <span>FITS & WCS Metadata</span>
            <button
              onClick={() => setSelectedMetadataLayer(null)}
              className="text-slate-500 hover:text-rose-300"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-slate-400 font-mono">
            <div>
              Dimensions:{" "}
              <span className="text-cyan-200">
                {selectedMetadataLayer.metadata.dimensions[0]} &times; {selectedMetadataLayer.metadata.dimensions[1]}
              </span>
            </div>
            <div>
              Projection:{" "}
              <span className="text-cyan-200">
                {selectedMetadataLayer.metadata.wcs.projection_type}
              </span>
            </div>
            <div>
              Center RA:{" "}
              <span className="text-cyan-200">
                {selectedMetadataLayer.metadata.wcs.center_radec[0].toFixed(4)}°
              </span>
            </div>
            <div>
              Center Dec:{" "}
              <span className="text-cyan-200">
                {selectedMetadataLayer.metadata.wcs.center_radec[1].toFixed(4)}°
              </span>
            </div>
            <div>
              Pixel Scale:{" "}
              <span className="text-cyan-200">
                {selectedMetadataLayer.metadata.wcs.pixel_scale_arcsec}"/px
              </span>
            </div>
            <div>
              Residual:{" "}
              <span className="text-emerald-400">
                {selectedMetadataLayer.metadata.wcs.round_trip_residual_pixels.toExponential(2)} px
              </span>
            </div>
          </div>

          <div className="pt-1 border-t border-cyan-950/40 text-slate-400">
            <span className="font-semibold text-slate-300">Footprint Corners (RA, Dec):</span>
            <div className="grid grid-cols-2 gap-1 mt-0.5 text-[9px] text-cyan-300/90 font-mono">
              {selectedMetadataLayer.metadata.wcs.footprint_corners.map((c, i) => (
                <div key={i}>
                  C{i + 1}: {c[0].toFixed(4)}°, {c[1].toFixed(4)}°
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
