import { create } from "zustand";
import {
  AstronomicalTargetDetail,
  ObservationEpoch,
  SpectralBand,
  SpectralMeasurement,
  DifferenceAnalysisResult,
  CoordinateResponse,
} from "../types/astronomy";
import {
  parseCoordinates,
  fetchValidationTargets,
  fetchObservations,
  fetchSpectralBands,
  fetchSpectralProfile,
  runDifferenceAnalysis,
} from "../services/api";

interface SkyStoreState {
  // Navigation & Coordinates
  raDeg: number;
  decDeg: number;
  fovDeg: number;
  raHms: string;
  decDms: string;
  galacticL: number;
  galacticB: number;
  eclipticLon: number;
  eclipticLat: number;

  // Selected Target
  selectedTarget: AstronomicalTargetDetail | null;
  validationTargets: AstronomicalTargetDetail[];
  isTargetLoading: boolean;

  // Temporal & Observations
  epochs: ObservationEpoch[];
  epochIndex: number;
  selectedEpoch: ObservationEpoch | null;
  comparisonEpoch: ObservationEpoch | null;
  comparisonMode: "single" | "blink" | "split" | "difference";
  isPlaying: boolean;
  playbackSpeed: number; // 0.5, 1, 2, 4
  diffResult: DifferenceAnalysisResult | null;
  isDiffLoading: boolean;
  imageStretch: "asinh" | "linear" | "log" | "sqrt";
  imageColormap: "astronomy" | "gray";

  // Spectral
  bands: SpectralBand[];
  selectedChannel: number;
  spectralProfile: SpectralMeasurement[];
  isSpectralLoading: boolean;

  // 3D Visualization Layers
  showGrid: boolean;
  showConstellations: boolean;
  showGalacticPlane: boolean;
  showEcliptic: boolean;
  showCoverage: boolean;
  showCutoutOverlay: boolean;
  cameraFlightTrigger: number; // incremented to trigger camera animation

  // UI Panels
  activeTab: "sky" | "temporal" | "spectral" | "targets" | "about";
  sidebarCollapsed: boolean;
  bottomPanelCollapsed: boolean;

  // Actions
  setCoordinates: (ra: number, dec: number, fov?: number) => void;
  setCoordinateStrings: (raStr: string, decStr: string) => Promise<void>;
  selectTarget: (target: AstronomicalTargetDetail | string) => Promise<void>;
  setSelectedEpochIndex: (index: number) => void;
  nextEpoch: () => void;
  prevEpoch: () => void;
  togglePlay: () => void;
  setPlaybackSpeed: (speed: number) => void;
  setComparisonMode: (mode: "single" | "blink" | "split" | "difference") => void;
  setSelectedChannel: (channel: number) => void;
  setImageStretch: (stretch: "asinh" | "linear" | "log" | "sqrt") => void;
  setImageColormap: (colormap: "astronomy" | "gray") => void;
  toggleLayer: (layer: "showGrid" | "showConstellations" | "showGalacticPlane" | "showEcliptic" | "showCoverage" | "showCutoutOverlay") => void;
  setActiveTab: (tab: "sky" | "temporal" | "spectral" | "targets" | "about") => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setBottomPanelCollapsed: (collapsed: boolean) => void;
  triggerDifferenceAnalysis: () => Promise<void>;
  initializeStore: () => Promise<void>;
  resetCamera: () => void;
}

