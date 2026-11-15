"""WCS Processing Engine for SPHEREx 3D Sky Explorer.
Handles FITS WCS initialization, pixel-to-world & world-to-pixel coordinate
transformations, pixel scale calculations, round-trip residual validation,
and footprint extraction using Astropy WCS.
"""

from __future__ import annotations

import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from pydantic import BaseModel, Field

from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales


class WcsMetadata(BaseModel):
    """Structured WCS metadata for client ingestion and visualization."""
    wcs_valid: bool = Field(..., description="Whether WCS initialized cleanly without errors")
    projection_type: str = Field(..., description="Projection code, e.g. TAN, SIN, CAR")
    ctype1: str = Field(..., description="Axis 1 coordinate type (e.g. RA---TAN)")
    ctype2: str = Field(..., description="Axis 2 coordinate type (e.g. DEC--TAN)")
    crval1: float = Field(..., description="Reference Right Ascension in degrees")
    crval2: float = Field(..., description="Reference Declination in degrees")
    crpix1: float = Field(..., description="Reference pixel X (1-based FITS convention)")
    crpix2: float = Field(..., description="Reference pixel Y (1-based FITS convention)")
    cdelt1: Optional[float] = Field(None, description="Coordinate increment per pixel on Axis 1")
    cdelt2: Optional[float] = Field(None, description="Coordinate increment per pixel on Axis 2")
    cunit1: str = Field("deg", description="Units of coordinate Axis 1")
    cunit2: str = Field("deg", description="Units of coordinate Axis 2")
    pixel_scale_arcsec: float = Field(..., description="Mean pixel scale in arcseconds per pixel")
    pixel_scale_x_arcsec: float = Field(..., description="X-axis pixel scale in arcseconds per pixel")
    pixel_scale_y_arcsec: float = Field(..., description="Y-axis pixel scale in arcseconds per pixel")
    rotation_deg: float = Field(0.0, description="Estimated position angle / orientation in degrees")
    round_trip_residual_pixels: float = Field(..., description="Maximum round-trip transformation residual in pixels")
    center_radec: Tuple[float, float] = Field(..., description="Center (RA, Dec) in degrees")
    footprint_corners: List[Tuple[float, float]] = Field(
        ..., description="4 corner (RA, Dec) coordinates: [bottom-left, bottom-right, top-right, top-left]"
    )


def extract_wcs(header: fits.Header) -> WCS:
    """Initialize an Astropy WCS object from a FITS header.
    Validates that celestial axes are present.
    Filters out any non-standard tabular coordinate keys (e.g. CTYPE1W='WAVE-TAB')
    that can cause wcslib to crash when reading primary celestial coordinates.
    """
    clean_hdr = header.copy()
    for k in list(clean_hdr.keys()):
        # Remove alternate tabular WCS systems (e.g. CTYPE1W, CRVAL1W)
        if any(k.startswith(prefix) and len(k) > len(prefix) for prefix in ["CTYPE", "CRVAL", "CRPIX", "CDELT"]):
            val = str(clean_hdr.get(k, ""))
            if "TAB" in val or k.endswith("W") or k.endswith("A"):
                del clean_hdr[k]

    try:
        wcs = WCS(clean_hdr, naxis=2)
    except Exception as e:
        raise ValueError(f"Failed to initialize WCS from FITS header: {e}")

    if not wcs.is_celestial:
        raise ValueError("FITS header does not contain valid celestial coordinates (RA/Dec)")

    return wcs


