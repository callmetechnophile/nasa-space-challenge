"""FastAPI endpoints for Multi-Epoch Temporal Observations."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Query
from app.models.schemas import ObservationEpoch
from app.providers import get_data_provider
from app.astronomy.coordinates import parse_sexagesimal_ra, parse_sexagesimal_dec

router = APIRouter(prefix="/observations", tags=["observations"])


@router.get("", response_model=List[ObservationEpoch])
def get_observations(
    ra: Optional[str] = Query(None, description="RA in decimal degrees or sexagesimal"),
    dec: Optional[str] = Query(None, description="Dec in decimal degrees or sexagesimal"),
    target: Optional[str] = Query(None, description="Target slug e.g. 'wise-0855'"),
    channel: int = Query(50, ge=1, le=102, description="Spectral band channel index 1-102"),
    provider_mode: str = Query("auto", description="Provider mode: 'curated', 'simulated', 'nasa', 'production', or 'auto'"),
    allow_demo: bool = Query(False, description="Explicit consent to return synthetic demonstration data if no real data exists"),
) -> List[ObservationEpoch]:
    """Retrieve chronologically ordered SPHEREx observation epochs.
    Anti-fabrication invariant: Real/production paths never silently substitute synthetic data.
    """
    mode = provider_mode.lower()

    if mode == "simulated":
        sim_provider = get_data_provider("simulated")
        ra_val = parse_sexagesimal_ra(str(ra)) if ra else 133.7951
        dec_val = parse_sexagesimal_dec(str(dec)) if dec else -7.2451
        return sim_provider.get_observations_for_region(ra_val, dec_val, channel_index=channel)

    if mode in ("nasa", "production"):
        nasa_provider = get_data_provider("nasa")
        ra_val = parse_sexagesimal_ra(str(ra)) if ra else 133.7951
        dec_val = parse_sexagesimal_dec(str(dec)) if dec else -7.2451
        return nasa_provider.get_observations_for_region(ra_val, dec_val, channel_index=channel, allow_demo_fallback=allow_demo)

    # Curated / Auto mode
    curated_provider = get_data_provider("curated")

    if target:
        t = curated_provider.get_target_by_id(target)
        if t:
            return t.available_epochs
        return []

    if ra is not None and dec is not None:
        ra_val = parse_sexagesimal_ra(str(ra))
        dec_val = parse_sexagesimal_dec(str(dec))

        # Check curated matches
        matches = curated_provider.search_by_coordinates(ra_val, dec_val, radius_deg=0.5)
        if matches:
            return matches[0].available_epochs

        # Check real local archive
        nasa_provider = get_data_provider("nasa")
        real_obs = nasa_provider.get_observations_for_region(ra_val, dec_val, channel_index=channel, allow_demo_fallback=False)
        if real_obs:
            return real_obs

        # If user explicitly opted into demonstration mode:
        if allow_demo:
            sim_provider = get_data_provider("simulated")
            return sim_provider.get_observations_for_region(ra_val, dec_val, channel_index=channel)

        # Anti-fabrication: Return empty if no real observations exist
        return []

    # Default to wise-0855 if nothing specified
    default_t = curated_provider.get_target_by_id("wise-0855")
    return default_t.available_epochs if default_t else []
