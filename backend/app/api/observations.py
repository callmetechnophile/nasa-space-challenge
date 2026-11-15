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
    provider_mode: str = Query("auto", description="Provider mode: 'curated', 'simulated', or 'auto'"),
) -> List[ObservationEpoch]:
    """Retrieve chronologically ordered SPHEREx observation epochs."""
    curated_provider = get_data_provider("curated")

    if target:
        t = curated_provider.get_target_by_id(target)
        if t:
            return t.available_epochs

    if ra is not None and dec is not None:
        ra_val = parse_sexagesimal_ra(str(ra))
        dec_val = parse_sexagesimal_dec(str(dec))

        # Check curated matches
        matches = curated_provider.search_by_coordinates(ra_val, dec_val, radius_deg=0.5)
        if matches:
            return matches[0].available_epochs

        # Outside curated benchmarks, route to simulator
        sim_provider = get_data_provider("simulated")
        return sim_provider.get_observations_for_region(ra_val, dec_val, channel_index=channel)

    # Default to first target
    default_t = curated_provider.get_target_by_id("wise-0855")
    return default_t.available_epochs if default_t else []
