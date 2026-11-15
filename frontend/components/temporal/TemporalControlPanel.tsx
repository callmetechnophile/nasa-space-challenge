"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import { useSkyStore } from "@/stores/useSkyStore";
import {
  getCutoutUrl,
  getFitsUrl,
  fetchTemporalObservations,
  fetchBenchmarkPairs,
  runM5TemporalCompare,
} from "@/services/api";
import { TimeSeriesPlayer } from "./TimeSeriesPlayer";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  ChevronDown,
  ChevronUp,
  Download,
  Sliders,
  Sparkles,
  Layers,
  SplitSquareVertical,
  Activity,
  AlertCircle,
  Eye,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Flame,
} from "lucide-react";

function TemporalControlPanelComponent() {
  const bottomPanelCollapsed = useSkyStore((s) => s.bottomPanelCollapsed);
  const setBottomPanelCollapsed = useSkyStore((s) => s.setBottomPanelCollapsed);

  const epochs = useSkyStore((s) => s.epochs);
  const epochIndex = useSkyStore((s) => s.epochIndex);
  const setSelectedEpochIndex = useSkyStore((s) => s.setSelectedEpochIndex);
  const selectedEpoch = useSkyStore((s) => s.selectedEpoch);
  const comparisonEpoch = useSkyStore((s) => s.comparisonEpoch);
  const comparisonMode = useSkyStore((s) => s.comparisonMode);
  const setComparisonMode = useSkyStore((s) => s.setComparisonMode);

  const isPlaying = useSkyStore((s) => s.isPlaying);
  const togglePlay = useSkyStore((s) => s.togglePlay);
  const nextEpoch = useSkyStore((s) => s.nextEpoch);
  const prevEpoch = useSkyStore((s) => s.prevEpoch);
  const playbackSpeed = useSkyStore((s) => s.playbackSpeed);
  const setPlaybackSpeed = useSkyStore((s) => s.setPlaybackSpeed);

  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const raDeg = useSkyStore((s) => s.raDeg);
  const decDeg = useSkyStore((s) => s.decDeg);
  const selectedChannel = useSkyStore((s) => s.selectedChannel);

  const imageStretch = useSkyStore((s) => s.imageStretch);
  const setImageStretch = useSkyStore((s) => s.setImageStretch);
  const imageColormap = useSkyStore((s) => s.imageColormap);
  const setImageColormap = useSkyStore((s) => s.setImageColormap);

  const diffResult = useSkyStore((s) => s.diffResult);
  const isDiffLoading = useSkyStore((s) => s.isDiffLoading);
  const triggerDifferenceAnalysis = useSkyStore((s) => s.triggerDifferenceAnalysis);

  // Blink comparison toggle state
  const [blinkState, setBlinkState] = useState<"ref" | "cmp">("ref");

  // Milestone 6 & 5 Mode State
  const [panelMode, setPanelMode] = useState<"explorer" | "diff" | "timeline">("explorer");
  const m5Mode = panelMode === "diff";
  const setM5Mode = (val: boolean) => setPanelMode(val ? "diff" : "explorer");
  const [m5Observations, setM5Observations] = useState<any[]>([]);
  const [m5BenchmarkPairs, setM5BenchmarkPairs] = useState<any[]>([]);
  const [selectedPairId, setSelectedPairId] = useState<string>("PAIR-EQUATORIAL-D1-8D-APPROVED");
  const [m5Result, setM5Result] = useState<any | null>(null);
  const [m5Loading, setM5Loading] = useState<boolean>(false);
  const [m5Error, setM5Error] = useState<string | null>(null);
  const [activeM5Layer, setActiveM5Layer] = useState<
    "diff" | "sig" | "epoch1" | "epoch2" | "blink"
  >("diff");
  const [snrThreshold, setSnrThreshold] = useState<number>(3.5);
  const [spectralTol, setSpectralTol] = useState<number>(0.02);

  // Load observations and benchmark pairs on mount
  useEffect(() => {
    async function initM5() {
      try {
        const obsData = await fetchTemporalObservations();
        setM5Observations(obsData.observations || []);
      } catch (err) {
        console.warn("Could not fetch temporal observations:", err);
      }
      try {
        const pairsData = await fetchBenchmarkPairs();
        setM5BenchmarkPairs(pairsData.pairs || []);
      } catch (err) {
        console.warn("Could not fetch benchmark pairs:", err);
      }
    }
    initM5();
  }, []);

  // Playback timer loop
  useEffect(() => {
    if (!isPlaying || epochs.length === 0) return;
    const intervalMs = Math.max(250, 1600 / playbackSpeed);
    const timer = setInterval(() => {
      nextEpoch();
    }, intervalMs);
    return () => clearInterval(timer);
  }, [isPlaying, epochs.length, playbackSpeed, nextEpoch]);

  // Blink comparator timer
  useEffect(() => {
    if (comparisonMode !== "blink" && activeM5Layer !== "blink") return;
    const timer = setInterval(() => {
      setBlinkState((prev) => (prev === "ref" ? "cmp" : "ref"));
    }, 500);
    return () => clearInterval(timer);
  }, [comparisonMode, activeM5Layer]);

  // Execute M5 scientific comparison
  const handleRunM5Pipeline = async () => {
    setM5Loading(true);
    setM5Error(null);
    try {
      let file1 = "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits";
      let file2 = "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits";

      const bench = m5BenchmarkPairs.find((p) => p.pair_id === selectedPairId);
      if (bench && bench.epoch_1?.file_name && bench.epoch_2?.file_name) {
        file1 = bench.epoch_1.file_name;
        file2 = bench.epoch_2.file_name;
      } else if (selectedPairId === "PAIR-EQUATORIAL-D1-8D-APPROVED") {
        file1 = "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits";
        file2 = "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits";
      } else if (selectedPairId === "SYNTH_FIXTURES") {
        file1 = "fixtures_m5/m5_synthetic_epoch1.fits";
        file2 = "fixtures_m5/m5_synthetic_epoch2.fits";
      } else if (selectedPairId === "REAL_SELF_DIFF") {
        file1 = "level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits";
        file2 = "level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits";
      } else if (m5Observations.length >= 2) {
        file1 = m5Observations[0].file_name;
        file2 = m5Observations[1].file_name;
      }

      const res = await runM5TemporalCompare({
        file1,
        file2,
        significance_threshold: snrThreshold,
        spectral_tolerance: spectralTol,
        grid_size: 512,
        subtract_background: true,
      });
      setM5Result(res);
    } catch (err: any) {
      setM5Error(err.message || "Failed to execute M5 difference imaging");
    } finally {
      setM5Loading(false);
    }
  };

  const activeEpochForCutout =
    comparisonMode === "blink"
      ? blinkState === "ref"
        ? selectedEpoch
        : comparisonEpoch || epochs[1] || epochs[0]
      : selectedEpoch;

  const currentCutoutUrl = getCutoutUrl({
    target: selectedTarget?.id,
    ra: selectedTarget ? undefined : raDeg,
    dec: selectedTarget ? undefined : decDeg,
    epoch: activeEpochForCutout?.epoch_id || "EPOCH-PASS1-20250615",
    channel: selectedChannel,
    stretch: imageStretch,
    colormap: imageColormap,
    fov_arcmin: 6.0,
  });

  const comparisonCutoutUrl = getCutoutUrl({
    target: selectedTarget?.id,
    ra: selectedTarget ? undefined : raDeg,
    dec: selectedTarget ? undefined : decDeg,
    epoch: comparisonEpoch?.epoch_id || epochs[1]?.epoch_id || "EPOCH-PASS2-20251214",
    channel: selectedChannel,
    stretch: imageStretch,
    colormap: imageColormap,
    fov_arcmin: 6.0,
  });

  const fitsDownloadUrl = getFitsUrl({
    target: selectedTarget?.id,
    ra: selectedTarget ? undefined : raDeg,
    dec: selectedTarget ? undefined : decDeg,
    epoch: selectedEpoch?.epoch_id || "EPOCH-PASS1-20250615",
    channel: selectedChannel,
  });

  const candidateMarkers = useMemo(() => {
    if (!m5Result?.candidates) return null;
    const gridSize = m5Result.registration?.grid_size || 512;
    return m5Result.candidates.map((c: any) => (
      <div
        key={c.candidate_id}
        style={{
          left: `${(c.pixel_x / gridSize) * 100}%`,
          bottom: `${(c.pixel_y / gridSize) * 100}%`,
        }}
        className={`absolute w-2.5 h-2.5 -translate-x-1/2 translate-y-1/2 rounded-full border-2 ${
          c.polarity === "POSITIVE"
            ? "border-rose-400 bg-rose-500/50 shadow-[0_0_4px_rgba(244,63,94,0.6)]"
            : "border-cyan-400 bg-cyan-500/50 shadow-[0_0_4px_rgba(6,182,212,0.6)]"
        } pointer-events-none ring-1 ring-white/40`}
      />
    ));
  }, [m5Result?.candidates, m5Result?.registration?.grid_size]);

  const candidateTable = useMemo(() => {
    if (!m5Result) return null;
    if (m5Result.candidates.length === 0) {
      return (
        <div className="p-4 text-center text-slate-500 italic text-xs">
          No statistically significant candidates detected above {snrThreshold}σ.
          (Baseline consistent with zero astrophysical variability).
        </div>
      );
    }
    return (
      <div className="max-h-36 overflow-y-auto space-y-1">
        {m5Result.candidates.map((cand: any) => (
          <div
            key={cand.candidate_id}
            className="bg-[#050b1a]/90 border border-slate-800 rounded p-1.5 flex items-center justify-between hover:border-cyan-500/60 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <span
                className={`px-1 py-0.2 rounded text-[9px] font-bold ${
                  cand.polarity === "POSITIVE"
                    ? "bg-rose-950 text-rose-300 border border-rose-700/60"
                    : "bg-cyan-950 text-cyan-300 border border-cyan-700/60"
                }`}
              >
                {cand.polarity === "POSITIVE" ? "▲ BRIGHTENING" : "▼ FADING"}
              </span>
              <span className="font-semibold text-slate-200">
                {cand.candidate_id}
              </span>
              <span className="text-slate-400 text-[10px]">
                ({cand.pixel_x}, {cand.pixel_y}) | RA: {cand.ra_deg?.toFixed(4)}°, Dec: {cand.dec_deg?.toFixed(4)}°
              </span>
            </div>

            <div className="flex items-center space-x-3 text-[10px]">
              <span className="text-amber-300 font-semibold">
                ΔFlux: {cand.peak_flux_mjy_sr > 0 ? "+" : ""}
                {cand.peak_flux_mjy_sr.toFixed(2)} MJy/sr
              </span>
              <span className="text-emerald-400 font-bold">
                SNR: {cand.significance_peak.toFixed(1)}σ
              </span>
              <span className="text-slate-400">
                {cand.area_pixels} px
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  }, [m5Result?.candidates, snrThreshold]);

  if (bottomPanelCollapsed) {
    return (
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20">
        <button
          onClick={() => setBottomPanelCollapsed(false)}
          className="flex items-center space-x-2 px-4 py-2 bg-[#050b1a]/90 backdrop-blur-md border border-cyan-950/80 rounded-xl text-cyan-400 hover:text-cyan-200 shadow-2xl transition-all font-mono text-xs"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
          <span>M5 Scientific Difference Imaging & Temporal Comparator</span>
          <ChevronUp className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="absolute bottom-4 left-4 md:left-[356px] right-4 md:right-[360px] z-20 bg-[#050b1a]/95 backdrop-blur-md border border-cyan-950/80 rounded-xl shadow-2xl p-3.5 text-slate-200 pointer-events-auto select-none font-sans max-h-[560px] overflow-y-auto">
      {/* Top Header & Mode Toggle Bar */}
      <div className="flex flex-wrap items-center justify-between pb-2.5 border-b border-cyan-950/80 gap-2">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 bg-[#09152e] p-0.5 rounded-lg border border-cyan-900/60">
            <button
              onClick={() => setPanelMode("explorer")}
              className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all flex items-center space-x-1.5 ${
                panelMode === "explorer"
                  ? "bg-cyan-500 text-slate-950 shadow-[0_0_10px_rgba(6,182,212,0.4)]"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Play className="w-3.5 h-3.5" />
              <span>Multi-Epoch Sky Explorer</span>
            </button>
            <button
              onClick={() => setPanelMode("diff")}
              className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all flex items-center space-x-1.5 ${
                panelMode === "diff"
                  ? "bg-cyan-500 text-slate-950 shadow-[0_0_10px_rgba(6,182,212,0.4)]"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>M5 Difference Imaging</span>
            </button>
            <button
              onClick={() => setPanelMode("timeline")}
              className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all flex items-center space-x-1.5 ${
                panelMode === "timeline"
                  ? "bg-cyan-500 text-slate-950 shadow-[0_0_10px_rgba(6,182,212,0.4)]"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Survey Timeline</span>
            </button>
          </div>
          <span className="text-[10px] text-cyan-400 font-mono bg-cyan-950/80 border border-cyan-800/60 px-2 py-0.5 rounded">
            NASA SPHEREx M6
          </span>
        </div>

        <button
          onClick={() => setBottomPanelCollapsed(true)}
          className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition-colors"
          title="Collapse Panel"
        >
          <ChevronDown className="w-4 h-4" />
        </button>
      </div>

      {/* VIEW MODES */}
      {panelMode === "explorer" ? (
        <TimeSeriesPlayer />
      ) : panelMode === "diff" ? (
        <div className="pt-3 space-y-3 font-mono text-xs">
          {/* Scientific Disclaimer Alert */}
          <div className="bg-amber-950/40 border border-amber-600/60 rounded-lg p-2 text-amber-200 flex items-center justify-between text-[11px]">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                <strong className="font-semibold text-amber-300">
                  SCIENTIFIC CONSERVATISM:
                </strong>{" "}
                Difference detections are labeled{" "}
                <em className="text-amber-100">
                  CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED
                </em>
                . Excludes WCS errors, bad pixels, and spectral LVF mismatch.
              </span>
            </div>
            <span className="text-[9px] bg-amber-900/60 border border-amber-500/50 px-1.5 py-0.5 rounded text-amber-200 uppercase font-semibold">
              M5 Acceptance Invariant
            </span>
          </div>

          {/* Configuration & Selection Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 bg-[#09152e]/70 p-2.5 rounded-lg border border-cyan-950">
            <div className="flex items-center space-x-2">
              <span className="text-slate-400 text-[11px]">Dataset:</span>
              <select
                value={selectedPairId}
                onChange={(e) => setSelectedPairId(e.target.value)}
                className="bg-[#050b1a] border border-cyan-800/80 rounded px-2.5 py-1 text-cyan-300 text-xs focus:outline-none focus:border-cyan-400"
              >
                <option value="PAIR-EQUATORIAL-D1-8D-APPROVED">
                  ★ Approved SPHEREx Real Observation Pair (D1, Δt=8.07d, Equatorial)
                </option>
                <option value="SYNTH_FIXTURES">
                  ★ Synthetic Verification Fixtures (Known Transients + Astrometry)
                </option>
                <option value="REAL_SELF_DIFF">
                  NASA Level-2 FITS Self-Consistency (level2_2025W44)
                </option>
                {m5BenchmarkPairs.map((p) => (
                  <option key={p.pair_id} value={p.pair_id}>
                    IRSA SIA2: {p.pair_id} ({p.detector}, Δt={p.baseline_days.toFixed(1)}d)
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-3 text-[11px]">
              <div className="flex items-center space-x-1">
                <span className="text-slate-400">SNR Threshold:</span>
                <input
                  type="number"
                  step="0.5"
                  min="2.0"
                  max="10.0"
                  value={snrThreshold}
                  onChange={(e) => setSnrThreshold(parseFloat(e.target.value) || 3.5)}
                  className="w-14 bg-[#050b1a] border border-cyan-900 rounded px-1.5 py-0.5 text-center text-cyan-300"
                />
                <span className="text-slate-500">σ</span>
              </div>

              <div className="flex items-center space-x-1">
                <span className="text-slate-400">LVF Tol:</span>
                <input
                  type="number"
                  step="0.005"
                  min="0.005"
                  max="0.05"
                  value={spectralTol}
                  onChange={(e) => setSpectralTol(parseFloat(e.target.value) || 0.02)}
                  className="w-14 bg-[#050b1a] border border-cyan-900 rounded px-1.5 py-0.5 text-center text-cyan-300"
                />
                <span className="text-slate-500">(2%)</span>
              </div>

              <button
                onClick={handleRunM5Pipeline}
                disabled={m5Loading}
                className="px-3 py-1 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold rounded flex items-center space-x-1.5 shadow-[0_0_8px_rgba(6,182,212,0.3)] transition-all"
              >
                {m5Loading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Activity className="w-3.5 h-3.5" />
                )}
                <span>{m5Loading ? "Processing..." : "Run Scientific Differencing"}</span>
              </button>
            </div>
          </div>

          {/* Error Message if any */}
          {m5Error && (
            <div className="p-2 bg-rose-950/60 border border-rose-700/80 rounded text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{m5Error}</span>
            </div>
          )}

          {/* Results Display */}
          {m5Result && (
            <div className="space-y-3 pt-1">
              {/* Scientific Verification Badges */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                <div className="bg-[#09152e] border border-cyan-900/50 rounded p-2">
                  <div className="text-slate-400">Temporal Baseline</div>
                  <div className="text-cyan-300 font-bold text-xs mt-0.5">
                    {m5Result.temporal_baseline.delta_days.toFixed(1)} days (
                    {m5Result.temporal_baseline.delta_hours.toFixed(0)} h)
                  </div>
                  <div className="text-slate-500 text-[9px] mt-0.5">
                    MJD {m5Result.epoch_1.mjd_obs.toFixed(2)} → {m5Result.epoch_2.mjd_obs.toFixed(2)}
                  </div>
                </div>

                <div className="bg-[#09152e] border border-cyan-900/50 rounded p-2">
                  <div className="text-slate-400">LVF Spectral Compatibility</div>
                  <div className="text-emerald-400 font-bold text-xs mt-0.5 flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                    <span>
                      {(m5Result.spectral_compatibility.compatibility_fraction * 100).toFixed(1)}% Valid
                    </span>
                  </div>
                  <div className="text-slate-500 text-[9px] mt-0.5">
                    |Δλ/λ| avg = {(m5Result.spectral_compatibility.mean_rel_diff * 100).toFixed(2)}% (≤ 2.0%)
                  </div>
                </div>

                <div className="bg-[#09152e] border border-cyan-900/50 rounded p-2">
                  <div className="text-slate-400">WCS Registration</div>
                  <div className="text-cyan-300 font-bold text-xs mt-0.5">
                    Δθ = {m5Result.registration.displacement.angular_separation_arcsec.toFixed(2)}&quot;
                  </div>
                  <div className="text-slate-500 text-[9px] mt-0.5">
                    Offset: {m5Result.registration.displacement.pixel_offset.toFixed(2)} px on 6.2&quot; grid
                  </div>
                </div>

                <div className="bg-[#09152e] border border-cyan-900/50 rounded p-2">
                  <div className="text-slate-400">Quality Masking & Variance</div>
                  <div className="text-cyan-300 font-bold text-xs mt-0.5">
                    {m5Result.difference_metrics.valid_pixel_count.toLocaleString()} px Valid
                  </div>
                  <div className="text-emerald-400 text-[9px] mt-0.5">
                    FLAGS masked, ZODI preserved
                  </div>
                </div>
              </div>

              {/* Interactive Layer Preview Deck */}
              <div className="bg-[#09152e]/80 border border-cyan-950 p-2.5 rounded-lg flex flex-col md:flex-row gap-4 items-start">
                {/* Visual Viewport with Interactive Layer Controls */}
                <div className="space-y-1.5 shrink-0">
                  <div className="relative w-44 h-44 rounded-lg overflow-hidden border-2 border-cyan-600/60 bg-black shadow-2xl">
                    {activeM5Layer === "diff" && (
                      <img
                        src={m5Result.previews.difference_image_b64}
                        alt="Difference image D(x,y)"
                        className="w-full h-full object-cover"
                      />
                    )}
                    {activeM5Layer === "sig" && (
                      <img
                        src={m5Result.previews.significance_map_b64}
                        alt="Significance map S(x,y)"
                        className="w-full h-full object-cover"
                      />
                    )}
                    {activeM5Layer === "epoch1" && (
                      <img
                        src={m5Result.previews.epoch_1_b64}
                        alt="Epoch 1 Reference"
                        className="w-full h-full object-cover"
                      />
                    )}
                    {activeM5Layer === "epoch2" && (
                      <img
                        src={m5Result.previews.epoch_2_b64}
                        alt="Epoch 2 Comparison"
                        className="w-full h-full object-cover"
                      />
                    )}
                    {activeM5Layer === "blink" && (
                      <img
                        src={
                          blinkState === "ref"
                            ? m5Result.previews.epoch_1_b64
                            : m5Result.previews.epoch_2_b64
                        }
                        alt="Blinking Epochs"
                        className="w-full h-full object-cover"
                      />
                    )}

                    {/* HUD Overlay Label */}
                    <div className="absolute top-1 left-1 bg-black/80 border border-slate-700/60 px-1.5 py-0.5 rounded text-[9px] font-bold text-cyan-300 uppercase">
                      {activeM5Layer === "diff" && "D = I2 - I1 (BWR)"}
                      {activeM5Layer === "sig" && `S = D / σ_D (|S| ≥ ${snrThreshold}σ)`}
                      {activeM5Layer === "epoch1" && "Epoch 1 (Ref)"}
                      {activeM5Layer === "epoch2" && "Epoch 2 (Cmp)"}
                      {activeM5Layer === "blink" && `Blink: ${blinkState === "ref" ? "Epoch 1" : "Epoch 2"}`}
                    </div>

                    {/* Candidate markers on preview (optimized: crisp static badges, no continuous CSS ping) */}
                    {candidateMarkers}
                  </div>

                  {/* Layer Selector Buttons */}
                  <div className="flex flex-wrap gap-1 max-w-[176px]">
                    {[
                      { id: "diff", label: "Diff D(x,y)" },
                      { id: "sig", label: "Significance S" },
                      { id: "blink", label: "Blink (1↔2)" },
                      { id: "epoch1", label: "Epoch 1" },
                      { id: "epoch2", label: "Epoch 2" },
                    ].map((btn) => (
                      <button
                        key={btn.id}
                        onClick={() => setActiveM5Layer(btn.id as any)}
                        className={`px-1.5 py-0.5 text-[9px] rounded font-mono ${
                          activeM5Layer === btn.id
                            ? "bg-cyan-600 text-white font-semibold"
                            : "bg-[#050b1a] text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {btn.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Candidate Extraction Table */}
                <div className="flex-1 w-full space-y-1.5 overflow-x-auto">
                  <div className="flex items-center justify-between text-[11px] pb-1 border-b border-cyan-950">
                    <span className="font-semibold text-cyan-300">
                      Detected Transient Candidates ({m5Result.candidate_count})
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Noise RMS: {m5Result.difference_metrics.rms_noise_mjy_sr.toFixed(3)} MJy/sr
                    </span>
                  </div>

                  {candidateTable}

                  <div className="text-[9px] text-slate-500 italic pt-1">
                    * Photometric calibration and PSF convolution verified prior to subtraction.
                    Zodiacal light baseline preserved without subtraction.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* ORIGINAL TIMELINE & SURVEY PASS VIEW */
        <div className="pt-3 pb-2">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1.5">
            <span>SPHEREx 6-Month Survey Timeline</span>
            {selectedEpoch && (
              <span className="text-cyan-300 font-semibold">
                Current: {selectedEpoch.survey_pass} — {selectedEpoch.timestamp_utc.slice(0, 10)}
              </span>
            )}
          </div>

          <div className="grid grid-cols-4 gap-2">
            {epochs.map((ep, idx) => {
              const isActive = epochIndex === idx;
              return (
                <button
                  key={ep.epoch_id}
                  onClick={() => setSelectedEpochIndex(idx)}
                  className={`p-2 rounded border text-left font-mono transition-all relative overflow-hidden ${
                    isActive
                      ? "bg-cyan-950/80 border-cyan-400 text-cyan-100 shadow-[0_0_12px_rgba(6,182,212,0.25)]"
                      : "bg-[#09152e]/50 border-cyan-950/70 text-slate-400 hover:border-cyan-800 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-cyan-300">
                      {ep.survey_pass}
                    </span>
                    {isActive && (
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                    )}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {ep.timestamp_utc.slice(0, 10)}
                  </div>
                  <div className="text-[10px] text-amber-300/90 font-semibold mt-0.5">
                    Flux: {ep.mean_flux_mjy_sr.toFixed(3)} MJy/sr
                  </div>
                </button>
              );
            })}
          </div>

          {/* Single Cutout Preview */}
          <div className="mt-3 pt-2.5 border-t border-cyan-950/60 flex items-center space-x-3 text-xs font-mono">
            <div className="relative w-24 h-24 rounded-lg overflow-hidden border border-cyan-800/60 bg-black shrink-0 shadow-lg">
              <img
                src={currentCutoutUrl}
                alt="Active astronomical cutout"
                className="w-full h-full object-cover"
              />
              <div className="absolute top-1 left-1 bg-black/70 px-1 py-0.5 rounded text-[9px] text-cyan-300">
                {selectedEpoch?.survey_pass || "Pass 1"}
              </div>
            </div>
            <div className="text-[11px] space-y-1 text-slate-300">
              <div className="text-cyan-300 font-semibold">
                Single Epoch Infrared Cutout View
              </div>
              <div className="text-slate-400">
                WCS-oriented tan projection centered at RA: {raDeg.toFixed(4)}°, Dec: {decDeg.toFixed(4)}°
              </div>
              <div className="text-slate-400">
                Channel: Band {selectedChannel} (Array {Math.ceil(selectedChannel / 17)}) | Field: 6.0 arcmin
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export const TemporalControlPanel = React.memo(TemporalControlPanelComponent);