def pixel_to_world(
    wcs: WCS,
    x: float | np.ndarray,
    y: float | np.ndarray,
    origin: int = 0
) -> Tuple[float | np.ndarray, float | np.ndarray]:
    """Transform pixel coordinates to world celestial coordinates (RA, Dec in degrees).
    origin: 0 for 0-based numpy/canvas array indexing; 1 for 1-based FITS convention.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    # all_pix2world applies distortion corrections if present
    ra_deg, dec_deg = wcs.all_pix2world(x_arr, y_arr, origin)

    # Normalize RA to [0, 360)
    ra_deg = np.remainder(ra_deg, 360.0)
    # Clamp Dec to [-90, +90]
    dec_deg = np.clip(dec_deg, -90.0, 90.0)

    if np.isscalar(x) and np.isscalar(y):
        return float(ra_deg), float(dec_deg)
    return ra_deg, dec_deg


def world_to_pixel(
    wcs: WCS,
    ra_deg: float | np.ndarray,
    dec_deg: float | np.ndarray,
    origin: int = 0
) -> Tuple[float | np.ndarray, float | np.ndarray]:
    """Transform world celestial coordinates (RA, Dec in degrees) to pixel coordinates.
    origin: 0 for 0-based indexing; 1 for 1-based FITS convention.
    """
    ra_arr = np.asarray(ra_deg, dtype=np.float64)
    dec_arr = np.asarray(dec_deg, dtype=np.float64)

    x, y = wcs.all_world2pix(ra_arr, dec_arr, origin)

    if np.isscalar(ra_deg) and np.isscalar(dec_deg):
        return float(x), float(y)
    return x, y


def get_pixel_scales_arcsec(wcs: WCS) -> Tuple[float, float, float]:
    """Calculate pixel scales in arcseconds per pixel (mean, x, y)."""
    try:
        scales_deg = proj_plane_pixel_scales(wcs)
        scale_x = float(scales_deg[0] * 3600.0)
        scale_y = float(scales_deg[1] * 3600.0)
        mean_scale = float(np.mean(scales_deg) * 3600.0)
        return mean_scale, scale_x, scale_y
    except Exception:
        # Fallback if proj_plane_pixel_scales fails
        cdelt = getattr(wcs.wcs, "cdelt", [0.001, 0.001])
        sx = abs(float(cdelt[0])) * 3600.0
        sy = abs(float(cdelt[1])) * 3600.0
        return (sx + sy) / 2.0, sx, sy


def validate_round_trip(
    wcs: WCS,
    width: int,
    height: int,
    grid_size: int = 5
) -> Tuple[float, float]:
    """Verify numerical reversibility of pixel <-> world transformations.
    Tests a grid of points across the image and computes residuals.
    Returns: (max_residual_pixels, mean_residual_pixels)
    """
    xs = np.linspace(0.0, float(width - 1), grid_size)
    ys = np.linspace(0.0, float(height - 1), grid_size)
    grid_x, grid_y = np.meshgrid(xs, ys)

    # 1. Pixel -> World
    ra, dec = pixel_to_world(wcs, grid_x, grid_y, origin=0)

    # 2. World -> Pixel
    px, py = world_to_pixel(wcs, ra, dec, origin=0)

    # 3. Residuals
    dx = px - grid_x
    dy = py - grid_y
    residuals = np.sqrt(dx * dx + dy * dy)

    max_res = float(np.max(residuals))
    mean_res = float(np.mean(residuals))
    return max_res, mean_res


def extract_wcs_metadata(wcs: WCS, width: int, height: int) -> WcsMetadata:
    """Extract complete, validated WCS metadata from an Astropy WCS instance."""
    # 1. Coordinate types and projection
    ctype1 = str(wcs.wcs.ctype[0])
    ctype2 = str(wcs.wcs.ctype[1])
    proj = ctype1.split("-")[-1] if "-" in ctype1 else "TAN"

    # 2. Reference parameters
    crval1 = float(wcs.wcs.crval[0]) % 360.0
    crval2 = float(wcs.wcs.crval[1])
    crpix1 = float(wcs.wcs.crpix[0])
    crpix2 = float(wcs.wcs.crpix[1])

    cdelt1 = float(wcs.wcs.cdelt[0]) if hasattr(wcs.wcs, "cdelt") and len(wcs.wcs.cdelt) > 0 else None
    cdelt2 = float(wcs.wcs.cdelt[1]) if hasattr(wcs.wcs, "cdelt") and len(wcs.wcs.cdelt) > 1 else None

    cunit1 = str(wcs.wcs.cunit[0]) if len(wcs.wcs.cunit) > 0 else "deg"
    cunit2 = str(wcs.wcs.cunit[1]) if len(wcs.wcs.cunit) > 1 else "deg"

    # 3. Pixel scales
    mean_scale, scale_x, scale_y = get_pixel_scales_arcsec(wcs)

    # 4. Rotation angle estimation (measuring East of North)
    rotation = 0.0
    try:
        cd = wcs.pixel_scale_matrix
        if cd is not None and cd.shape == (2, 2):
            rotation = math.degrees(math.atan2(cd[0, 1], -cd[0, 0]))
    except Exception:
        if hasattr(wcs.wcs, "cd") and wcs.wcs.cd is not None and np.any(wcs.wcs.cd):
            cd = wcs.wcs.cd
            rotation = math.degrees(math.atan2(cd[0, 1], -cd[0, 0]))
        elif hasattr(wcs.wcs, "pc") and wcs.wcs.pc is not None:
            pc = wcs.wcs.pc
            rotation = math.degrees(math.atan2(pc[0, 1], -pc[0, 0]))

    # 5. Round trip residual verification
    max_res, _ = validate_round_trip(wcs, width, height)

    # 6. Center coordinate
    center_x = (width - 1) / 2.0
    center_y = (height - 1) / 2.0
    center_ra, center_dec = pixel_to_world(wcs, center_x, center_y, origin=0)

    # 7. Footprint corners: [bottom-left, bottom-right, top-right, top-left]
    corner_pixels = np.array([
        [0.0, 0.0],
        [float(width - 1), 0.0],
        [float(width - 1), float(height - 1)],
        [0.0, float(height - 1)]
    ])
    corners_ra, corners_dec = pixel_to_world(wcs, corner_pixels[:, 0], corner_pixels[:, 1], origin=0)
    footprint = [
        (float(corners_ra[i]), float(corners_dec[i]))
        for i in range(4)
    ]

    return WcsMetadata(
        wcs_valid=True,
        projection_type=proj,
        ctype1=ctype1,
        ctype2=ctype2,
        crval1=crval1,
        crval2=crval2,
        crpix1=crpix1,
        crpix2=crpix2,
        cdelt1=cdelt1,
        cdelt2=cdelt2,
        cunit1=cunit1,
        cunit2=cunit2,
        pixel_scale_arcsec=round(mean_scale, 4),
        pixel_scale_x_arcsec=round(scale_x, 4),
        pixel_scale_y_arcsec=round(scale_y, 4),
        rotation_deg=round(rotation, 4),
        round_trip_residual_pixels=round(max_res, 6),
        center_radec=(round(center_ra, 6), round(center_dec, 6)),
        footprint_corners=[(round(ra, 6), round(dec, 6)) for ra, dec in footprint],
    )
