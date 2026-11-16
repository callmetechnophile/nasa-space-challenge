import {
  CoordinateResponse,
  AstronomicalTargetDetail,
  ObservationEpoch,
  SpectralBand,
  SpectralMeasurement,
  DifferenceAnalysisResult,
} from "../types/astronomy";
import { getApiBaseUrl } from "./apiConfig";

export interface M5ApiErrorDetails {
  status: number;
  stage: string;
  category: string;
  message: string;
  filename?: string;
}

export class M5ComparisonError extends Error {
  status: number;
  stage: string;
  category: string;
  filename?: string;

  constructor(details: M5ApiErrorDetails) {
    super(details.message);
    this.name = "M5ComparisonError";
    this.status = details.status;
    this.stage = details.stage;
    this.category = details.category;
    this.filename = details.filename;
  }
}

export async function parseCoordinates(ra: string, dec: string): Promise<CoordinateResponse> {
  const resp = await fetch(`${getApiBaseUrl()}/coordinates/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ra, dec }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Coordinate parse failed" }));
    throw new Error(err.detail || "Failed to parse coordinates");
  }
  return resp.json();
}

export async function fetchValidationTargets(): Promise<AstronomicalTargetDetail[]> {
  const resp = await fetch(`${getApiBaseUrl()}/targets`);
  if (!resp.ok) throw new Error("Failed to fetch validation targets");
  return resp.json();
}

export async function fetchTargetById(id: string): Promise<AstronomicalTargetDetail> {
  const resp = await fetch(`${getApiBaseUrl()}/targets/${id}`);
  if (!resp.ok) throw new Error(`Target ${id} not found`);
  return resp.json();
}

export async function fetchObservations(params: {
  ra?: number | string;
  dec?: number | string;
  target?: string;
  channel?: number;
}): Promise<ObservationEpoch[]> {
  const query = new URLSearchParams();
  if (params.target) query.set("target", params.target);
  if (params.ra !== undefined) query.set("ra", params.ra.toString());
  if (params.dec !== undefined) query.set("dec", params.dec.toString());
  if (params.channel) query.set("channel", params.channel.toString());

  const resp = await fetch(`${getApiBaseUrl()}/observations?${query.toString()}`);
  if (!resp.ok) throw new Error("Failed to fetch observations");
  return resp.json();
}

export async function fetchSpectralBands(): Promise<SpectralBand[]> {
  const resp = await fetch(`${getApiBaseUrl()}/spectral/bands`);
  if (!resp.ok) throw new Error("Failed to fetch spectral bands");
  return resp.json();
}

export async function fetchSpectralMeasurements(params: {
  ra?: number | string;
  dec?: number | string;
  target?: string;
  mode?: string;
}): Promise<SpectralMeasurement[]> {
  const query = new URLSearchParams();
  if (params.target) query.set("target", params.target);
  if (params.ra !== undefined) query.set("ra", params.ra.toString());
  if (params.dec !== undefined) query.set("dec", params.dec.toString());
  if (params.mode) query.set("mode", params.mode);

  const resp = await fetch(`${getApiBaseUrl()}/spectral/profile?${query.toString()}`);
  if (!resp.ok) throw new Error("Failed to fetch spectral measurements");
  return resp.json();
}

export const fetchSpectralProfile = fetchSpectralMeasurements;

export async function fetchChannelDiagnostics(
  channelIndex: number,
  ra?: number,
  dec?: number
): Promise<any> {
  const query = new URLSearchParams();
  if (ra !== undefined) query.set("ra", ra.toString());
  if (dec !== undefined) query.set("dec", dec.toString());
  const resp = await fetch(`${getApiBaseUrl()}/spectral/diagnostics/${channelIndex}?${query.toString()}`);
  if (!resp.ok) throw new Error(`Failed to fetch channel diagnostics for band ${channelIndex}`);
  return resp.json();
}

export async function fetchDifferenceAnalysis(params: {
  refEpoch?: string;
  targetEpoch?: string;
  epoch_ref?: string;
  epoch_cmp?: string;
  target?: string;
  channel?: number;
  ra?: number;
  dec?: number;
  sigma_threshold?: number;
}): Promise<DifferenceAnalysisResult> {
  const query = new URLSearchParams();
  const ref = params.refEpoch || params.epoch_ref || "";
  const target = params.targetEpoch || params.epoch_cmp || "";
  if (ref) query.set("ref", ref);
  if (target) query.set("target", target);
  if (params.target) query.set("target_id", params.target);
  if (params.channel) query.set("channel", params.channel.toString());
  if (params.ra !== undefined) query.set("ra", params.ra.toString());
  if (params.dec !== undefined) query.set("dec", params.dec.toString());
  if (params.sigma_threshold !== undefined) query.set("sigma_threshold", params.sigma_threshold.toString());

  const resp = await fetch(`${getApiBaseUrl()}/analysis/difference?${query.toString()}`);
  if (!resp.ok) throw new Error("Failed to run difference analysis");
  return resp.json();
}

export const runDifferenceAnalysis = fetchDifferenceAnalysis;

export function getCutoutUrl(params: {
  target?: string;
  ra?: number;
  dec?: number;
  epoch: string;
  channel: number;
  stretch?: string;
  colormap?: string;
  fov_arcmin?: number;
}): string {
  const query = new URLSearchParams();
  if (params.target) query.set("target", params.target);
  if (params.ra !== undefined) query.set("ra", params.ra.toString());
  if (params.dec !== undefined) query.set("dec", params.dec.toString());
  query.set("epoch", params.epoch);
  query.set("channel", params.channel.toString());
  if (params.stretch) query.set("stretch", params.stretch);
  if (params.colormap) query.set("colormap", params.colormap);
  if (params.fov_arcmin !== undefined) query.set("fov_arcmin", params.fov_arcmin.toString());

  return `${getApiBaseUrl()}/images/cutout?${query.toString()}`;
}

export function getFitsUrl(params: {
  target?: string;
  ra?: number;
  dec?: number;
  epoch?: string;
  channel?: number;
}): string {
  const query = new URLSearchParams();
  if (params.target) query.set("target", params.target);
  if (params.ra !== undefined) query.set("ra", params.ra.toString());
  if (params.dec !== undefined) query.set("dec", params.dec.toString());
  if (params.epoch) query.set("epoch", params.epoch);
  if (params.channel) query.set("channel", params.channel.toString());

  return `${getApiBaseUrl()}/images/fits?${query.toString()}`;
}

export async function fetchTemporalObservations(): Promise<any> {
  const resp = await fetch(`${getApiBaseUrl()}/temporal/observations`);
  if (!resp.ok) throw new Error("Failed to fetch temporal observations");
  return resp.json();
}

export async function fetchBenchmarkPairs(): Promise<any> {
  const resp = await fetch(`${getApiBaseUrl()}/temporal/benchmark-pairs`);
  if (!resp.ok) throw new Error("Failed to fetch benchmark pairs");
  return resp.json();
}

export async function runM5TemporalCompare(payload: {
  file1: string;
  file2: string;
  significance_threshold?: number;
  spectral_tolerance?: number;
  grid_size?: number;
  subtract_background?: boolean;
}): Promise<any> {
  const resp = await fetch(`${getApiBaseUrl()}/temporal/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    let errBody: any = null;
    try {
      errBody = await resp.json();
    } catch {
      errBody = null;
    }

    const detail = errBody?.detail;
    let message = "Temporal comparison execution failed";
    let stage = "PIPELINE_EXECUTION";
    let category = "PROCESSING_ERROR";
    let filename: string | undefined = undefined;

    if (typeof detail === "object" && detail !== null) {
      message = detail.message || detail.detail || message;
      stage = detail.stage || stage;
      category = detail.category || category;
      filename = detail.filename;
    } else if (typeof detail === "string") {
      message = detail;
      if (resp.status === 404) {
        stage = "FILE_INGESTION";
        category = "MISSING_INPUT_FILE";
      } else if (resp.status === 422) {
        stage = "SCIENTIFIC_VALIDATION";
        category = "SCIENTIFIC_INCOMPATIBILITY";
      }
    } else if (resp.status === 404) {
      message = "Required observation files not found on server or archive.";
      stage = "FILE_INGESTION";
      category = "MISSING_INPUT_FILE";
    } else if (resp.status === 502 || resp.status === 503) {
      message = "Difference imaging backend service currently unavailable.";
      stage = "SERVICE_GATEWAY";
      category = "BACKEND_UNAVAILABLE";
    }

    throw new M5ComparisonError({
      status: resp.status,
      stage,
      category,
      message,
      filename,
    });
  }

  return resp.json();
}