export const useSkyStore = create<SkyStoreState>((set, get) => ({
  // Default coordinates: WISE 0855 (coldest Y-dwarf)
  raDeg: 133.7951,
  decDeg: -7.2451,
  fovDeg: 0.5,
  raHms: "08h 55m 10.83s",
  decDms: "-07° 14' 42.50\"",
  galacticL: 232.42,
  galacticB: 23.95,
  eclipticLon: 139.12,
  eclipticLat: -24.81,

  selectedTarget: null,
  validationTargets: [],
  isTargetLoading: false,

  epochs: [],
  epochIndex: 0,
  selectedEpoch: null,
  comparisonEpoch: null,
  comparisonMode: "single",
  isPlaying: false,
  playbackSpeed: 1,
  diffResult: null,
  isDiffLoading: false,
  imageStretch: "asinh",
  imageColormap: "astronomy",

  bands: [],
  selectedChannel: 50, // Array 4, ~3.12 um
  spectralProfile: [],
  isSpectralLoading: false,

  showGrid: true,
  showConstellations: true,
  showGalacticPlane: true,
  showEcliptic: true,
  showCoverage: true,
  showCutoutOverlay: true,
  cameraFlightTrigger: 0,

  activeTab: "sky",
  sidebarCollapsed: false,
  bottomPanelCollapsed: false,

  setCoordinates: (ra, dec, fov) => {
    set((state) => ({
      raDeg: (ra % 360 + 360) % 360,
      decDeg: Math.max(-90, Math.min(90, dec)),
      fovDeg: fov !== undefined ? fov : state.fovDeg,
      cameraFlightTrigger: state.cameraFlightTrigger + 1,
    }));
  },

  setCoordinateStrings: async (raStr, decStr) => {
    try {
      const parsed = await parseCoordinates(raStr, decStr);
      set((state) => ({
        raDeg: parsed.ra_deg,
        decDeg: parsed.dec_deg,
        raHms: parsed.ra_hms,
        decDms: parsed.dec_dms,
        galacticL: parsed.galactic_l_deg,
        galacticB: parsed.galactic_b_deg,
        eclipticLon: parsed.ecliptic_lon_deg,
        eclipticLat: parsed.ecliptic_lat_deg,
        cameraFlightTrigger: state.cameraFlightTrigger + 1,
      }));

      // Refresh observations and spectra for this location
      const epochs = await fetchObservations({
        ra: parsed.ra_deg,
        dec: parsed.dec_deg,
        channel: get().selectedChannel,
      });
      const spectra = await fetchSpectralProfile({
        ra: parsed.ra_deg,
        dec: parsed.dec_deg,
      });

      set({
        epochs,
        epochIndex: 0,
        selectedEpoch: epochs[0] || null,
        comparisonEpoch: epochs[1] || null,
        spectralProfile: spectra,
        selectedTarget: null,
      });
    } catch (err) {
      console.error("Failed to parse coordinates:", err);
      throw err;
    }
  },

  selectTarget: async (targetInput) => {
    set({ isTargetLoading: true });
    try {
      let target: AstronomicalTargetDetail | null = null;
      if (typeof targetInput === "string") {
        const found = get().validationTargets.find(
          (t) => t.id === targetInput || t.name.toLowerCase() === targetInput.toLowerCase()
        );
        target = found || null;
      } else {
        target = targetInput;
      }

      if (target) {
        set((state) => ({
          selectedTarget: target,
          raDeg: target.ra_deg,
          decDeg: target.dec_deg,
          raHms: target.ra_hms,
          decDms: target.dec_dms,
          epochs: target.available_epochs,
          epochIndex: 0,
          selectedEpoch: target.available_epochs[0] || null,
          comparisonEpoch: target.available_epochs[1] || null,
          spectralProfile: target.spectral_profile,
          cameraFlightTrigger: state.cameraFlightTrigger + 1,
          diffResult: null,
        }));
      }
    } catch (err) {
      console.error("Failed to select target:", err);
    } finally {
      set({ isTargetLoading: false });
    }
  },

  setSelectedEpochIndex: (index) => {
    const { epochs } = get();
    if (index >= 0 && index < epochs.length) {
      set({
        epochIndex: index,
        selectedEpoch: epochs[index],
      });
    }
  },

  nextEpoch: () => {
    const { epochs, epochIndex } = get();
    if (epochs.length > 0) {
      const nextIdx = (epochIndex + 1) % epochs.length;
      set({
        epochIndex: nextIdx,
        selectedEpoch: epochs[nextIdx],
      });
    }
  },

  prevEpoch: () => {
    const { epochs, epochIndex } = get();
    if (epochs.length > 0) {
      const prevIdx = (epochIndex - 1 + epochs.length) % epochs.length;
      set({
        epochIndex: prevIdx,
        selectedEpoch: epochs[prevIdx],
      });
    }
  },

  togglePlay: () => {
    set((state) => ({ isPlaying: !state.isPlaying }));
  },

  setPlaybackSpeed: (speed) => {
    set({ playbackSpeed: speed });
  },

  setComparisonMode: (mode) => {
    set({ comparisonMode: mode });
    if (mode === "difference") {
      get().triggerDifferenceAnalysis();
    }
  },

  setSelectedChannel: (channel) => {
    set({ selectedChannel: channel });
  },

  setImageStretch: (stretch) => {
    set({ imageStretch: stretch });
  },

  setImageColormap: (colormap) => {
    set({ imageColormap: colormap });
  },

  toggleLayer: (layer) => {
    set((state) => ({ [layer]: !state[layer] }));
  },

  setActiveTab: (tab) => {
    set({ activeTab: tab });
  },

  setSidebarCollapsed: (collapsed) => {
    set({ sidebarCollapsed: collapsed });
  },

  setBottomPanelCollapsed: (collapsed) => {
    set({ bottomPanelCollapsed: collapsed });
  },

  triggerDifferenceAnalysis: async () => {
    const { selectedTarget, raDeg, decDeg, selectedEpoch, comparisonEpoch, selectedChannel } = get();
    const epRef = selectedEpoch?.epoch_id || "EPOCH-PASS1-20250615";
    const epCmp = comparisonEpoch?.epoch_id || "EPOCH-PASS2-20251214";

    set({ isDiffLoading: true });
    try {
      const res = await runDifferenceAnalysis({
        target: selectedTarget?.id,
        ra: raDeg,
        dec: decDeg,
        epoch_ref: epRef,
        epoch_cmp: epCmp,
        channel: selectedChannel,
        sigma_threshold: 3.5,
      });
      set({ diffResult: res });
    } catch (err) {
      console.error("Failed to execute difference analysis:", err);
    } finally {
      set({ isDiffLoading: false });
    }
  },

  resetCamera: () => {
    set((state) => ({
      raDeg: 133.7951,
      decDeg: -7.2451,
      fovDeg: 0.5,
      cameraFlightTrigger: state.cameraFlightTrigger + 1,
    }));
  },

  initializeStore: async () => {
    try {
      const [targets, bands] = await Promise.all([
        fetchValidationTargets(),
        fetchSpectralBands(),
      ]);

      set({
        validationTargets: targets,
        bands,
      });

      // Select WISE 0855 as initial verified target
      const wise0855 = targets.find((t) => t.id === "wise-0855") || targets[0];
      if (wise0855) {
        await get().selectTarget(wise0855);
      }
    } catch (err) {
      console.error("Store initialization error:", err);
    }
  },
}));
