"""Astronomical cutout generator and scientific display stretch module.
Creates WCS-calibrated FITS image products and web-ready rendered cutouts.
"""

from __future__ import annotations

import io
import math
import numpy as np
from PIL import Image
from typing import Tuple, Optional, Dict, Any

from astropy.io import fits
from astropy.wcs import WCS


def apply_astronomical_stretch(
    data: np.ndarray,
    stretch: str = "asinh",
    vmin_pct: float = 1.0,
    vmax_pct: float = 99.5,
    asinh_factor: float = 10.0,
) -> np.ndarray:
    """Apply standard scientific image stretches preserving photometric dynamics.
    Supported stretches: 'asinh' (default for IR), 'linear', 'log', 'sqrt'.
    """
    clean = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    vmin = float(np.percentile(clean, vmin_pct))
    vmax = float(np.percentile(clean, vmax_pct))

    if vmax <= vmin:
        vmax = vmin + 1.0

    clipped = np.clip((clean - vmin) / (vmax - vmin), 0.0, 1.0)

    if stretch == "asinh":
        # Lupton et al. (1999) astronomical asinh stretch
        normalized = np.arcsinh(clipped * asinh_factor) / np.arcsinh(asinh_factor)
    elif stretch == "log":
        normalized = np.log1p(clipped * 9.0) / np.log(10.0)
    elif stretch == "sqrt":
        normalized = np.sqrt(clipped)
    else:  # linear
        normalized = clipped

    return np.clip(normalized, 0.0, 1.0)


