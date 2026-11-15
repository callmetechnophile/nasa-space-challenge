import {
  CoordinateResponse,
  AstronomicalTargetDetail,
  ObservationEpoch,
  SpectralBand,
  SpectralMeasurement,
  DifferenceAnalysisResult,
} from "../types/astronomy";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export async function parseCoordinates(ra: string, dec: string): Promise<CoordinateResponse> {
  const resp = await fetch(`${API_BASE_URL}/coordinates/parse`, {
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
  const resp = await fetch(`${API_BASE_URL}/targets`);
  if (!resp.ok) throw new Error("Failed to fetch validation targets");
  return resp.json();
}

export async function fetchTargetById(id: string): Promise<AstronomicalTargetDetail> {
  const resp = await fetch(`${API_BASE_URL}/targets/${id}`);
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

  const resp = await fetch(`${API_BASE_URL}/observations?${query.toString()}`);
  if (!resp.ok) throw new Error("Failed to fetch observations");
  return resp.json();
}

export async function fetchSpectralBands(): Promise<SpectralBand[]> {
  const resp = await fetch(`${API_BASE_URL}/spectral/bands`);
  if (!resp.ok) throw new Error("Failed to fetch spectral bands");
  return resp.json();
}

export async function fetchSpectralProfile(params: {
  target?: string;
  ra?: number;
  dec?: number;
}): Promise<SpectralMeasurement[]> {
  const query = new URLSearchParams();
  if (params.target) query.set("target", params.target);
  if (params.ra !== undefined) query.set("ra", params.ra.toString());
  if (params.dec !== undefined) query.set("dec", params.dec.toString());

  const resp = await fetch(`${API_BASE_URL}/spectral/profile?${query.toString()}`);
  if (!resp.ok) throw new Error("Failed to fetch spectral profile");
  return resp.json();
}

export async function runDifferenceAnalysis(payload: {
  target?: string;
  ra?: number | string;
  dec?: number | string;
  epoch_ref: string;
  epoch_cmp: string;
  channel?: number;
  sigma_threshold?: number;
}): Promise<DifferenceAnalysisResult> {
  const resp = await fetch(`${API_BASE_URL}/images/difference`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target: payload.target,
      ra: payload.ra,
      dec: payload.dec,
      epoch_ref: payload.epoch_ref,
      epoch_cmp: payload.epoch_cmp,
      channel: payload.channel || 50,
      sigma_threshold: payload.sigma_threshold || 3.5,
    }),
  });
  if (!resp.ok) throw new Error("Difference analysis execution failed");
  return resp.json();
}

export function getCutoutUrl(params: {
  target?: string;
  ra?: number;
  dec?: number;
  epoch?: string;
  channel?: number;
  stretch?: string;
  colormap?: string;
  fov_arcmin?: number;
}): string {
  const query = new URLSearchParams();
  if (params.target) query.set("target", params.target);
  if (params.ra !== undefined) query.set("ra", params.ra.toString());
  if (params.dec !== undefined) query.set("dec", params.dec.toString());
  if (params.epoch) query.set("epoch", params.epoch);
  if (params.channel) query.set("channel", params.channel.toString());
  if (params.stretch) query.set("stretch", params.stretch);
  if (params.colormap) query.set("colormap", params.colormap);
  if (params.fov_arcmin) query.set("fov_arcmin", params.fov_arcmin.toString());

  return `${API_BASE_URL}/images/cutout?${query.toString()}`;
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

  return `${API_BASE_URL}/images/fits?${query.toString()}`;
}

export async function fetchTemporalObservations(): Promise<any> {
  const resp = await fetch(`${API_BASE_URL}/temporal/observations`);
  if (!resp.ok) throw new Error("Failed to fetch temporal observations");
  return resp.json();
}

export async function fetchBenchmarkPairs(): Promise<any> {
  const resp = await fetch(`${API_BASE_URL}/temporal/benchmark-pairs`);
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
  const resp = await fetch(`${API_BASE_URL}/temporal/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Comparison failed" }));
    throw new Error(err.detail || "Temporal comparison execution failed");
  }
  return resp.json();
}

export async function discoverTimeSeries(params: {
  ra: number;
  dec: number;
  fov_deg?: number;
  release?: string;
}): Promise<any> {
  const query = new URLSearchParams();
  query.set("ra", params.ra.toString());
  query.set("dec", params.dec.toString());
  if (params.fov_deg !== undefined) query.set("fov_deg", params.fov_deg.toString());
  if (params.release) query.set("release", params.release);

  const resp = await fetch(`${API_BASE_URL}/temporal/discovery?${query.toString()}`);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Discovery query failed" }));
    throw new Error(err.detail || "Time-series discovery failed");
  }
  return resp.json();
}

export async function fetchM6TargetValidation(slug?: string): Promise<any> {
  const url = slug
    ? `${API_BASE_URL}/targets/m6-validation/${slug}`
    : `${API_BASE_URL}/targets/m6-validation`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("Failed to fetch M6 validation data");
  return resp.json();
}

