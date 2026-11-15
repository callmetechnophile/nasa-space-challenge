"""FastAPI endpoints for Astronomical Cutouts, FITS files, and Difference Imaging."""

from __future__ import annotations

import io
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.image_processing.cutout import (
    create_synthetic_astronomical_cutout,
    cutout_to_png_bytes,
)
from app.image_processing.diff_imaging import compute_difference_image
from app.models.schemas import DifferenceAnalysisResult
from app.providers import get_data_provider
from app.astronomy.coordinates import parse_sexagesimal_ra, parse_sexagesimal_dec
from app.spectral.bands import get_band_by_channel

router = APIRouter(prefix="/images", tags=["images"])


class DifferenceRequest(BaseModel):
    target: Optional[str] = None
    ra: Optional[str | float] = None
    dec: Optional[str | float] = None
    epoch_ref: str = "EPOCH-PASS1-20250615"
    epoch_cmp: str = "EPOCH-PASS2-20251214"
    channel: int = 50
    sigma_threshold: float = 3.5


def _resolve_coords_and_target(target: Optional[str], ra: Optional[str | float], dec: Optional[str | float]):
    provider = get_data_provider("curated")
    t_obj = None
    if target:
        t_obj = provider.get_target_by_id(target)
        if t_obj:
            return t_obj.ra_deg, t_obj.dec_deg, t_obj

    if ra is not None and dec is not None:
        ra_val = parse_sexagesimal_ra(str(ra))
        dec_val = parse_sexagesimal_dec(str(dec))
        matches = provider.search_by_coordinates(ra_val, dec_val, radius_deg=0.5)
        if matches:
            return matches[0].ra_deg, matches[0].dec_deg, matches[0]
        return ra_val, dec_val, None

    # Fallback to WISE 0855
    t_obj = provider.get_target_by_id("wise-0855")
    return t_obj.ra_deg, t_obj.dec_deg, t_obj


@router.get("/cutout")
def get_image_cutout(
    target: Optional[str] = Query(None),
    ra: Optional[str] = Query(None),
    dec: Optional[str] = Query(None),
    epoch: str = Query("EPOCH-PASS1-20250615"),
    channel: int = Query(50, ge=1, le=102),
    stretch: str = Query("asinh", description="Stretch: 'asinh', 'linear', 'log', 'sqrt'"),
    colormap: str = Query("astronomy", description="Colormap: 'astronomy' or 'gray'"),
    fov_arcmin: float = Query(6.0, ge=1.0, le=30.0),
):
    """Generate high-contrast calibrated PNG cutout tile."""
    ra_deg, dec_deg, t_obj = _resolve_coords_and_target(target, ra, dec)

    # Determine epoch timing
    epoch_days = 0.0
    if "PASS2" in epoch or "20251214" in epoch:
        epoch_days = 182.0
    elif "PASS3" in epoch or "20260618" in epoch:
        epoch_days = 368.0
    elif "PASS4" in epoch or "20261105" in epoch:
        epoch_days = 508.0

    is_var = False
    pm_ra = 0.0
    pm_dec = 0.0
    if t_obj:
        is_var = t_obj.id in ["rw-aurigae", "r-draconis"]
        pm_ra = t_obj.proper_motion_ra_mas_yr or 0.0
        pm_dec = t_obj.proper_motion_dec_mas_yr or 0.0

    data, wcs, header = create_synthetic_astronomical_cutout(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        fov_arcmin=fov_arcmin,
        channel_index=channel,
        epoch_id=epoch,
        time_offset_days=epoch_days,
        is_variable=is_var,
        proper_motion_ra=pm_ra,
        proper_motion_dec=pm_dec,
    )

    png_bytes = cutout_to_png_bytes(data, stretch=stretch, colormap=colormap)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/fits")
def download_fits(
    target: Optional[str] = Query(None),
    ra: Optional[str] = Query(None),
    dec: Optional[str] = Query(None),
    epoch: str = Query("EPOCH-PASS1-20250615"),
    channel: int = Query(50, ge=1, le=102),
    fov_arcmin: float = Query(6.0),
):
    """Download calibrated Astropy WCS FITS image file."""
    ra_deg, dec_deg, t_obj = _resolve_coords_and_target(target, ra, dec)

    is_var = False
    pm_ra = 0.0
    pm_dec = 0.0
    if t_obj:
        is_var = t_obj.id in ["rw-aurigae", "r-draconis"]
        pm_ra = t_obj.proper_motion_ra_mas_yr or 0.0
        pm_dec = t_obj.proper_motion_dec_mas_yr or 0.0

    data, wcs, header = create_synthetic_astronomical_cutout(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        fov_arcmin=fov_arcmin,
        channel_index=channel,
        epoch_id=epoch,
        is_variable=is_var,
        proper_motion_ra=pm_ra,
        proper_motion_dec=pm_dec,
    )

    from astropy.io import fits
    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)

    filename = f"SPHEREx_{target or f'{ra_deg:.2f}_{dec_deg:.2f}'}_{epoch}_band{channel}.fits"
    return Response(
        content=buf.getvalue(),
        media_type="application/fits",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/difference", response_model=DifferenceAnalysisResult)
def run_difference_imaging(req: DifferenceRequest) -> DifferenceAnalysisResult:
    """Perform statistical difference imaging D = |I2 - I1| between two observation epochs."""
    ra_deg, dec_deg, t_obj = _resolve_coords_and_target(req.target, req.ra, req.dec)

    def get_days(ep: str) -> float:
        if "PASS2" in ep or "20251214" in ep:
            return 182.0
        if "PASS3" in ep or "20260618" in ep:
            return 368.0
        if "PASS4" in ep or "20261105" in ep:
            return 508.0
        return 0.0

    days1 = get_days(req.epoch_ref)
    days2 = get_days(req.epoch_cmp)

    is_var = False
    pm_ra = 0.0
    pm_dec = 0.0
    if t_obj:
        is_var = t_obj.id in ["rw-aurigae", "r-draconis"]
        pm_ra = t_obj.proper_motion_ra_mas_yr or 0.0
        pm_dec = t_obj.proper_motion_dec_mas_yr or 0.0

    img1, _, _ = create_synthetic_astronomical_cutout(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        fov_arcmin=6.0,
        channel_index=req.channel,
        epoch_id=req.epoch_ref,
        time_offset_days=days1,
        is_variable=is_var,
        proper_motion_ra=pm_ra,
        proper_motion_dec=pm_dec,
    )

    img2, _, _ = create_synthetic_astronomical_cutout(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        fov_arcmin=6.0,
        channel_index=req.channel,
        epoch_id=req.epoch_cmp,
        time_offset_days=days2,
        is_variable=is_var,
        proper_motion_ra=pm_ra,
        proper_motion_dec=pm_dec,
    )

    band_info = get_band_by_channel(req.channel)
    wl = band_info.wavelength_um if band_info else 3.12

    result = compute_difference_image(
        image1=img1,
        image2=img2,
        center_ra=ra_deg,
        center_dec=dec_deg,
        pixel_scale_arcsec=6.2,
        sigma_threshold=req.sigma_threshold,
        channel_index=req.channel,
        wavelength_um=wl,
        epoch_ref_id=req.epoch_ref,
        epoch_ref_date="2025-06-15" if days1 == 0 else "2025-12-14",
        epoch_cmp_id=req.epoch_cmp,
        epoch_cmp_date="2025-12-14" if days2 == 182.0 else "2026-06-18",
        delta_days=abs(days2 - days1),
        target_name=t_obj.name if t_obj else None,
    )

    return result
