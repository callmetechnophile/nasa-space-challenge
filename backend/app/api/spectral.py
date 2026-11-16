"""FastAPI endpoints for SPHEREx 102 Spectral Bands, Calibration Manifests, and Authentic Object Spectra.
Strict anti-fabrication invariant: Real/production paths never fabricate spectral flux, wavelength
measurements, uncertainties, molecular signatures, or spectral curves. Missing channels remain explicitly null.
"""

from __future__ import annotations

import os
import json
import yaml
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Response

from app.models.schemas import SpectralMeasurement
from app.models.provenance import ProvenanceState
from app.spectral.bands import SPHEREX_BANDS, SpectralBand, get_band_by_channel, get_bands_by_array
from app.spectral.real_spectral_extractor import extract_real_spectrum_at_coords
from app.providers import get_data_provider
from app.astronomy.coordinates import parse_sexagesimal_ra, parse_sexagesimal_dec

router = APIRouter(prefix="/spectral", tags=["spectral"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex"))


@router.get("/bands", response_model=List[SpectralBand], summary="List all 102 SPHEREx spectral channels")
def list_bands(array_index: Optional[int] = Query(None, ge=1, le=6)) -> List[SpectralBand]:
    """Retrieve full catalogue of 102 SPHEREx spectral channels or filter by detector array 1-6."""
    if array_index is not None:
        return get_bands_by_array(array_index)
    return SPHEREX_BANDS


@router.get("/bands/{channel_index}", response_model=SpectralBand, summary="Get metadata for a single spectral channel")
def get_band(channel_index: int) -> SpectralBand:
    """Retrieve metadata for a specific spectral channel (1 to 102)."""
    b = get_band_by_channel(channel_index)
    if not b:
        raise HTTPException(status_code=404, detail=f"Spectral channel {channel_index} not found (must be 1-102)")
    return b


@router.get("/manifest", summary="Retrieve complete SPHEREx 102 band manifest JSON")
def get_band_manifest() -> Dict[str, Any]:
    """Retrieve complete verified JSON manifest of all 102 SPHEREx channels with pre-flight LVF calibrations."""
    manifest_path = os.path.join(DATA_DIR, "band_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback dynamic generator
    return {
        "mission": "NASA SPHEREx",
        "total_channels": 102,
        "spectral_range_um": [0.75, 5.00],
        "bands": [b.dict() for b in SPHEREX_BANDS],
    }


@router.get("/arrays", summary="Retrieve detector arrays YAML specification")
def get_detector_arrays() -> Response:
    """Retrieve official YAML specification of SPHEREx 6 focal plane detector arrays."""
    arrays_path = os.path.join(DATA_DIR, "detector_arrays.yaml")
    if os.path.exists(arrays_path):
        with open(arrays_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/yaml")
    return Response(content="error: detector_arrays.yaml not found", status_code=404)


@router.get("/profile", response_model=List[SpectralMeasurement], summary="Retrieve 102-band spectral energy distribution")
@router.get("/measurements", response_model=List[SpectralMeasurement], summary="Alias for /profile")
def get_spectral_profile(
    response: Response,
    target: Optional[str] = Query(None, description="Target slug e.g. 'wise-0855' or 'barnards-star'"),
    ra: Optional[str] = Query(None, description="Right Ascension in decimal degrees or sexagesimal"),
    dec: Optional[str] = Query(None, description="Declination in decimal degrees or sexagesimal"),
    mode: str = Query("real", description="Extraction mode: 'real' (authentic Level-2 FITS WCS-WAVE) or 'synthetic' (nominal model)"),
    allow_demo: bool = Query(False, description="Explicit consent to return synthetic demonstration spectrum if no calibrated flight spectrum exists"),
) -> List[SpectralMeasurement]:
    """Retrieve 102-channel spectral energy distribution (SED).
    In 'real' mode, extracts calibrated wavelength and flux from authentic Level-2 FITS pointings.
    Unobserved channels are explicitly reported with flux=None and flux_is_available=False.
    """
    curated = get_data_provider("curated")

    # 1. Handle synthetic mode
    if mode == "synthetic" or allow_demo:
        if target:
            t = curated.get_target_by_id(target)
            if t:
                response.headers["X-Data-Provenance"] = "SYNTHETIC_DEMO"
                response.headers["X-Spectral-Coverage-State"] = "SYNTHETIC_DEMONSTRATION"
                return t.spectral_profile
        sim = get_data_provider("simulated")
        ra_val = parse_sexagesimal_ra(str(ra)) if ra else 133.7951
        dec_val = parse_sexagesimal_dec(str(dec)) if dec else -7.2451
        response.headers["X-Data-Provenance"] = "SYNTHETIC_DEMO"
        response.headers["X-Spectral-Coverage-State"] = "SYNTHETIC_DEMONSTRATION"
        return sim.get_spectral_profile(ra_val, dec_val)

    # 2. Determine target celestial coordinates
    if ra is not None and dec is not None:
        ra_val = parse_sexagesimal_ra(str(ra))
        dec_val = parse_sexagesimal_dec(str(dec))
    elif target:
        t = curated.get_target_by_id(target)
        if t:
            ra_val = t.ra_deg
            dec_val = t.dec_deg
        else:
            raise HTTPException(status_code=404, detail=f"Target '{target}' not found")
    else:
        # Default to primary research field (WISE 0855 coordinates)
        ra_val = 133.7951
        dec_val = -7.2451

    # 3. Extract authentic spectrum using WCS-WAVE, IMAGE, VARIANCE, and FLAGS
    profile, diag = extract_real_spectrum_at_coords(ra_val, dec_val)

    # Attach provenance headers
    response.headers["X-Data-Provenance"] = "REAL_VERIFIED" if diag["measured_channels_count"] > 0 else "NO_DATA"
    response.headers["X-Spectral-Coverage-State"] = diag["coverage_state"]
    response.headers["X-Measured-Channels"] = str(diag["measured_channels_count"])
    response.headers["X-Covering-Products"] = ",".join(diag["covering_products"]) if diag["covering_products"] else "NONE"

    return profile


@router.get("/diagnostics/{channel_index}", summary="Get detailed scientific diagnostics for a specific band")
def get_channel_diagnostics(
    channel_index: int,
    ra: Optional[float] = Query(None),
    dec: Optional[float] = Query(None),
) -> Dict[str, Any]:
    """Retrieve full instrument, calibration, and astrophysical diagnostics for a specific channel."""
    band = get_band_by_channel(channel_index)
    if not band:
        raise HTTPException(status_code=404, detail=f"Channel {channel_index} out of range (1-102)")

    # Check if this channel has a real measurement at coordinates
    real_measurement = None
    if ra is not None and dec is not None:
        profile, diag = extract_real_spectrum_at_coords(ra, dec)
        for m in diag.get("calibrated_measurements", []):
            if m.get("channel_index") == channel_index:
                real_measurement = m
                break

    # Array specification
    array_specs = {
        1: {"detector": "D1", "range": "0.75 - 1.11 um", "cutoff": "2.5 um (SWIR)", "nominal_r": 41.0},
        2: {"detector": "D2", "range": "1.11 - 1.64 um", "cutoff": "2.5 um (SWIR)", "nominal_r": 41.0},
        3: {"detector": "D3", "range": "1.64 - 2.42 um", "cutoff": "2.5 um (SWIR)", "nominal_r": 41.0},
        4: {"detector": "D4", "range": "2.42 - 3.82 um", "cutoff": "5.3 um (MWIR)", "nominal_r": 35.0},
        5: {"detector": "D5", "range": "3.82 - 4.42 um", "cutoff": "5.3 um (MWIR)", "nominal_r": 110.0},
        6: {"detector": "D6", "range": "4.42 - 5.00 um", "cutoff": "5.3 um (MWIR)", "nominal_r": 130.0},
    }
    arr_info = array_specs.get(band.array_index, array_specs[1])

    return {
        "channel_index": band.channel_index,
        "array_index": band.array_index,
        "detector_id": arr_info["detector"],
        "detector_cutoff": arr_info["cutoff"],
        "nominal_wavelength_um": band.wavelength_um,
        "nominal_bandwidth_um": band.bandwidth_um,
        "nominal_resolving_power_r": band.resolving_power_r,
        "key_features": band.key_features,
        "calibration_source": "NASA SPHEREx Pre-Flight LVF & In-Flight WCS-WAVE (HDU 6)",
        "is_measured": real_measurement is not None,
        "measured_data": real_measurement,
        "measurement_state": "MEASURED_AUTHENTIC_FLIGHT" if real_measurement else "UNOBSERVED_IN_POINTING",
        "astrophysical_lines_note": "Astrophysical molecular references indicate laboratory transition wavelengths; detection is asserted only when measured flux exceeds the significance threshold.",
    }
