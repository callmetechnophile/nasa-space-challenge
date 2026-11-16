"""Astronomical cutout generator and scientific display stretch module.
Extracts authentic cutouts from calibrated FITS files or generates explicitly marked synthetic fixtures.
"""

from __future__ import annotations

import io
import os
import math
import numpy as np
from PIL import Image
from typing import Tuple, Optional, Dict, Any

from astropy.io import fits
from astropy.wcs import WCS
from astropy.nddata import Cutout2D
from astropy.coordinates import SkyCoord
import astropy.units as u


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
        normalized = np.arcsinh(clipped * asinh_factor) / np.arcsinh(asinh_factor)
    elif stretch == "log":
        normalized = np.log1p(clipped * 9.0) / np.log(10.0)
    elif stretch == "sqrt":
        normalized = np.sqrt(clipped)
    else:  # linear
        normalized = clipped

    return np.clip(normalized, 0.0, 1.0)


def extract_real_fits_cutout(
    fits_path: str,
    ra_deg: float,
    dec_deg: float,
    fov_arcmin: float = 6.0,
    allow_center_fallback: bool = False,
) -> Optional[Tuple[np.ndarray, WCS, fits.Header]]:
    """Extract an authentic 2D sub-array cutout from a real SPHEREx FITS product if coordinates are covered."""
    if not os.path.exists(fits_path):
        return None

    try:
        with fits.open(fits_path) as hdul:
            # Find image HDU
            img_hdu = None
            if len(hdul) > 1 and hdul[1].data is not None:
                img_hdu = hdul[1]
            elif hdul[0].data is not None:
                img_hdu = hdul[0]

            if img_hdu is None or img_hdu.data is None:
                return None

            header = img_hdu.header.copy()
            w = WCS(header)
            if not w.is_celestial:
                return None

            pos = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")
            size = (fov_arcmin * u.arcmin, fov_arcmin * u.arcmin)

            # Check if position falls within footprint
            in_bounds = False
            try:
                pix_x, pix_y = w.world_to_pixel(pos)
                ny, nx = img_hdu.data.shape
                if 0 <= pix_x < nx and 0 <= pix_y < ny:
                    in_bounds = True
            except Exception:
                in_bounds = False

            if not in_bounds:
                if allow_center_fallback:
                    crval1 = float(header.get("CRVAL1", ra_deg))
                    crval2 = float(header.get("CRVAL2", dec_deg))
                    pos = SkyCoord(ra=crval1 * u.deg, dec=crval2 * u.deg, frame="icrs")
                else:
                    return None

            cutout = Cutout2D(img_hdu.data.astype(np.float32), position=pos, size=size, wcs=w, mode="trim")
            out_header = cutout.wcs.to_header()
            out_header["BUNIT"] = header.get("BUNIT", "MJy/sr")
            out_header["TELESCOP"] = header.get("TELESCOP", "SPHEREx")
            out_header["INSTRUME"] = header.get("INSTRUME", "SPHEREx")
            out_header["DATE-OBS"] = header.get("DATE-OBS", "UNKNOWN")
            out_header["MJD-OBS"] = header.get("MJD-OBS", 0.0)
            out_header["OBSID"] = header.get("OBSID", os.path.basename(fits_path).split(".")[0])
            out_header["DETECTOR"] = header.get("DETECTOR", 1)
            out_header["PROVENAN"] = "REAL_VERIFIED"
            out_header["SRCFIL"] = os.path.basename(fits_path)

            return cutout.data, cutout.wcs, out_header
    except Exception:
        return None


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
    """Generate an explicitly marked synthetic demonstration astronomical cutout with Astropy WCS.
    Models background zodiacal emission, realistic detector noise floor, and point spread function (PSF).
    """
    npix = int(round((fov_arcmin * 60.0) / pixel_scale_arcsec))
    npix = max(33, min(npix, 129))
    if npix % 2 == 0:
        npix += 1

    center_pix = (npix - 1) / 2.0

    w = WCS(naxis=2)
    w.wcs.crpix = [center_pix + 1.0, center_pix + 1.0]
    w.wcs.cdelt = [-pixel_scale_arcsec / 3600.0, pixel_scale_arcsec / 3600.0]
    w.wcs.crval = [ra_deg, dec_deg]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

    zodi_bg = 0.15 + 0.05 * math.sin(math.radians(ra_deg * 2.0))
    rng = np.random.default_rng(seed=int(abs(ra_deg * 1000 + dec_deg * 100 + channel_index * 10)) % 100000)

    noise = rng.normal(loc=0.0, scale=0.012, size=(npix, npix))
    data = np.full((npix, npix), zodi_bg) + noise

    pm_ra_arcsec = (proper_motion_ra / 1000.0) * (time_offset_days / 365.25)
    pm_dec_arcsec = (proper_motion_dec / 1000.0) * (time_offset_days / 365.25)

    pm_dx_pix = -pm_ra_arcsec / pixel_scale_arcsec
    pm_dy_pix = pm_dec_arcsec / pixel_scale_arcsec

    base_target_flux = 1.25  # MJy/sr
    if is_variable:
        phase = (time_offset_days % 250.0) / 250.0
        base_target_flux *= (0.4 + 1.2 * (0.5 + 0.5 * math.cos(2.0 * math.pi * phase)))

    target_x = center_pix + pm_dx_pix
    target_y = center_pix + pm_dy_pix

    y_idx, x_idx = np.ogrid[:npix, :npix]
    psf_sigma = 1.35
    target_psf = base_target_flux * np.exp(-((x_idx - target_x) ** 2 + (y_idx - target_y) ** 2) / (2.0 * psf_sigma ** 2))
    data += target_psf

    num_field_stars = int(rng.integers(3, 8))
    for _ in range(num_field_stars):
        sx = rng.uniform(4.0, npix - 5.0)
        sy = rng.uniform(4.0, npix - 5.0)
        s_flux = rng.uniform(0.1, 0.7)
        star = s_flux * np.exp(-((x_idx - sx) ** 2 + (y_idx - sy) ** 2) / (2.0 * psf_sigma ** 2))
        data += star

    header = w.to_header()
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
    header["TELESCOP"] = "SPHEREx-SIMULATOR"
    header["INSTRUME"] = "SPHEREx-LVF-SIM"
    header["CHANNEL"] = channel_index
    header["EPOCH_ID"] = epoch_id
    header["EXPTIME"] = 120.0
    # Mandatory Anti-Fabrication Provenance Header Keys
    header["PROVENAN"] = "SYNTHETIC_DEMO"
    header["ORIGIN"] = "SkyTrace Synthetic Cutout Generator"
    header["COMMENT"] = "SYNTHETIC DEMONSTRATION CUTOUT - NOT FLIGHT OBSERVATION"

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
        for y in range(h):
            for x in range(w):
                v = stretched[y, x]
                r = int(np.clip(255 * (v ** 1.6), 0, 255))
                g = int(np.clip(255 * (v ** 1.1), 0, 255))
                b = int(np.clip(255 * (0.15 + 0.85 * (v ** 0.8)), 0, 255))
                rgb[y, x] = [r, g, b]
    else:
        gray = (stretched * 255).astype(np.uint8)
        rgb[:, :, 0] = gray
        rgb[:, :, 1] = gray
        rgb[:, :, 2] = gray

    img = Image.fromarray(rgb, mode="RGB")
    upscaled = img.resize((w * 4, h * 4), Image.Resampling.BILINEAR)

    buf = io.BytesIO()
    upscaled.save(buf, format="PNG")
    return buf.getvalue()
