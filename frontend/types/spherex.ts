/**
 * TypeScript types for SPHEREx Real Data Integration (Milestone 4).
 * Mirrors Pydantic models from backend/app/models/spherex_observation.py.
 */

import { FitsMetadata, SphericalMeshGeometry, DisplayStretchType } from "./astronomicalImage";

export interface SpherexSearchRequest {
  ra: number;
  dec: number;
  radius_deg?: number;
  collection?: string;
  allow_fallback?: boolean;
  detector_filter?: string | null;
}

export interface SpherexObservationRecord {
  obs_id: string;
  collection: string;
  facility_name: string;
  instrument_name: string;
  detector_band: string;
  ra_deg: number;
  dec_deg: number;
  dimensions: [number, number];
  access_url: string;
  access_format: string;
  file_size_bytes: number;
  file_size_mb: number;
  obs_date: string | null;
  cloud_access: string | null;
  s_region: string | null;
  is_downloaded: boolean;
  local_filename: string | null;
}

export interface SpherexSearchResponse {
  query_ra: number;
  query_dec: number;
  query_radius_deg: number;
  collection_queried: string;
  fallback_triggered: boolean;
  fallback_collection: string | null;
  match_count: number;
  observations: SpherexObservationRecord[];
  archive_status: "OK" | "EMPTY" | "ERROR";
  message: string | null;
}

export interface SpherexDownloadRequest {
  access_url: string;
  obs_id?: string;
  detector_band?: string;
}

export interface SpherexDownloadResponse {
  success: boolean;
  obs_id: string | null;
  filename: string;
  file_path: string;
  file_size_bytes: number;
  file_size_mb: number;
  sha256: string;
  download_time_sec: number;
  already_existed: boolean;
  message: string;
}

export interface SpherexMefHduSummary {
  index: number;
  name: string;
  hdu_type: string;
  shape: number[] | null;
  dtype: string | null;
  bunit: string | null;
  card_count: number;
}

export interface SpherexMefInspection {
  filename: string;
  file_size_bytes: number;
  sha256: string;
  hdus: SpherexMefHduSummary[];
  observation_id: string;
  detector: string;
  date_obs: string | null;
  exposure_time: number | null;
  image_units: string;
  has_image: boolean;
  has_flags: boolean;
  has_variance: boolean;
  has_zodi: boolean;
  has_psf: boolean;
  has_wcs_wave: boolean;
  flags_summary: {
    flagged_pixel_count: number;
    clean_pixel_count: number;
    flagged_ratio: number;
  } | null;
  variance_summary: {
    min: number;
    max: number;
    median: number;
    bunit: string;
  } | null;
  wcs_type: string;
  has_sip: boolean;
  sip_order: number | null;
  nan_pixels: number;
  finite_pixels: number;
  wcs_corners: Array<[number, number]>;
}

export interface SpherexLayerLoadRequest {
  filename: string;
  stretch?: DisplayStretchType;
  brightness?: number;
  contrast?: number;
  radius?: number;
}

export interface SpherexLayerPayload {
  layer_id: string;
  title: string;
  provenance: string;
  is_real_data: boolean;
  observation_id: string;
  detector: string;
  obs_date: string | null;
  metadata: FitsMetadata;
  mesh: SphericalMeshGeometry;
  texture_data_uri: string;
  units: string;
  stretch: DisplayStretchType;
  brightness: number;
  contrast: number;
}

export interface SpherexCacheFile {
  filename: string;
  size_mb: number;
  modified: number;
}

export interface SpherexCacheStatus {
  status: string;
  storage_dir: string;
  stats: {
    file_count: number;
    total_bytes: number;
    total_mb: number;
    max_mb: number;
  };
  cached_products: SpherexCacheFile[];
}
