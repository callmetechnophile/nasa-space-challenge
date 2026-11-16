import sys

with open("frontend/components/temporal/TimeSeriesPlayer.tsx", "r", encoding="utf-8") as f:
    content = f.read().replace("\r\n", "\n")

# 1. Update imports
old_imports = """import {
  Play,
  Pause,
  RotateCcw,
  SkipBack,
  SkipForward,
  FastForward,
  Layers,
  Sparkles,
  Calendar,
  Clock,
  Radio,
  Download,
  Crosshair,
  Search,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";"""

new_imports = """import {
  Play,
  Pause,
  RotateCcw,
  SkipBack,
  SkipForward,
  FastForward,
  Layers,
  Sparkles,
  Calendar,
  Clock,
  Radio,
  Download,
  Crosshair,
  Search,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  XCircle,
  AlertTriangle,
} from "lucide-react";"""

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    print("Updated lucide-react imports")

# 2. Update Discovery state & logic
old_state_block = """  // Discovery state
  const [inputRa, setInputRa] = useState<string>(raDeg.toFixed(4));
  const [inputDec, setInputDec] = useState<string>(decDeg.toFixed(4));
  const [activeTargetName, setActiveTargetName] = useState<string | null>("WISE 0855");
  const [isDiscovering, setIsDiscovering] = useState<boolean>(false);
  const [discoveryData, setDiscoveryData] = useState<any | null>(null);
  const [frames, setFrames] = useState<any[]>([]);
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);

  // Playback state
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0); // 0.5, 1, 2, 4, 5
  const [isLooping, setIsLooping] = useState<boolean>(true);
  const [archiveStatusNote, setArchiveStatusNote] = useState<string | null>(null);

  // Blink comparator mode
  const [isBlinkActive, setIsBlinkActive] = useState<boolean>(false);
  const [blinkState, setBlinkState] = useState<"ref" | "cur">("cur");

  // Sync input fields when store coordinates change externally
  useEffect(() => {
    setInputRa(raDeg.toFixed(4));
    setInputDec(decDeg.toFixed(4));
  }, [raDeg, decDeg]);

  // Load initial discovery for default coordinates on mount
  useEffect(() => {
    executeDiscovery(raDeg, decDeg, "WISE 0855");
  }, []);

  const executeDiscovery = async (ra: number, dec: number, targetName?: string) => {
    setIsDiscovering(true);
    setIsPlaying(false);
    setArchiveStatusNote(null);
    try {
      const data = await discoverTimeSeries({ ra, dec, fov_deg: 0.5, release: "all" });
      setDiscoveryData(data);
      const obs = data.observations || [];
      setFrames(obs);
      setCurrentFrameIndex(0);
      if (targetName) {
        setActiveTargetName(targetName);
      } else {
        setActiveTargetName(null);
      }

      if (obs.length === 0) {
        const dr1Err = data.archive_queries?.spherex_dr1?.error;
        const qr3Err = data.archive_queries?.spherex_qr3?.error;
        if (dr1Err || qr3Err) {
          setArchiveStatusNote(`Archive service returned: ${dr1Err || qr3Err}`);
        }
      }
    } catch (err: any) {
      console.warn("Discovery failed:", err);
      setDiscoveryData(null);
      setFrames([]);
      setArchiveStatusNote(err.message || "Archive discovery request failed");
    } finally {
      setIsDiscovering(false);
    }
  };"""

new_state_block = """  // Discovery state with 6-decimal precision
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

  // Load initial discovery for default coordinates on mount
  useEffect(() => {
    executeDiscovery(raDeg, decDeg, "WISE 0855");
  }, []);

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
  };"""

if old_state_block in content:
    content = content.replace(old_state_block, new_state_block)
    print("Updated state and executeDiscovery logic")

# 3. Update Preset & Custom search calls
old_preset = """  const handleSelectPreset = (target: TargetPreset) => {
    setInputRa(target.raDeg.toFixed(6));
    setInputDec(target.decDeg.toFixed(6));
    setActiveTargetName(target.name);
    setCoordinates(target.raDeg, target.decDeg, 0.5);
    executeDiscovery(target.raDeg, target.decDeg, target.name);
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
    executeDiscovery(r, d);
  };"""

new_preset = """  const handleSelectPreset = (target: TargetPreset) => {
    setInputRa(target.raDeg.toFixed(6));
    setInputDec(target.decDeg.toFixed(6));
    setActiveTargetName(target.name);
    setCoordinates(target.raDeg, target.decDeg, 0.5);
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
  };"""

if old_preset in content:
    content = content.replace(old_preset, new_preset)
    print("Updated handleSelectPreset and handleCustomSearch")

# 4. Replace section 4 Insufficient Coverage Handling with 4 distinct states
old_coverage_panel = """      {/* 4. Insufficient Coverage Handling */}
      {frames.length < 2 && !isDiscovering && (
        <div className="bg-amber-950/30 border border-amber-600/70 rounded-lg p-3 text-amber-200 space-y-1">
          <div className="flex items-center space-x-2 font-mono font-bold text-xs text-amber-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>INSUFFICIENT SPHEREx TEMPORAL COVERAGE</span>
          </div>
          <p className="text-[11px] text-amber-100 font-sans leading-relaxed">
            {frames.length === 1
              ? "Only 1 usable SPHEREx Level-2 observation exists at this sky location. Minimum 2 distinct epochs are required to construct a time-series video or perform difference imaging."
              : "0 overlapping Level-2 observations found in public SPHEREx archives (DR1/QR3) for this sky position."}
            {archiveStatusNote && (
              <span className="block mt-1 font-mono text-[10px] text-amber-300/80">
                Note: {archiveStatusNote}
              </span>
            )}
          </p>
        </div>
      )}"""

new_coverage_panel = """      {/* 4. Archive Query and Temporal Coverage Status Section */}
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
      )}"""

if old_coverage_panel in content:
    content = content.replace(old_coverage_panel, new_coverage_panel)
    print("Updated coverage panel with 4 distinct states")

with open("frontend/components/temporal/TimeSeriesPlayer.tsx", "w", encoding="utf-8") as f:
    f.write(content)

print("TimeSeriesPlayer.tsx patched successfully!")
