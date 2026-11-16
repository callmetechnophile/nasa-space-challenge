"""FastAPI endpoints for Astronomical Cutouts, FITS files, and Difference Imaging."""

from __future__ import annotations

import io
import os
import glob
from typing import Optional, Tuple
import numpy as np
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.image_processing.cutout import (
    create_synthetic_astronomical_cutout,
    cutout_to_png_bytes,
    extract_real_fits_cutout,
)
from app.image_processing.diff_imaging import compute_difference_image
from app.models.schemas import DifferenceAnalysisResult, TransientCandidate
from app.models.provenance import (
    ScientificDatasetProvenance,
    ProvenanceState,
    AUTHENTIC_FITS_REGISTRY,
)
from app.services.temporal_service import TemporalService
from app.providers import get_data_provider
from app.astronomy.coordinates import parse_sexagesimal_ra, parse_sexagesimal_dec
from app.spectral.bands import get_band_by_channel

router = APIRouter(prefix="/images", tags=["images"])
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex"))


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

    # Default to WISE 0855
    t_obj = provider.get_target_by_id("wise-0855")
    return t_obj.ra_deg, t_obj.dec_deg, t_obj


def _find_real_fits_cutout(ra_deg: float, dec_deg: float, fov_arcmin: float) -> Optional[Tuple[Any, Any, Any, str]]:
    """Check if any authentic Level-2 SPHEREx FITS covers these coordinates."""
    if not os.path.exists(DATA_DIR):
        return None

    for fname in AUTHENTIC_FITS_REGISTRY.keys():
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            cutout_res = extract_real_fits_cutout(fpath, ra_deg, dec_deg, fov_arcmin, allow_center_fallback=False)
            if cutout_res is not None:
                data, wcs, header = cutout_res
                return data, wcs, header, fname
    return None


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
    allow_demo: bool = Query(True, description="Allow synthetic demonstration fallback if no flight data exists"),
):
    """Generate high-contrast calibrated PNG cutout tile with explicit provenance headers."""
    ra_deg, dec_deg, t_obj = _resolve_coords_and_target(target, ra, dec)

    # 1. Check if epoch directly names or references a real SPHEREx flight observation
    temp_service = TemporalService(DATA_DIR)
    is_real_epoch_ref = (
        epoch in AUTHENTIC_FITS_REGISTRY
        or epoch.startswith("level2_")
        or epoch.endswith(".fits")
        or "W31" in epoch
        or "W32" in epoch
        or "W44" in epoch
    )

    if is_real_epoch_ref:
        fpath = temp_service.resolve_or_fetch_observation_file(epoch)
        if not fpath:
            # Try to map OBSID to filename in registry
            for reg_name, reg_meta in AUTHENTIC_FITS_REGISTRY.items():
                if reg_meta.get("observation_id") == epoch or epoch in reg_name:
                    fpath = temp_service.resolve_or_fetch_observation_file(reg_name)
                    break

        if fpath and os.path.exists(fpath):
            cutout_res = extract_real_fits_cutout(
                fpath, ra_deg, dec_deg, fov_arcmin=fov_arcmin, allow_center_fallback=True
            )
            if cutout_res is not None:
                data, wcs, header = cutout_res
                clean_data = np.nan_to_num(data, nan=0.0)
                png_bytes = cutout_to_png_bytes(data, stretch=stretch, colormap=colormap)
                obs_id = str(header.get("OBSID", os.path.basename(fpath).split(".")[0]))
                date_obs = str(header.get("DATE-OBS", "UNKNOWN"))
                return Response(
                    content=png_bytes,
                    media_type="image/png",
                    headers={
                        "X-Data-Provenance": "REAL_VERIFIED",
                        "X-Source-Product": os.path.basename(fpath),
                        "X-Data-Classification": "REAL",
                        "X-Observation-ID": obs_id,
                        "X-Observation-Date": date_obs,
                        "X-Pixel-Min": f"{float(np.nanmin(data)):.4f}",
                        "X-Pixel-Max": f"{float(np.nanmax(data)):.4f}",
                        "X-Pixel-Mean": f"{float(np.nanmean(data)):.4f}",
                        "X-Valid-Pixels": str(int((~np.isnan(data)).sum())),
                        "X-Display-Stretch": stretch,
                        "X-Display-Colormap": colormap,
                    },
                )
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "stage": "FITS_RETRIEVAL",
                    "category": "PRODUCT_NOT_FOUND",
                    "message": f"Authentic SPHEREx observation file not found or could not be retrieved: {epoch}",
                    "filename": epoch,
                },
            )

    # 2. Check if any authentic Level-2 SPHEREx FITS covers these coordinates
    real_cutout = _find_real_fits_cutout(ra_deg, dec_deg, fov_arcmin)
    if real_cutout is not None:
        data, wcs, header, fname = real_cutout
        png_bytes = cutout_to_png_bytes(data, stretch=stretch, colormap=colormap)
        obs_id = str(header.get("OBSID", fname.split(".")[0]))
        date_obs = str(header.get("DATE-OBS", "UNKNOWN"))
        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={
                "X-Data-Provenance": "REAL_VERIFIED",
                "X-Source-Product": fname,
                "X-Data-Classification": "REAL",
                "X-Observation-ID": obs_id,
                "X-Observation-Date": date_obs,
                "X-Pixel-Min": f"{float(np.nanmin(data)):.4f}",
                "X-Pixel-Max": f"{float(np.nanmax(data)):.4f}",
                "X-Pixel-Mean": f"{float(np.nanmean(data)):.4f}",
                "X-Valid-Pixels": str(int((~np.isnan(data)).sum())),
                "X-Display-Stretch": stretch,
                "X-Display-Colormap": colormap,
            },
        )

    # 3. If explicit flight data was requested without demo consent, return 404
    if not allow_demo and not ("PASS" in epoch or "SIM" in epoch):
        raise HTTPException(
            status_code=404,
            detail={
                "stage": "FOOTPRINT_VALIDATION",
                "category": "NO_OBSERVATION_COVERAGE",
                "message": f"No authentic SPHEREx flight observation covers coordinates ({ra_deg:.4f}, {dec_deg:.4f}) in release {epoch}",
            },
        )

    # 4. Generate explicit synthetic demonstration cutout
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
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "X-Data-Provenance": "SYNTHETIC_DEMO",
            "X-Source-Product": "SkyTrace_Synthetic_Cutout_Generator",
            "X-Data-Classification": "SYNTHETIC",
            "X-Observation-ID": epoch,
            "X-Observation-Date": "SIMULATED_CADENCE",
            "X-Display-Stretch": stretch,
            "X-Display-Colormap": colormap,
        },
    )


