"""Data Models for SPHEREx Archive Integration (Milestone 4).
Pydantic schemas for IRSA SIA2 queries, observation metadata,
MEF HDU inspection, and layer rendering payloads.
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field
from app.astronomy.fits_reader import FitsMetadata
from app.astronomy.image_footprint import SphericalMeshGeometry


class SpherexSearchRequest(BaseModel):
    """Request payload for IRSA SIA2 coordinate queries."""
    ra: float = Field(..., ge=0.0, le=360.0, description="Right Ascension in decimal degrees")
    dec: float = Field(..., ge=-90.0, le=90.0, description="Declination in decimal degrees")
    radius_deg: float = Field(0.05, ge=0.0001, le=2.0, description="Search radius in degrees")
    collection: str = Field("spherex_qr3", description="Target collection: spherex_qr3, spherex_qr2, etc.")
    allow_fallback: bool = Field(True, description="Automatically fall back to QR2 if QR3 yields 0 matches")
    detector_filter: Optional[str] = Field(None, description="Optional detector filter: SPHEREx-D1 through D6")


class SpherexObservationRecord(BaseModel):
    """Normalized metadata for a single SPHEREx spectral-image observation."""
    obs_id: str = Field(..., description="Unique observation product identifier")
    collection: str = Field(..., description="Archive collection, e.g. spherex_qr3, spherex_qr2")
    facility_name: str = Field("SPHEREx", description="Observatory facility")
    instrument_name: str = Field("SPHEREx", description="Instrument identifier")
    detector_band: str = Field(..., description="Detector / bandpass name (e.g. SPHEREx-D1)")
    ra_deg: float = Field(..., description="Observation center Right Ascension in degrees")
    dec_deg: float = Field(..., description="Observation center Declination in degrees")
    dimensions: Tuple[int, int] = Field(..., description="Image array dimensions (width, height in pixels)")
    access_url: str = Field(..., description="Direct archive HTTP download URL for FITS product")
    access_format: str = Field("image/fits", description="MIME type")
    file_size_bytes: int = Field(..., description="Estimated product file size in bytes")
    file_size_mb: float = Field(..., description="Estimated product file size in megabytes")
    obs_date: Optional[str] = Field(None, description="Observation timestamp / release date")
    cloud_access: Optional[str] = Field(None, description="S3 or cloud URI if available")
    s_region: Optional[str] = Field(None, description="Spatial outline polygon string from SIA2")
    is_downloaded: bool = Field(False, description="Whether this product is currently cached locally")
    local_filename: Optional[str] = Field(None, description="Local cached filename if downloaded")


class SpherexSearchResponse(BaseModel):
    """Response payload for archive coordinate queries."""
    query_ra: float
    query_dec: float
    query_radius_deg: float
    collection_queried: str
    fallback_triggered: bool
    fallback_collection: Optional[str] = None
    match_count: int
    observations: List[SpherexObservationRecord]
    archive_status: str = Field("OK", description="OK, EMPTY, or ERROR")
    message: Optional[str] = None


class SpherexDownloadRequest(BaseModel):
    """Request to download a specific archive product."""
    access_url: str = Field(..., description="Official IRSA access URL")
    obs_id: Optional[str] = Field(None, description="Observation ID for tracking")
    detector_band: Optional[str] = Field(None, description="Detector band identifier")


class SpherexDownloadResponse(BaseModel):
    """Result of an observation product download."""
    success: bool
    obs_id: Optional[str]
    filename: str
    file_path: str
    file_size_bytes: int
    file_size_mb: float
    sha256: str
    download_time_sec: float
    already_existed: bool
    message: str


class SpherexMefHduSummary(BaseModel):
    """Summary of a single extension in a multi-extension FITS file."""
    index: int
    name: str
    hdu_type: str
    shape: Optional[List[int]] = None
    dtype: Optional[str] = None
    bunit: Optional[str] = None
    card_count: int


class SpherexMefInspection(BaseModel):
    """Comprehensive inspection report for a downloaded SPHEREx MEF product."""
    filename: str
    file_size_bytes: int
    sha256: str
    hdus: List[SpherexMefHduSummary]
    observation_id: str
    detector: str
    date_obs: Optional[str]
    exposure_time: Optional[float]
    image_units: str
    has_image: bool
    has_flags: bool
    has_variance: bool
    has_zodi: bool
    has_psf: bool
    has_wcs_wave: bool
    flags_summary: Optional[Dict[str, Any]] = None
    variance_summary: Optional[Dict[str, Any]] = None
    wcs_type: str
    has_sip: bool
    sip_order: Optional[int] = None
    nan_pixels: int
    finite_pixels: int
    wcs_corners: List[Tuple[float, float]]


class SpherexLayerLoadRequest(BaseModel):
    """Request to convert a downloaded real SPHEREx MEF into a 3D visualization layer."""
    filename: str = Field(..., description="Downloaded FITS filename in data/spherex/")
    stretch: str = Field("asinh", description="Display stretch: asinh, log, linear, sqrt")
    brightness: float = Field(1.0, ge=0.1, le=3.0)
    contrast: float = Field(1.0, ge=0.1, le=3.0)
    radius: float = Field(98.0, ge=50.0, le=150.0)


class SpherexLayerPayload(BaseModel):
    """Renderable payload for Three.js display of genuine SPHEREx data."""
    layer_id: str
    title: str
    provenance: str = Field("NASA/IPAC IRSA SPHEREx", description="Strict provenance distinction")
    is_real_data: bool = Field(True, description="Strictly True for real NASA data")
    observation_id: str
    detector: str
    obs_date: Optional[str]
    metadata: FitsMetadata
    mesh: SphericalMeshGeometry
    texture_data_uri: str
    units: str
    stretch: str
    brightness: float
    contrast: float