export async function discoverTimeSeries(params: {
  ra: number;
  dec: number;
  fov_deg?: number;
  release?: string;
  use_cache?: boolean;
  force_refresh?: boolean;
  signal?: AbortSignal;
}): Promise<any> {
  const query = new URLSearchParams();
  query.set("ra", params.ra.toString());
  query.set("dec", params.dec.toString());
  if (params.fov_deg !== undefined) query.set("fov_deg", params.fov_deg.toString());
  if (params.release) query.set("release", params.release);
  if (params.use_cache !== undefined) query.set("use_cache", params.use_cache.toString());
  if (params.force_refresh !== undefined) query.set("force_refresh", params.force_refresh.toString());

  const resp = await fetch(`${getApiBaseUrl()}/temporal/discovery?${query.toString()}`, {
    signal: params.signal,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: `Discovery query failed (HTTP ${resp.status})` }));
    throw new Error(err.detail || `Time-series discovery failed (HTTP ${resp.status})`);
  }
  return resp.json();
}

export async function fetchM6TargetValidation(slug?: string): Promise<any> {
  const url = slug
    ? `${getApiBaseUrl()}/targets/m6-validation/${slug}`
    : `${getApiBaseUrl()}/targets/m6-validation`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("Failed to fetch M6 validation data");
  return resp.json();
}