@router.get("/fits")
def download_fits(
    target: Optional[str] = Query(None),
    ra: Optional[str] = Query(None),
    dec: Optional[str] = Query(None),
    epoch: str = Query("EPOCH-PASS1-20250615"),
    channel: int = Query(50, ge=1, le=102),
    fov_arcmin: float = Query(6.0),
):
    """Download calibrated Astropy WCS FITS image file with strict provenance labeling."""
    ra_deg, dec_deg, t_obj = _resolve_coords_and_target(target, ra, dec)

    # 1. Check if authentic Level-2 FITS covers this coordinate
    real_cutout = _find_real_fits_cutout(ra_deg, dec_deg, fov_arcmin)
    if real_cutout is not None:
        data, wcs, header, fname = real_cutout
        from astropy.io import fits
        hdu = fits.PrimaryHDU(data=data, header=header)
        buf = io.BytesIO()
        hdu.writeto(buf)
        filename = f"SPHEREx_REAL_{target or f'{ra_deg:.2f}_{dec_deg:.2f}'}_{epoch}_band{channel}.fits"
        return Response(
            content=buf.getvalue(),
            media_type="application/fits",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Data-Provenance": "REAL_VERIFIED",
                "X-Source-Product": fname,
                "X-Data-Classification": "REAL",
            },
        )

    # 2. Synthetic demonstration FITS file
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

    filename = f"SPHEREx_SYNTHETIC_{target or f'{ra_deg:.2f}_{dec_deg:.2f}'}_{epoch}_band{channel}.fits"
    return Response(
        content=buf.getvalue(),
        media_type="application/fits",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Data-Provenance": "SYNTHETIC_DEMO",
            "X-Source-Product": "SkyTrace_Synthetic_Cutout_Generator",
            "X-Data-Classification": "SYNTHETIC",
        },
    )


@router.post("/difference", response_model=DifferenceAnalysisResult)
def run_difference_imaging(req: DifferenceRequest) -> DifferenceAnalysisResult:
    """Perform statistical difference imaging D = |I2 - I1| between two observation epochs.
    Attaches explicit provenance classifying synthetic demonstration vs real flight analysis.
    """
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

    # Attach rigorous provenance classification
    prov = ScientificDatasetProvenance(
        provenance_state=ProvenanceState.SYNTHETIC_DEMO,
        data_source="SkyTrace Synthetic Difference Simulator",
        product_or_catalogue_id=f"DIFF-SYNTH-{req.epoch_ref}-{req.epoch_cmp}-CH{req.channel}",
        observation_id=f"{req.epoch_ref}_{req.epoch_cmp}",
        synthetic_real_classification="SYNTHETIC",
        validation_status="SIMULATED",
        scientific_notes="Difference image and extracted candidates derived from procedural test cutouts. Extracted candidates are simulation injections for UI testing, NOT verified astronomical detections.",
    )

    # Mark candidates as simulated injections
    marked_candidates = []
    for c in result.candidates:
        c_dict = c.model_dump() if hasattr(c, "model_dump") else c.dict()
        c_dict["is_simulated_injection"] = True
        marked_candidates.append(TransientCandidate(**c_dict))

    result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    result_dict["provenance"] = prov
    result_dict["candidates"] = marked_candidates

    return DifferenceAnalysisResult(**result_dict)
