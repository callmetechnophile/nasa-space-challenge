"""FastAPI endpoints for SPHEREx 102 Spectral Bands and Object Spectra."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.models.schemas import SpectralMeasurement
from app.spectral.bands import SPHEREX_BANDS, SpectralBand, get_band_by_channel, get_bands_by_array
from app.providers import get_data_provider
from app.astronomy.coordinates import parse_sexagesimal_ra, parse_sexagesimal_dec

router = APIRouter(prefix="/spectral", tags=["spectral"])


@router.get("/bands", response_model=List[SpectralBand])
def list_bands(array_index: Optional[int] = Query(None, ge=1, le=6)) -> List[SpectralBand]:
    """Retrieve full catalog of 102 SPHEREx spectral channels or filter by detector array 1-6."""
    if array_index is not None:
        return get_bands_by_array(array_index)
    return SPHEREX_BANDS


@router.get("/bands/{channel_index}", response_model=SpectralBand)
def get_band(channel_index: int) -> SpectralBand:
    """Retrieve metadata for a specific spectral channel."""
    b = get_band_by_channel(channel_index)
    if not b:
        raise HTTPException(status_code=404, detail=f"Spectral channel {channel_index} not found (must be 1-102)")
    return b


@router.get("/profile", response_model=List[SpectralMeasurement])
def get_spectral_profile(
    target: Optional[str] = Query(None, description="Target slug e.g. 'barnards-star'"),
    ra: Optional[str] = Query(None),
    dec: Optional[str] = Query(None),
) -> List[SpectralMeasurement]:
    """Retrieve 102-band flux measurements for a target or coordinate position."""
    curated = get_data_provider("curated")

    if target:
        t = curated.get_target_by_id(target)
        if t:
            return t.spectral_profile
        raise HTTPException(status_code=404, detail=f"Target '{target}' not found")

    if ra is not None and dec is not None:
        ra_val = parse_sexagesimal_ra(str(ra))
        dec_val = parse_sexagesimal_dec(str(dec))
        matches = curated.search_by_coordinates(ra_val, dec_val, radius_deg=0.5)
        if matches:
            return matches[0].spectral_profile

        sim = get_data_provider("simulated")
        return sim.get_spectral_profile(ra_val, dec_val)

    # Default to wise-0855
    t = curated.get_target_by_id("wise-0855")
    return t.spectral_profile if t else []
