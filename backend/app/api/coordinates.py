"""FastAPI endpoints for Astronomical Coordinate Parsing and Transformations."""

from __future__ import annotations

import math
from fastapi import APIRouter, HTTPException, Query
from astropy.coordinates import SkyCoord
import astropy.units as u

from app.models.schemas import CoordinateRequest, CoordinateResponse
from app.astronomy.coordinates import (
    create_sky_coordinate,
    parse_sexagesimal_ra,
    parse_sexagesimal_dec,
    radec_to_threejs,
)

router = APIRouter(prefix="/coordinates", tags=["coordinates"])


def compute_celestial_coords(ra_deg: float, dec_deg: float) -> CoordinateResponse:
    """Use Astropy SkyCoord to calculate verified Galactic and Ecliptic coordinates."""
    coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")
    gal = coord.galactic
    ecl = coord.barycentricmeanecliptic

    sky = create_sky_coordinate(ra_deg, dec_deg)

    return CoordinateResponse(
        ra_deg=sky.ra_deg,
        dec_deg=sky.dec_deg,
        ra_hms=sky.ra_hms,
        dec_dms=sky.dec_dms,
        cartesian_unit=list(sky.cartesian_unit),
        threejs_vector=list(sky.threejs_vector),
        galactic_l_deg=round(float(gal.l.deg), 4),
        galactic_b_deg=round(float(gal.b.deg), 4),
        ecliptic_lon_deg=round(float(ecl.lon.deg), 4),
        ecliptic_lat_deg=round(float(ecl.lat.deg), 4),
    )


@router.post("/parse", response_model=CoordinateResponse)
def parse_coordinates(req: CoordinateRequest) -> CoordinateResponse:
    try:
        ra = parse_sexagesimal_ra(str(req.ra))
        dec = parse_sexagesimal_dec(str(req.dec))
        return compute_celestial_coords(ra, dec)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse celestial coordinates: {str(e)}")


@router.get("/convert", response_model=CoordinateResponse)
def convert_coordinates(
    ra: str = Query(..., description="Right Ascension in decimal deg or sexagesimal e.g. '08h 55m 10.83s'"),
    dec: str = Query(..., description="Declination in decimal deg or sexagesimal e.g. '-07° 14\' 42.5\"'"),
) -> CoordinateResponse:
    try:
        ra_val = parse_sexagesimal_ra(ra)
        dec_val = parse_sexagesimal_dec(dec)
        return compute_celestial_coords(ra_val, dec_val)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to convert coordinates: {str(e)}")
