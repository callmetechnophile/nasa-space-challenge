"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useSkyStore } from "@/stores/useSkyStore";
import { discoverTimeSeries, getCutoutUrl } from "@/services/api";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Repeat,
  Download,
  AlertTriangle,
  Compass,
  Clock,
  Layers,
  Sparkles,
  Info,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  XCircle,
} from "lucide-react";

export interface TargetPreset {
  id: string;
  name: string;
  designation: string;
  raDeg: number;
  decDeg: number;
  raHms: string;
  decDms: string;
  description: string;
}

export const NASA_5_TARGETS: TargetPreset[] = [
  {
    id: "barnards-star",
    name: "Barnard's Star",
    designation: "GJ 699",
    raDeg: 269.452083,
    decDeg: 4.693333,
    raHms: "17h 57m 48.50s",
    decDms: "+04° 41' 36.00\"",
    description: "High-proper-motion M-dwarf (10.37\"/yr displacement)",
  },
  {
    id: "epsilon-indi-b",
    name: "Epsilon Indi B",
    designation: "HD 209100 B",
    raDeg: 331.043792,
    decDeg: -56.782722,
    raHms: "22h 04m 10.51s",
    decDms: "-56° 46' 57.80\"",
    description: "T-dwarf binary companion (0.73\" sep, unresolved at 6.2\" PSF)",
  },
  {
    id: "wise-0855",
    name: "WISE 0855",
    designation: "WISE J085510.83-071442.5",
    raDeg: 133.795129,
    decDeg: -7.245147,
    raHms: "08h 55m 10.831s",
    decDms: "-07° 14' 42.53\"",
    description: "Coldest known Y-dwarf brown dwarf, high proper motion",
  },
  {
    id: "rw-aurigae",
    name: "RW Aurigae",
    designation: "RW Aur",
    raDeg: 76.956417,
    decDeg: 30.401417,
    raHms: "05h 07m 49.54s",
    decDms: "+30° 24' 05.10\"",
    description: "Variable young T Tauri star with circumstellar dust dimming",
  },
  {
    id: "r-draconis",
    name: "R Draconis",
    designation: "R Dra",
    raDeg: 248.167625,
    decDeg: 66.755056,
    raHms: "16h 32m 40.23s",
    decDms: "+66° 45' 18.20\"",
    description: "Mira pulsating giant star (P=245.6d, large amplitude variability)",
  },
];

