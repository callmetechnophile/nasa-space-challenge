/**
 * Type definitions for Astronomical Image Rendering and WCS-Aware Projection (Milestone 3).
 */

export type DisplayStretchType = "asinh" | "log" | "linear" | "sqrt";

export type ProvenanceStateType =
  | "REAL_VERIFIED"
  | "REAL_UNVERIFIED"
  | "SYNTHETIC_DEMO"
  | "MOCK_TEST"
  | "ARCHIVE_ERROR"
  | "NO_DATA";

export interface WcsMetadata {
  wcs_valid: boolean;
  projection_type: string;
  ctype1: string;
  ctype2: string;
  crval1: number;
  crval2: number;
  crpix1: number;
  crpix2: number;
  cdelt1: number | null;
  cdelt2: number | null;
  cunit1: string;
  cunit2: string;
  pixel_scale_arcsec: number;
  pixel_scale_x_arcsec: number;
  pixel_scale_y_arcsec: number;
  rotation_deg: number;
  round_trip_residual_pixels: number;
  center_radec: [number, number];
  footprint_corners: Array<[number, number]>;
}

export interface FitsMetadata {
  filename: string;
  dimensions: [number, number];
  naxis: number;
  bitpix: number;
  bunit: string;
  telescope: string | null;
  instrument: string | null;
  target_object: string | null;
  date_obs: string | null;
  filter_band: string | null;
  exposure_time_sec: number | null;
  data_min: number;
  data_max: number;
  data_mean: number;
  data_std: number;
  wcs: WcsMetadata;
}

export interface SphericalMeshGeometry {
  radius: number;
  grid_density_x: number;
  grid_density_y: number;
  vertex_count: number;
  index_count: number;
  vertices: number[];
  uvs: number[];
  indices: number[];
  corners_radec: Array<[number, number]>;
  center_radec: [number, number];
  angular_diameter_deg: number;
}

export interface SampleImageInfo {
  id: string;
  title: string;
  provenance: string;
  provenance_state?: ProvenanceStateType;
  ra: number;
  dec: number;
  width: number;
  height: number;
  pixel_scale_arcsec: number;
  projection: string;
  description: string;
}

export interface AstronomicalImageLayerData {
  layer_id: string;
  title: string;
  provenance: string;
  provenance_state?: ProvenanceStateType;
  is_real_data?: boolean;
  observation_id?: string;
  detector?: string;
  metadata: FitsMetadata;
  mesh: SphericalMeshGeometry;
  texture_data_uri: string;
  stretch: DisplayStretchType;
  brightness: number;
  contrast: number;
}

export interface ActiveImageLayerState extends AstronomicalImageLayerData {
  visible: boolean;
  opacity: number;
  isLoading?: boolean;
}
