"""Astronomical coordinate transformation and parsing module for SPHEREx Explorer.
Supports decimal degrees, sexagesimal strings, angular separation, and 3D spherical projections.
"""

from __future__ import annotations

import math
import re
from typing import Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field


class SkyCoordinate(BaseModel):
    ra_deg: float = Field(..., ge=0.0, lt=360.0, description="Right Ascension in decimal degrees [0, 360)")
    dec_deg: float = Field(..., ge=-90.0, le=90.0, description="Declination in decimal degrees [-90, +90]")
    ra_hms: str = Field(..., description="RA in sexagesimal HMS format (e.g. 08h 55m 10.83s)")
    dec_dms: str = Field(..., description="Dec in sexagesimal DMS format (e.g. -07d 14m 42.53s)")
    cartesian_unit: Tuple[float, float, float] = Field(
        ..., description="Standard astronomical unit vector (X, Y, Z)"
    )
    threejs_vector: Tuple[float, float, float] = Field(
        ..., description="Three.js vector coordinates (x, y, z) on unit sphere"
    )


def deg_to_hms(ra_deg: float) -> str:
    """Convert RA from decimal degrees to 'XXh YYm ZZ.ZZs' string."""
    normalized_ra = (ra_deg % 360.0)
    total_hours = normalized_ra / 15.0
    hours = int(total_hours)
    minutes_rem = (total_hours - hours) * 60.0
    minutes = int(minutes_rem)
    seconds = (minutes_rem - minutes) * 60.0
    return f"{hours:02d}h {minutes:02d}m {seconds:05.2f}s"


def deg_to_dms(dec_deg: float) -> str:
    """Convert Dec from decimal degrees to '+/-XX° YY' ZZ.ZZ\"' string."""
    sign = "+" if dec_deg >= 0 else "-"
    abs_dec = abs(dec_deg)
    degrees = int(abs_dec)
    minutes_rem = (abs_dec - degrees) * 60.0
    minutes = int(minutes_rem)
    seconds = (minutes_rem - minutes) * 60.0
    return f"{sign}{degrees:02d}° {minutes:02d}' {seconds:05.2f}\""


def parse_sexagesimal_ra(ra_str: str) -> float:
    """Parse sexagesimal RA string to decimal degrees.
    Matches formats like:
    - 08h 55m 10.831s
    - 08:55:10.831
    - 08 55 10.831
    - 133.7951 (decimal fallback)
    """
    clean_ra = ra_str.strip()

    # Try plain float first
    try:
        val = float(clean_ra)
        return val % 360.0
    except ValueError:
        pass

    # Regex for sexagesimal patterns
    pattern = r"^\s*([0-9]{1,2})[h:\s]+([0-9]{1,2})[m:\s]+([0-9]{1,2}(?:\.[0-9]+)?)[s]?\s*$"
    match = re.match(pattern, clean_ra)
    if not match:
        raise ValueError(f"Invalid RA format: '{ra_str}'. Expected format e.g. '08h 55m 10.83s' or '133.7951'")

    h = float(match.group(1))
    m = float(match.group(2))
    s = float(match.group(3))

    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError(f"RA components out of range in '{ra_str}'")

    deg = (h + m / 60.0 + s / 3600.0) * 15.0
    return deg % 360.0


