export interface CoordinateResponse {
  ra_deg: number;
  dec_deg: number;
  ra_hms: string;
  dec_dms: string;
  cartesian_unit: [number, number, number];
  threejs_vector: [number, number, number];
  galactic_l_deg: number;
  galactic_b_deg: number;
  ecliptic_lon_deg: number;
  ecliptic_lat_deg: number;
}

export interface ObservationEpoch {
  epoch_id: string;
  timestamp_utc: string;
  mjd: number;
  survey_pass: string;
  channel_index: number;
  array_index: number;
  wavelength_um: number;
  integration_time_sec: number;
  mean_flux_mjy_sr: number;
  cutout_png_url: string;
  cutout_fits_url?: string;
  quality_flags: string[];
  is_simulated: boolean;
  data_provider: string;
}

export interface SpectralBand {
  channel_index: number;
  array_index: number;
  array_name: string;
  wavelength_um: number;
  bandwidth_um: number;
  resolving_power_r: number;
  key_features: string;
}

export interface SpectralMeasurement {
  channel_index: number;
  array_index: number;
  wavelength_um: number;
  bandwidth_um: number;
  flux_mjy: number | null;
  flux_err_mjy: number | null;
  flux_is_available: boolean;
  key_features: string;
}

export interface TransientCandidate {
  candidate_id: string;
  pixel_x: number;
  pixel_y: number;
  ra_deg: number;
  dec_deg: number;
  angular_dist_arcsec: number;
  flux_delta_mjy: number;
  snr: number;
  significance_sigma: number;
  flag: string;
  quality_assessment: string;
}

export interface DifferenceAnalysisResult {
  target_name?: string;
  ra_deg: number;
  dec_deg: number;
  channel_index: number;
  wavelength_um: number;
  epoch_ref_id: string;
  epoch_ref_date: string;
  epoch_cmp_id: string;
  epoch_cmp_date: string;
  delta_days: number;
  max_abs_diff_mjy: number;
  median_diff_mjy: number;
  std_diff_mjy: number;
  diff_image_base64: string;
  colormap: string;
  candidates_found: number;
  candidates: TransientCandidate[];
  algorithm_notes: string;
}

export interface CatalogCrossMatch {
  catalog_name: string;
  source_id: string;
  angular_separation_arcsec: number;
  ra_deg: number;
  dec_deg: number;
  photometry: Record<string, number | null>;
  spectral_type?: string;
  proper_motion_ra_mas_yr?: number;
  proper_motion_dec_mas_yr?: number;
  parallax_mas?: number;
  provenance_url: string;
}

export interface AstronomicalTargetDetail {
  id: string;
  name: string;
  designation: string;
  target_type: string;
  description: string;
  scientific_significance: string;
  ra_deg: number;
  dec_deg: number;
  ra_hms: string;
  dec_dms: string;
  proper_motion_ra_mas_yr?: number;
  proper_motion_dec_mas_yr?: number;
  parallax_mas?: number;
  distance_pc?: number;
  spectral_class: string;
  test_validation_role: string;
  observations_available: number;
  available_epochs: ObservationEpoch[];
  spectral_profile: SpectralMeasurement[];
  catalog_crossmatches: CatalogCrossMatch[];
}
