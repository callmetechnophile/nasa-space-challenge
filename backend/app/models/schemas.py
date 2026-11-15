"""Pydantic data schemas for SPHEREx 3D Temporal Sky Explorer.
Strictly separates verified scientific data, local sample data, and explicitly labeled simulation data.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CoordinateRequest(BaseModel):
    ra: str | float = Field(..., description="RA in decimal degrees or sexagesimal HMS string")
    dec: str | float = Field(..., description="Dec in decimal degrees or sexagesimal DMS string")
    fov_deg: Optional[float] = Field(0.5, ge=0.01, le=180.0, description="Field of view in degrees")


class CoordinateResponse(BaseModel):
    ra_deg: float
    dec_deg: float
    ra_hms: str
    dec_dms: str
    cartesian_unit: List[float]
    threejs_vector: List[float]
    galactic_l_deg: float
    galactic_b_deg: float
    ecliptic_lon_deg: float
    ecliptic_lat_deg: float


class ObservationEpoch(BaseModel):
    epoch_id: str = Field(..., description="Unique observation epoch identifier")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp of midpoint observation")
    mjd: float = Field(..., description="Modified Julian Date")
    survey_pass: str = Field(..., description="SPHEREx survey iteration (Pass 1 to 4)")
    channel_index: int = Field(..., ge=1, le=102, description="SPHEREx spectral channel 1-102")
    array_index: int = Field(..., ge=1, le=6, description="Detector array index 1-6")
    wavelength_um: float = Field(..., description="Band central wavelength in micrometers")
    integration_time_sec: float = Field(..., description="Effective integration time in seconds")
    mean_flux_mjy_sr: float = Field(..., description="Mean observed surface brightness (MJy/sr)")
    cutout_png_url: str = Field(..., description="Relative API URL for high-dynamic-range cutout tile")
    cutout_fits_url: Optional[str] = Field(None, description="FITS cutout file download URL")
    quality_flags: List[str] = Field(default_factory=list, description="Detector and pipeline data quality flags")
    is_simulated: bool = Field(False, description="Explicit flag indicating if data is synthetic/simulated")
    data_provider: str = Field(..., description="Data provenance (e.g. NASA_IRSA, SAMPLE_ARCHIVE, SIMULATOR)")


class SpectralMeasurement(BaseModel):
    channel_index: int
    array_index: int
    wavelength_um: float
    bandwidth_um: float
    flux_mjy: Optional[float] = None
    flux_err_mjy: Optional[float] = None
    flux_is_available: bool = True
    key_features: str


class TransientCandidate(BaseModel):
    candidate_id: str
    pixel_x: float
    pixel_y: float
    ra_deg: float
    dec_deg: float
    angular_dist_arcsec: float
    flux_delta_mjy: float
    snr: float
    significance_sigma: float
    flag: str = "CANDIDATE_UNVERIFIED"
    quality_assessment: str


class DifferenceAnalysisResult(BaseModel):
    target_name: Optional[str] = None
    ra_deg: float
    dec_deg: float
    channel_index: int
    wavelength_um: float
    epoch_ref_id: str
    epoch_ref_date: str
    epoch_cmp_id: str
    epoch_cmp_date: str
    delta_days: float
    max_abs_diff_mjy: float
    median_diff_mjy: float
    std_diff_mjy: float
    diff_image_base64: str
    colormap: str = "seismic"
    candidates_found: int
    candidates: List[TransientCandidate]
    algorithm_notes: str


class CatalogCrossMatch(BaseModel):
    catalog_name: str
    source_id: str
    angular_separation_arcsec: float
    ra_deg: float
    dec_deg: float
    photometry: Dict[str, Optional[float]]
    spectral_type: Optional[str] = None
    proper_motion_ra_mas_yr: Optional[float] = None
    proper_motion_dec_mas_yr: Optional[float] = None
    parallax_mas: Optional[float] = None
    provenance_url: str


class AstronomicalTargetDetail(BaseModel):
    id: str
    name: str
    designation: str
    target_type: str
    description: str
    scientific_significance: str
    ra_deg: float
    dec_deg: float
    ra_hms: str
    dec_dms: str
    proper_motion_ra_mas_yr: Optional[float] = None
    proper_motion_dec_mas_yr: Optional[float] = None
    parallax_mas: Optional[float] = None
    distance_pc: Optional[float] = None
    spectral_class: str
    test_validation_role: str
    observations_available: int
    available_epochs: List[ObservationEpoch]
    spectral_profile: List[SpectralMeasurement]
    catalog_crossmatches: List[CatalogCrossMatch]