def parse_sexagesimal_dec(dec_str: str) -> float:
    """Parse sexagesimal Dec string to decimal degrees.
    Matches formats like:
    - -07° 14' 42.53"
    - -07d 14m 42.53s
    - -07:14:42.53
    - -07 14 42.53
    - -7.2451 (decimal fallback)
    """
    clean_dec = dec_str.strip()

    # Try plain float
    try:
        val = float(clean_dec)
        if -90.0 <= val <= 90.0:
            return val
        raise ValueError(f"Dec {val} out of bounds [-90, +90]")
    except ValueError as e:
        if "out of bounds" in str(e):
            raise

    # Regex for DMS patterns
    pattern = r"^\s*([+-]?)\s*([0-9]{1,2})[°d:\s]+([0-9]{1,2})['m:\s]+([0-9]{1,2}(?:\.[0-9]+)?)[\"s]?\s*$"
    match = re.match(pattern, clean_dec)
    if not match:
        raise ValueError(f"Invalid Dec format: '{dec_str}'. Expected format e.g. '-07° 14\' 42.53\"' or '-7.2451'")

    sign_str = match.group(1)
    sign = -1.0 if sign_str == "-" else 1.0
    d = float(match.group(2))
    m = float(match.group(3))
    s = float(match.group(4))

    if not (0 <= d <= 90 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError(f"Dec components out of range in '{dec_str}'")

    dec_val = sign * (d + m / 60.0 + s / 3600.0)
    if not (-90.0 <= dec_val <= 90.0):
        raise ValueError(f"Calculated Dec {dec_val} out of bounds [-90, +90]")

    return dec_val


def radec_to_cartesian(ra_deg: float, dec_deg: float, radius: float = 1.0) -> Tuple[float, float, float]:
    """Convert RA, Dec in degrees to standard astronomical 3D unit vector.
    X points to RA=0h, Dec=0 deg (Vernal Equinox)
    Y points to RA=6h, Dec=0 deg
    Z points to Dec=+90 deg (North Celestial Pole)
    """
    alpha = math.radians(ra_deg)
    delta = math.radians(dec_deg)

    x = radius * math.cos(delta) * math.cos(alpha)
    y = radius * math.cos(delta) * math.sin(alpha)
    z = radius * math.sin(delta)
    return (float(x), float(y), float(z))


def radec_to_threejs(ra_deg: float, dec_deg: float, radius: float = 100.0) -> Tuple[float, float, float]:
    """Convert RA/Dec to Three.js world space coordinates on a celestial sphere of given radius.
    Three.js convention:
    +Y is North Celestial Pole (up)
    -Z is RA = 0h (looking forward from origin onto celestial sphere)
    +X is RA = 6h (to the right when looking inward or outward with consistent handedness)
    To represent the sky from inside/outside looking at the celestial sphere:
    x = radius * cos(dec) * sin(ra)
    y = radius * sin(dec)
    z = -radius * cos(dec) * cos(ra)
    """
    alpha = math.radians(ra_deg)
    delta = math.radians(dec_deg)

    x = radius * math.cos(delta) * math.sin(alpha)
    y = radius * math.sin(delta)
    z = -radius * math.cos(delta) * math.cos(alpha)
    return (round(float(x), 5), round(float(y), 5), round(float(z), 5))


def angular_separation(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Calculate angular separation between two sky coordinates in degrees (Vincenty formula)."""
    phi1 = math.radians(dec1)
    phi2 = math.radians(dec2)
    delta_lambda = math.radians(ra1 - ra2)

    numerator = math.sqrt(
        (math.cos(phi2) * math.sin(delta_lambda)) ** 2
        + (math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)) ** 2
    )
    denominator = math.sin(phi1) * math.sin(phi2) + math.cos(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    angle_rad = math.atan2(numerator, denominator)
    return math.degrees(angle_rad)


def create_sky_coordinate(ra_input: str | float, dec_input: str | float) -> SkyCoordinate:
    """Parse and normalize sky coordinates from either string or float representations."""
    ra = parse_sexagesimal_ra(str(ra_input)) if isinstance(ra_input, str) else float(ra_input % 360.0)
    dec = parse_sexagesimal_dec(str(dec_input)) if isinstance(dec_input, str) else float(dec_input)

    if not (-90.0 <= dec <= 90.0):
        raise ValueError(f"Declination {dec} out of bounds [-90, +90]")

    ra_hms = deg_to_hms(ra)
    dec_dms = deg_to_dms(dec)
    cartesian = radec_to_cartesian(ra, dec, 1.0)
    threejs = radec_to_threejs(ra, dec, 1.0)

    return SkyCoordinate(
        ra_deg=round(ra, 6),
        dec_deg=round(dec, 6),
        ra_hms=ra_hms,
        dec_dms=dec_dms,
        cartesian_unit=(round(cartesian[0], 6), round(cartesian[1], 6), round(cartesian[2], 6)),
        threejs_vector=threejs,
    )