export function TimeSeriesPlayer() {
  const raDeg = useSkyStore((s) => s.raDeg);
  const decDeg = useSkyStore((s) => s.decDeg);
  const setCoordinates = useSkyStore((s) => s.setCoordinates);
  const imageStretch = useSkyStore((s) => s.imageStretch);
  const imageColormap = useSkyStore((s) => s.imageColormap);
  const selectedChannel = useSkyStore((s) => s.selectedChannel);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const selectTarget = useSkyStore((s) => s.selectTarget);

  // Discovery state with 6-decimal precision
  const [inputRa, setInputRa] = useState<string>(raDeg.toFixed(6));
  const [inputDec, setInputDec] = useState<string>(decDeg.toFixed(6));
  const [activeTargetName, setActiveTargetName] = useState<string | null>("WISE 0855");
  const [isDiscovering, setIsDiscovering] = useState<boolean>(false);
  const [discoveryData, setDiscoveryData] = useState<any | null>(null);
  const [frames, setFrames] = useState<any[]>([]);
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);
  const [lastQueryTime, setLastQueryTime] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<{
    statusText: string;
    message: string;
    httpStatus?: number;
    classification?: string;
  } | null>(null);

  // Playback state
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0); // 0.5, 1, 2, 4, 5
  const [isLooping, setIsLooping] = useState<boolean>(true);
  const [archiveStatusNote, setArchiveStatusNote] = useState<string | null>(null);

  // Blink comparator mode
  const [isBlinkActive, setIsBlinkActive] = useState<boolean>(false);
  const [blinkState, setBlinkState] = useState<"ref" | "cur">("cur");

  // In-flight abort controller
  const abortControllerRef = useRef<AbortController | null>(null);

  // Sync input fields when store coordinates change externally
  useEffect(() => {
    setInputRa(raDeg.toFixed(6));
    setInputDec(decDeg.toFixed(6));
  }, [raDeg, decDeg]);

  // Sync active target name when store target changes
  useEffect(() => {
    if (selectedTarget) {
      setActiveTargetName(selectedTarget.name);
    }
  }, [selectedTarget]);

  // Mount discovery is handled by useSkyStore.initializeStore(); removed duplicate call.

  const executeDiscovery = async (
    ra: number,
    dec: number,
    targetName?: string,
    forceRefresh: boolean = false
  ) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsDiscovering(true);
    setIsPlaying(false);
    setArchiveStatusNote(null);
    setQueryError(null);
    setLastQueryTime(new Date().toISOString());

    try {
      const data = await discoverTimeSeries({
        ra,
        dec,
        fov_deg: 0.5,
        release: "all",
        use_cache: !forceRefresh,
        force_refresh: forceRefresh,
        signal: controller.signal,
      });

      setDiscoveryData(data);
      const obs = data.observations || [];
      setFrames(obs);
      setCurrentFrameIndex(0);
      if (targetName) {
        setActiveTargetName(targetName);
      } else {
        setActiveTargetName(null);
      }

      const failedStates = [
        "ARCHIVE_QUERY_FAILED",
        "ARCHIVE_QUERY_TIMEOUT",
        "ARCHIVE_QUERY_RATE_LIMITED",
        "ARCHIVE_SERVICE_UNAVAILABLE",
      ];

      if (failedStates.includes(data.discovery_state)) {
        const errCollection = Object.values(data.archive_queries || {}).find(
          (q: any) => failedStates.includes(q?.status)
        ) as any;

        setQueryError({
          statusText: data.discovery_state,
          message:
            errCollection?.message ||
            data.message ||
            "Archive query failed to retrieve catalog records from IRSA.",
          httpStatus: errCollection?.http_status,
          classification: errCollection?.classification,
        });
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        return;
      }
      console.warn("Discovery failed:", err);
      setDiscoveryData({
        discovery_state: "ARCHIVE_QUERY_FAILED",
        temporal_coverage_status: "UNVERIFIED",
        observations: [],
      });
      setFrames([]);
      setQueryError({
        statusText: "ARCHIVE_QUERY_FAILED",
        message: err.message || "Failed to communicate with archive discovery endpoint",
      });
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleSelectPreset = async (target: TargetPreset) => {
    setInputRa(target.raDeg.toFixed(6));
    setInputDec(target.decDeg.toFixed(6));
    setActiveTargetName(target.name);
    await selectTarget(target.id);
    executeDiscovery(target.raDeg, target.decDeg, target.name, false);
  };

  const handleCustomSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const r = parseFloat(inputRa);
    const d = parseFloat(inputDec);
    if (isNaN(r) || isNaN(d) || r < 0 || r > 360 || d < -90 || d > 90) {
      alert("Please enter valid decimal coordinates: RA [0, 360], Dec [-90, +90].");
      return;
    }
    setActiveTargetName(null);
    setCoordinates(r, d, 0.5);
    executeDiscovery(r, d, undefined, false);
  };

  // Playback timer loop
  useEffect(() => {
    if (!isPlaying || frames.length <= 1) return;

    const intervalMs = Math.max(200, 1500 / playbackSpeed);
    const timer = setInterval(() => {
      setCurrentFrameIndex((prev) => {
        if (prev + 1 >= frames.length) {
          if (isLooping) {
            return 0;
          } else {
            setIsPlaying(false);
            return prev;
          }
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isPlaying, frames.length, playbackSpeed, isLooping]);

  // Blink comparator timer
  useEffect(() => {
    if (!isBlinkActive || frames.length < 2) return;
    const timer = setInterval(() => {
      setBlinkState((prev) => (prev === "ref" ? "cur" : "ref"));
    }, 500);
    return () => clearInterval(timer);
  }, [isBlinkActive, frames.length]);

  const activeFrame = frames.length > 0 ? frames[currentFrameIndex] : null;
  const refFrame = frames.length > 0 ? frames[0] : null;

  const displayedFrame = isBlinkActive
    ? blinkState === "ref"
      ? refFrame
      : activeFrame
    : activeFrame;

  const handleDownloadMetadata = () => {
    const payload = {
      export_timestamp: new Date().toISOString(),
      target_name: activeTargetName || "CUSTOM_COORDINATES",
      ra_deg: parseFloat(inputRa),
      dec_deg: parseFloat(inputDec),
      total_observations_found: frames.length,
      coverage_status: discoveryData?.coverage_status || "UNKNOWN",
      archive_queries: discoveryData?.archive_queries || {},
      observations: frames,
      disclaimer: "NOTICE: Observed Data | Processed Images | Synthetic Test Data | Change Candidates — NOT SCIENTIFICALLY CONFIRMED. Unverified candidates are not astronomical discoveries.",
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `spherex_observations_${activeTargetName ? activeTargetName.replace(/\s+/g, "_").toLowerCase() : "custom"}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Generate cutout preview URL
  const previewCutoutUrl = activeFrame
    ? getCutoutUrl({
        ra: parseFloat(inputRa),
        dec: parseFloat(inputDec),
        epoch: activeFrame.obs_id || "EPOCH-1",
        channel: selectedChannel,
        stretch: imageStretch,
        colormap: imageColormap,
        fov_arcmin: 6.0,
      })
    : null;

  return (
    <div className="pt-2 space-y-3 font-sans text-xs">
      {/* 1. Mandatory Non-Discovery Notice Banner */}
      <div className="bg-amber-950/40 border border-amber-500/60 rounded-lg p-2.5 text-amber-200 flex items-start space-x-2 text-[11px] leading-relaxed">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <strong className="font-semibold text-amber-300">
            NOTICE: Observed Data | Processed Images | Synthetic Test Data | Change Candidates — NOT SCIENTIFICALLY CONFIRMED.
          </strong>{" "}
          Unverified candidates are not astronomical discoveries. Differences may arise from point spread variations, spectral gradients, or instrumental artifacts.
        </div>
      </div>

      {/* 2. Target Presets Quick-Bar */}
      <div className="bg-[#09152e]/80 border border-cyan-950 rounded-lg p-2.5">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-300 mb-2">
          <span className="flex items-center space-x-1.5 text-cyan-400 font-semibold">
            <Compass className="w-3.5 h-3.5" />
            <span>NASA SPHEREx 5-Target Challenge Presets:</span>
          </span>
          <span className="text-[10px] text-slate-400">Click to load chronological series</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-1.5 font-mono">
          {NASA_5_TARGETS.map((t) => {
            const isSelected =
              selectedTarget?.name === t.name ||
              activeTargetName === t.name ||
              (Math.abs(raDeg - t.raDeg) < 0.005 && Math.abs(decDeg - t.decDeg) < 0.005);
            return (
              <button
                key={t.id}
                onClick={() => handleSelectPreset(t)}
                className={`p-1.5 rounded border text-left transition-all ${
                  isSelected
                    ? "bg-cyan-950 border-cyan-400 text-cyan-200 shadow-[0_0_8px_rgba(6,182,212,0.3)]"
                    : "bg-[#050b1a] border-cyan-900/60 text-slate-400 hover:text-slate-200 hover:border-cyan-700"
                }`}
              >
                <div className="font-bold text-[11px] truncate text-cyan-300">
                  {t.name}
                </div>
                <div className="text-[9px] text-slate-400 truncate">
                  {t.designation}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Coordinate Entry & Discovery Bar */}
      <form
        onSubmit={handleCustomSearch}
        className="flex flex-wrap items-center justify-between gap-2 bg-[#09152e]/70 p-2.5 rounded-lg border border-cyan-950 font-mono text-[11px]"
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-slate-400">Coordinates:</span>
          <div className="flex items-center space-x-1">
            <span className="text-cyan-400">RA°</span>
            <input
              type="text"
              value={inputRa}
              onChange={(e) => setInputRa(e.target.value)}
              placeholder="e.g. 133.7951"
              className="w-28 bg-[#050b1a] border border-cyan-900/80 rounded px-2 py-0.5 text-cyan-300 focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div className="flex items-center space-x-1">
            <span className="text-cyan-400">Dec°</span>
            <input
              type="text"
              value={inputDec}
              onChange={(e) => setInputDec(e.target.value)}
              placeholder="e.g. -7.2451"
              className="w-24 bg-[#050b1a] border border-cyan-900/80 rounded px-2 py-0.5 text-cyan-300 focus:outline-none focus:border-cyan-400"
            />
          </div>

          <button
            type="submit"
            disabled={isDiscovering}
            className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-semibold rounded flex items-center space-x-1.5 shadow-[0_0_8px_rgba(6,182,212,0.25)] transition-all"
          >
            {isDiscovering ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Search className="w-3.5 h-3.5" />
            )}
            <span>{isDiscovering ? "Searching..." : "Discover Observations"}</span>
          </button>
        </div>

        <button
          type="button"
          onClick={handleDownloadMetadata}
          disabled={frames.length === 0}
          className="px-2.5 py-1 bg-[#050b1a] hover:bg-cyan-950/60 disabled:opacity-40 border border-cyan-900/80 text-cyan-300 rounded flex items-center space-x-1.5 transition-colors"
          title="Export JSON observation series"
        >
          <Download className="w-3 h-3" />
          <span>Download Observation Metadata</span>
        </button>
      </form>

      {/* 4. Archive Query and Temporal Coverage Status Section */}
      {isDiscovering && (
        <div className="bg-cyan-950/30 border border-cyan-800 rounded-lg p-3 text-cyan-200 flex items-center space-x-2">
          <RefreshCw className="w-4 h-4 animate-spin text-cyan-400 shrink-0" />
          <span className="font-mono text-xs text-cyan-300">
            QUERYING SPHEREx ARCHIVES (DR1 & QR3)...
          </span>
        </div>
      )}

      {!isDiscovering && (
        <>
          {/* CASE A: ARCHIVE QUERY FAILED (UNVERIFIED) */}
          {(queryError || [
            "ARCHIVE_QUERY_FAILED",
            "ARCHIVE_QUERY_TIMEOUT",
            "ARCHIVE_QUERY_RATE_LIMITED",
            "ARCHIVE_SERVICE_UNAVAILABLE",
          ].includes(discoveryData?.discovery_state)) && (
            <div className="bg-rose-950/40 border border-rose-600/80 rounded-lg p-3 text-rose-200 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 font-mono font-bold text-xs text-rose-400">
                  <XCircle className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>ARCHIVE QUERY FAILED</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-rose-900/60 border border-rose-700/60 text-rose-300 font-normal">
                    {queryError?.statusText || discoveryData?.discovery_state || "ERROR"}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 font-normal">
                    COVERAGE: UNVERIFIED
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => executeDiscovery(parseFloat(inputRa), parseFloat(inputDec), activeTargetName || undefined, true)}
                  disabled={isDiscovering}
                  className="px-2.5 py-1 bg-rose-900/40 hover:bg-rose-900/80 border border-rose-600 text-rose-200 rounded font-mono text-[10px] flex items-center space-x-1.5 transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Retry Archive Query</span>
                </button>
              </div>

              <div className="text-[11px] text-rose-100 font-sans space-y-1">
                <p>
                  Remote SPHEREx archive query to Caltech/IPAC IRSA SIA/TAP failed or timed out.
                  {queryError?.message && (
                    <span className="block font-mono text-[10px] text-rose-300 mt-0.5">
                      Diagnostic: {queryError.message} {queryError.httpStatus ? `(HTTP ${queryError.httpStatus})` : ""}
                    </span>
                  )}
                </p>
                <p className="font-semibold text-rose-200 text-[10px] pt-1 border-t border-rose-900/60 flex items-center space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span>
                    A failed archive query does not establish that zero observations exist. Temporal coverage remains UNVERIFIED.
                  </span>
                </p>
                {lastQueryTime && (
                  <div className="font-mono text-[9px] text-rose-400/80">
                    Last Query Attempt: {lastQueryTime}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* CASE B: ARCHIVE QUERY SUCCESSFUL — NO MATCHING PRODUCTS (0 OBSERVATIONS) */}
          {!queryError &&
            discoveryData?.discovery_state === "ARCHIVE_QUERY_SUCCESS_NO_RESULTS" &&
            frames.length === 0 && (
              <div className="bg-sky-950/30 border border-sky-600/60 rounded-lg p-3 text-sky-200 space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 font-mono font-bold text-xs text-sky-400">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-sky-400" />
                    <span>ARCHIVE QUERY SUCCESSFUL — NO MATCHING PRODUCTS</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-sky-900/60 border border-sky-700/60 text-sky-300 font-normal">
                      INSUFFICIENT_TEMPORAL_COVERAGE (0)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => executeDiscovery(parseFloat(inputRa), parseFloat(inputDec), activeTargetName || undefined, true)}
                    disabled={isDiscovering}
                    className="px-2 py-0.5 bg-sky-900/40 hover:bg-sky-900/80 border border-sky-700 text-sky-200 rounded font-mono text-[10px] flex items-center space-x-1"
                  >
                    <RefreshCw className="w-2.5 h-2.5" />
                    <span>Refresh</span>
                  </button>
                </div>
                <p className="text-[11px] text-sky-100 font-sans leading-relaxed">
                  The SPHEREx archive was successfully queried (HTTP 200). Exactly 0 overlapping Level-2 observations were found in public archives (DR1/QR3) for this sky position.
                </p>
              </div>
            )}

          {/* CASE C: INSUFFICIENT TEMPORAL COVERAGE (1 OBSERVATION) */}
          {!queryError &&
            frames.length === 1 && (
              <div className="bg-amber-950/30 border border-amber-600/70 rounded-lg p-3 text-amber-200 space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 font-mono font-bold text-xs text-amber-400">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>INSUFFICIENT TEMPORAL COVERAGE</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-900/60 border border-amber-700/60 text-amber-300 font-normal">
                      1 OBSERVATION
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-amber-100 font-sans leading-relaxed">
                  Exactly 1 usable SPHEREx Level-2 observation exists at this sky location. Minimum 2 distinct epochs are required to construct a time-series video or perform difference imaging.
                </p>
              </div>
            )}

          {/* CASE D: SUFFICIENT TEMPORAL COVERAGE (>= 2 OBSERVATIONS) */}
          {!queryError &&
            frames.length >= 2 && (
              <div className="bg-emerald-950/20 border border-emerald-600/60 rounded-lg p-2.5 text-emerald-200 flex items-center justify-between">
                <div className="flex items-center space-x-2 font-mono text-xs text-emerald-400">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold">SUFFICIENT TEMPORAL COVERAGE</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-900/60 border border-emerald-700/60 text-emerald-300 font-normal">
                    {frames.length} OBSERVATIONS VERIFIED
                  </span>
                </div>
                <span className="text-[10px] font-mono text-emerald-400/80">
                  Chronological Series Ready
                </span>
              </div>
            )}
        </>
      )}

      {/* 5. Time-Series Video Player Section */}
      {frames.length > 0 && (
        <div className="bg-[#09152e]/80 border border-cyan-950 rounded-lg p-3 space-y-3">
          {/* Main Visual Frame & Telemetry Deck */}
          <div className="flex flex-col md:flex-row gap-4 items-start">
            {/* Animated Sky Patch Viewer */}
            <div className="space-y-2 shrink-0">
              <div className="relative w-48 h-48 rounded-lg overflow-hidden border-2 border-cyan-600/70 bg-black shadow-2xl flex items-center justify-center">
                {previewCutoutUrl ? (
                  <img
                    src={previewCutoutUrl}
                    alt="SPHEREx Sky Patch View"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-slate-600 font-mono text-[10px] text-center p-2">
                    Level-2 MEF Frame
                  </div>
                )}

                {/* HUD Overlay */}
                <div className="absolute top-1.5 left-1.5 bg-black/85 border border-cyan-900 px-2 py-0.5 rounded text-[9px] font-mono text-cyan-300">
                  Frame {currentFrameIndex + 1} / {frames.length}
                </div>

                {isBlinkActive && (
                  <div className="absolute top-1.5 right-1.5 bg-indigo-950/90 border border-indigo-700 px-1.5 py-0.5 rounded text-[8px] font-mono text-indigo-300">
                    Blink: {blinkState === "ref" ? "Ref (Epoch 1)" : `Frame ${currentFrameIndex + 1}`}
                  </div>
                )}

                {isPlaying && (
                  <div className="absolute bottom-1.5 right-1.5 bg-emerald-950/80 border border-emerald-700 px-1.5 py-0.5 rounded text-[8px] font-mono text-emerald-300 flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    <span>PLAYING ({playbackSpeed}x)</span>
                  </div>
                )}
              </div>

              {/* Blink Comparator Button */}
              {frames.length >= 2 && (
                <button
                  type="button"
                  onClick={() => setIsBlinkActive((v) => !v)}
                  className={`w-48 py-1 rounded text-[10px] font-mono font-semibold transition-all border ${
                    isBlinkActive
                      ? "bg-indigo-600 border-indigo-400 text-white shadow-[0_0_8px_rgba(99,102,241,0.4)]"
                      : "bg-[#050b1a] border-cyan-900/60 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {isBlinkActive ? "Disable Blink Comparator" : "Enable Blink Comparator (500ms)"}
                </button>
              )}
            </div>

            {/* Active Frame Telemetry Card */}
            <div className="flex-1 w-full space-y-2 font-mono">
              <div className="flex items-center justify-between pb-1 border-b border-cyan-950 text-[11px]">
                <span className="font-bold text-cyan-300 flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Observation Frame Telemetry</span>
                </span>
                <div className="flex items-center space-x-1.5">
                  {activeFrame?.provenance?.state === "REAL_VERIFIED" || (!activeFrame?.is_simulated && activeFrame?.archive_release?.includes("Level-2")) ? (
                    <span className="text-[9px] px-2 py-0.5 rounded bg-emerald-950/90 text-emerald-300 border border-emerald-700/80 font-mono font-semibold flex items-center space-x-1 shadow-[0_0_6px_rgba(16,185,129,0.3)]">
                      <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                      <span>REAL_VERIFIED (SPHEREx L2)</span>
                    </span>
                  ) : (
                    <span className="text-[9px] px-2 py-0.5 rounded bg-amber-950/90 text-amber-300 border border-amber-700/80 font-mono font-semibold flex items-center space-x-1 shadow-[0_0_6px_rgba(245,158,11,0.25)]">
                      <AlertCircle className="w-2.5 h-2.5 text-amber-400" />
                      <span>SYNTHETIC_DEMO</span>
                    </span>
                  )}
                  <span className="text-[10px] px-2 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                    {activeFrame?.data_quality || "QUALITY_NOMINAL"}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="bg-[#050b1a] border border-cyan-950 p-2 rounded">
                  <div className="text-slate-400">Observation Identifier:</div>
                  <div className="text-cyan-200 font-bold truncate mt-0.5">
                    {activeFrame?.obs_id || "OBS-UNKNOWN"}
                  </div>
                </div>

                <div className="bg-[#050b1a] border border-cyan-950 p-2 rounded">
                  <div className="text-slate-400">Observation Timestamp:</div>
                  <div className="text-amber-300 font-semibold mt-0.5">
                    {activeFrame?.timestamp_utc ? activeFrame.timestamp_utc.slice(0, 19).replace("T", " ") : "MJD " + (activeFrame?.mjd_obs?.toFixed(2) || "N/A")}
                  </div>
                  <div className="text-slate-500 text-[9px]">
                    MJD: {activeFrame?.mjd_obs ? activeFrame.mjd_obs.toFixed(4) : "N/A"}
                  </div>
                </div>

                <div className="bg-[#050b1a] border border-cyan-950 p-2 rounded">
                  <div className="text-slate-400">Detector & Archive Release:</div>
                  <div className="text-cyan-200 font-bold mt-0.5">
                    Array {activeFrame?.detector_array || activeFrame?.band || "D1"} | {activeFrame?.archive_release || "Level-2 MEF"}
                  </div>
                </div>

                <div className="bg-[#050b1a] border border-cyan-950 p-2 rounded">
                  <div className="text-slate-400">Effective LVF Wavelength:</div>
                  <div className="text-emerald-400 font-bold mt-0.5">
                    {activeFrame?.effective_wavelength_um
                      ? `${activeFrame.effective_wavelength_um.toFixed(3)} µm`
                      : "0.75 – 5.00 µm"}
                  </div>
                  <div className="text-slate-500 text-[9px]">
                    LVF Filter Linear Dispersion
                  </div>
                </div>
              </div>

              {activeFrame?.file_name && (
                <div className="text-[9px] text-slate-500 truncate pt-0.5">
                  Source FITS: {activeFrame.file_name}
                </div>
              )}
            </div>
          </div>

          {/* Player Scrubber & Transport Controls */}
          <div className="bg-[#050b1a] border border-cyan-950 p-2.5 rounded-lg space-y-2 font-mono">
            {/* Timeline Scrubber */}
            <div className="flex items-center space-x-3 text-[10px]">
              <span className="text-slate-400 shrink-0">Frame:</span>
              <input
                type="range"
                min="0"
                max={Math.max(0, frames.length - 1)}
                value={currentFrameIndex}
                onChange={(e) => {
                  setCurrentFrameIndex(parseInt(e.target.value, 10));
                  setIsPlaying(false);
                }}
                className="w-full h-1.5 bg-cyan-950 rounded-lg appearance-none cursor-pointer accent-cyan-400"
              />
              <span className="text-cyan-300 font-bold shrink-0">
                {currentFrameIndex + 1} / {frames.length}
              </span>
            </div>

            {/* Transport Button Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-cyan-950/60">
              <div className="flex items-center space-x-1">
                {/* Step Back */}
                <button
                  type="button"
                  onClick={() => {
                    setCurrentFrameIndex((prev) => Math.max(0, prev - 1));
                    setIsPlaying(false);
                  }}
                  className="p-1.5 rounded bg-[#09152e] hover:bg-cyan-950 border border-cyan-900/60 text-cyan-300 transition-colors"
                  title="Previous Frame"
                >
                  <SkipBack className="w-3.5 h-3.5" />
                </button>

                {/* Play / Pause */}
                <button
                  type="button"
                  onClick={() => setIsPlaying((v) => !v)}
                  className="px-3 py-1.5 rounded bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold flex items-center space-x-1 shadow-[0_0_8px_rgba(6,182,212,0.3)] transition-all"
                  title={isPlaying ? "Pause Video" : "Play Time Series Video"}
                >
                  {isPlaying ? (
                    <>
                      <Pause className="w-3.5 h-3.5" />
                      <span>Pause</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" />
                      <span>Play Video</span>
                    </>
                  )}
                </button>

                {/* Step Forward */}
                <button
                  type="button"
                  onClick={() => {
                    setCurrentFrameIndex((prev) => Math.min(frames.length - 1, prev + 1));
                    setIsPlaying(false);
                  }}
                  className="p-1.5 rounded bg-[#09152e] hover:bg-cyan-950 border border-cyan-900/60 text-cyan-300 transition-colors"
                  title="Next Frame"
                >
                  <SkipForward className="w-3.5 h-3.5" />
                </button>

                {/* Loop Toggle */}
                <button
                  type="button"
                  onClick={() => setIsLooping((v) => !v)}
                  className={`p-1.5 rounded border transition-colors ${
                    isLooping
                      ? "bg-cyan-950 border-cyan-500 text-cyan-200"
                      : "bg-[#09152e] border-cyan-900/60 text-slate-500"
                  }`}
                  title={isLooping ? "Loop Enabled" : "Loop Disabled"}
                >
                  <Repeat className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Speed Multipliers */}
              <div className="flex items-center space-x-1 text-[10px]">
                <span className="text-slate-400 mr-1">Speed:</span>
                {[0.5, 1.0, 2.0, 4.0, 5.0].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setPlaybackSpeed(s)}
                    className={`px-2 py-0.5 rounded border ${
                      playbackSpeed === s
                        ? "bg-cyan-600 border-cyan-400 text-white font-bold"
                        : "bg-[#09152e] border-cyan-900/60 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {s}x
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