def create_synthetic_astronomical_cutout(
    ra_deg: float,
    dec_deg: float,
    fov_arcmin: float = 6.0,
    pixel_scale_arcsec: float = 6.2,  # SPHEREx detector scale ~6.2"/px
    channel_index: int = 50,
    epoch_id: str = "EPOCH-1",
    point_sources: Optional[list] = None,
    time_offset_days: float = 0.0,
    is_variable: bool = False,
    proper_motion_ra: float = 0.0,  # mas/yr
    proper_motion_dec: float = 0.0,  # mas/yr
) -> Tuple[np.ndarray, WCS, fits.Header]:
    """Generate a scientifically calibrated astronomical cutout image with Astropy WCS.
    Models background zodiacal emission, realistic detector noise floor, and point spread function (PSF).
    """
    # Calculate pixel dimensions (odd number for perfect center pixel)
    npix = int(round((fov_arcmin * 60.0) / pixel_scale_arcsec))
    npix = max(33, min(npix, 129))
    if npix % 2 == 0:
        npix += 1

    center_pix = (npix - 1) / 2.0

    # Build Astropy WCS header
    w = WCS(naxis=2)
    w.wcs.crpix = [center_pix + 1.0, center_pix + 1.0]
    w.wcs.cdelt = [-pixel_scale_arcsec / 3600.0, pixel_scale_arcsec / 3600.0]
    w.wcs.crval = [ra_deg, dec_deg]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

    # Realistic infrared background (MJy/sr) depending on wavelength
    # SPHEREx observes zodiacal light minimum around 3.5 um (~0.1 - 0.5 MJy/sr)
    zodi_bg = 0.15 + 0.05 * math.sin(math.radians(ra_deg * 2.0))
    rng = np.random.default_rng(seed=int(abs(ra_deg * 1000 + dec_deg * 100 + channel_index * 10)) % 100000)

    # Detector noise floor
    noise = rng.normal(loc=0.0, scale=0.012, size=(npix, npix))
    data = np.full((npix, npix), zodi_bg) + noise

    # Proper motion shift in pixels over time_offset_days
    pm_ra_arcsec = (proper_motion_ra / 1000.0) * (time_offset_days / 365.25)
    pm_dec_arcsec = (proper_motion_dec / 1000.0) * (time_offset_days / 365.25)

    pm_dx_pix = -pm_ra_arcsec / pixel_scale_arcsec
    pm_dy_pix = pm_dec_arcsec / pixel_scale_arcsec

    # Primary target at center
    base_target_flux = 1.25  # MJy/sr
    if is_variable:
        # Variable star modulation (e.g. Mira period ~250d or T Tauri erratic dimming)
        phase = (time_offset_days % 250.0) / 250.0
        var_factor = 0.4 + 1.2 * (0.5 + 0.5 * math.cos(2.0 * math.pi * phase))
        base_target_flux *= var_factor

    # Render target Gaussian PSF (~1.5 pixels FWHM)
    fwhm_pix = 1.8
    sigma_pix = fwhm_pix / 2.355

    target_x = center_pix + pm_dx_pix
    target_y = center_pix + pm_dy_pix

    y_indices, x_indices = np.indices((npix, npix))
    r_sq = (x_indices - target_x) ** 2 + (y_indices - target_y) ** 2
    target_psf = base_target_flux * np.exp(-0.5 * r_sq / (sigma_pix ** 2))
    data += target_psf

    # Add surrounding field stars if any
    sources = point_sources or []
    for src in sources:
        sx = center_pix + src.get("dx_pix", 0.0)
        sy = center_pix + src.get("dy_pix", 0.0)
        sflux = src.get("flux_mjy", 0.2)
        sr_sq = (x_indices - sx) ** 2 + (y_indices - sy) ** 2
        data += sflux * np.exp(-0.5 * sr_sq / (sigma_pix ** 2))

    # Construct complete FITS header
    header = fits.Header()
    header["SIMPLE"] = True
    header["BITPIX"] = -32
    header["NAXIS"] = 2
    header["NAXIS1"] = npix
    header["NAXIS2"] = npix
    header["CRPIX1"] = center_pix + 1.0
    header["CRPIX2"] = center_pix + 1.0
    header["CRVAL1"] = ra_deg
    header["CRVAL2"] = dec_deg
    header["CDELT1"] = -pixel_scale_arcsec / 3600.0
    header["CDELT2"] = pixel_scale_arcsec / 3600.0
    header["CTYPE1"] = "RA---TAN"
    header["CTYPE2"] = "DEC--TAN"
    header["BUNIT"] = "MJy/sr"
    header["TELESCOP"] = "SPHEREx"
    header["INSTRUME"] = "SPHEREx-LVF"
    header["CHANNEL"] = channel_index
    header["EPOCH_ID"] = epoch_id
    header["EXPTIME"] = 120.0

    return data.astype(np.float32), w, header


def cutout_to_png_bytes(
    data: np.ndarray,
    stretch: str = "asinh",
    colormap: str = "astronomy",
) -> bytes:
    """Render 2D float astronomical array to PNG bytes with scientific contrast stretch."""
    stretched = apply_astronomical_stretch(data, stretch=stretch)
    h, w = stretched.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)

    if colormap == "astronomy":
        # Deep space dark indigo -> cyan -> white core
        for y in range(h):
            for x in range(w):
                v = stretched[y, x]
                # non-linear color ramps
                r = int(np.clip(255 * (v ** 1.6), 0, 255))
                g = int(np.clip(255 * (v ** 1.1), 0, 255))
                b = int(np.clip(255 * (0.15 + 0.85 * (v ** 0.8)), 0, 255))
                rgb[y, x] = [r, g, b]
    else:
        # Grayscale
        gray = (stretched * 255).astype(np.uint8)
        rgb[:, :, 0] = gray
        rgb[:, :, 1] = gray
        rgb[:, :, 2] = gray

    img = Image.fromarray(rgb, mode="RGB")
    # Upscale 2x with bilinear filtering for crisp display on high-DPI
    upscaled = img.resize((w * 4, h * 4), Image.Resampling.BILINEAR)

    buf = io.BytesIO()
    upscaled.save(buf, format="PNG")
    return buf.getvalue()
