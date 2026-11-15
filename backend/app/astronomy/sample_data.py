"""Sample Astronomical FITS Data Provider for SPHEREx 3D Sky Explorer.
Generates verified, calibrated demonstration FITS image products with Astropy WCS.
Strictly labeled as SYNTHETIC DEMONSTRATION DATA (not actual SPHEREx flight data).
"""

from __future__ import annotations

import io
import math
from typing import Dict, Any, List
import numpy as np

from astropy.io import fits
from astropy.wcs import WCS

from app.astronomy.fits_reader import read_fits_image, LoadedFitsProduct


def generate_synthetic_fits_fixture(
    ra_center: float,
    dec_center: float,
    width: int = 256,
    height: int = 256,
    pixel_scale_arcsec: float = 2.5,
    projection: str = "TAN",
    rotation_deg: float = 0.0,
    num_stars: int = 35,
    nebulosity: bool = True,
    target_name: str = "Synthetic Field",
    filter_band: str = "SPHEREx Band 3 (2.4 um)",
    seed: int = 42,
) -> bytes:
    """Generate a calibrated in-memory FITS file with Astropy-compliant WCS header."""
    rng = np.random.default_rng(seed)

    # 1. Base detector background + read noise
    # Realistic ADU baseline ~ 150.0 ADU with Poisson-like noise
    data = rng.normal(loc=150.0, scale=8.5, size=(height, width)).astype(np.float32)

    # 2. Add smooth diffuse nebulosity / dust emission
    if nebulosity:
        y_grid, x_grid = np.ogrid[:height, :width]
        cx, cy = width * 0.45, height * 0.55
        dist_sq = (x_grid - cx) ** 2 + 1.8 * (y_grid - cy) ** 2
        dust = 85.0 * np.exp(-dist_sq / (2.0 * (width * 0.22) ** 2))
        data += dust.astype(np.float32)

    # 3. Add central target source (e.g. brown dwarf / primary target)
    center_x = (width - 1) / 2.0
    center_y = (height - 1) / 2.0
    y_idx, x_idx = np.ogrid[:height, :width]

    # Gaussian PSF ~ 2.2 pixels FWHM
    sigma = 1.8
    target_psf = 450.0 * np.exp(-((x_idx - center_x) ** 2 + (y_idx - center_y) ** 2) / (2.0 * sigma ** 2))
    data += target_psf.astype(np.float32)

    # 4. Add random field stars with various magnitudes
    for _ in range(num_stars):
        sx = rng.uniform(8.0, width - 8.0)
        sy = rng.uniform(8.0, height - 8.0)
        peak = rng.uniform(40.0, 380.0)
        s_sigma = rng.uniform(1.2, 2.4)
        star_psf = peak * np.exp(-((x_idx - sx) ** 2 + (y_idx - sy) ** 2) / (2.0 * s_sigma ** 2))
        data += star_psf.astype(np.float32)

    # 5. Build standard Astropy WCS
    w = WCS(naxis=2)
    # FITS uses 1-based indexing for CRPIX
    w.wcs.crpix = [center_x + 1.0, center_y + 1.0]
    # Reference coordinates
    w.wcs.crval = [float(ra_center % 360.0), float(dec_center)]
    # Pixel scale in degrees/pixel
    scale_deg = pixel_scale_arcsec / 3600.0

    # Coordinate transformation matrix (CD matrix) with rotation
    rad = math.radians(rotation_deg)
    # Standard astronomical convention: RA increases to the left (-CDELT1)
    cd1_1 = -scale_deg * math.cos(rad)
    cd1_2 = scale_deg * math.sin(rad)
    cd2_1 = scale_deg * math.sin(rad)
    cd2_2 = scale_deg * math.cos(rad)

    w.wcs.cd = np.array([[cd1_1, cd1_2], [cd2_1, cd2_2]])
    w.wcs.ctype = [f"RA---{projection}", f"DEC--{projection}"]
    w.wcs.cunit = ["deg", "deg"]

    # 6. Build FITS Header (ensure strictly ASCII-compliant cards)
    ascii_target = target_name.encode("ascii", "replace").decode("ascii").replace("?", "deg")
    header = w.to_header()
    header["TELESCOP"] = "SPHEREx-Simulator"
    header["INSTRUME"] = "NIR-Spectrometer"
    header["OBJECT"] = ascii_target
    header["FILTER"] = filter_band
    header["BUNIT"] = "adu"
    header["EXPTIME"] = 120.0
    header["DATE-OBS"] = "2026-06-15T04:22:18.000"
    header["COMMENT"] = "SYNTHETIC DEMONSTRATION FITS PRODUCT - NOT ACTUAL OBSERVATION"
    header["PROVENAN"] = "DEMO-FIXTURE-M3"

    # 7. Write to in-memory bytes
    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


# Registry of built-in sample fixtures
SAMPLE_FIXTURES: Dict[str, Dict[str, Any]] = {
    "wise-0855": {
        "id": "wise-0855",
        "title": "WISE 0855 Field (Infrared Brown Dwarf Region)",
        "provenance": "SYNTHETIC DEMONSTRATION DATA (WCS-CALIBRATED)",
        "ra": 133.795129,
        "dec": -7.245147,
        "width": 256,
        "height": 256,
        "pixel_scale": 2.5,
        "projection": "TAN",
        "description": "Synthetic 2.4um infrared demonstration field around cold brown dwarf WISE 0855-0714 with calibrated TAN WCS projection.",
    },
    "equatorial-cal": {
        "id": "equatorial-cal",
        "title": "Equatorial Calibration Field (Vernal Equinox)",
        "provenance": "SYNTHETIC DEMONSTRATION DATA (WCS-CALIBRATED)",
        "ra": 0.0,
        "dec": 0.0,
        "width": 220,
        "height": 220,
        "pixel_scale": 3.0,
        "projection": "TAN",
        "description": "Synthetic demonstration field centered at RA 0°, Dec 0° for optical and coordinate grid alignment validation.",
    },
    "polar-demonstration": {
        "id": "polar-demonstration",
        "title": "North Celestial Polar Field (Dec +89.5°)",
        "provenance": "SYNTHETIC DEMONSTRATION DATA (WCS-CALIBRATED)",
        "ra": 0.0,
        "dec": 89.5,
        "width": 240,
        "height": 240,
        "pixel_scale": 4.0,
        "projection": "TAN",
        "description": "Synthetic demonstration field near the North Celestial Pole to verify high-declination spherical mesh curvature.",
    },
    "ra-wraparound": {
        "id": "ra-wraparound",
        "title": "RA Wraparound Field (RA 359.95°, Dec +12.0°)",
        "provenance": "SYNTHETIC DEMONSTRATION DATA (WCS-CALIBRATED)",
        "ra": 359.95,
        "dec": 12.0,
        "width": 256,
        "height": 256,
        "pixel_scale": 3.5,
        "projection": "TAN",
        "description": "Synthetic demonstration field crossing the 0°/360° Right Ascension meridian to verify continuous spherical projection.",
    },
}


def get_sample_fits(sample_id: str) -> LoadedFitsProduct:
    """Retrieve or generate a loaded sample FITS product by ID."""
    cfg = SAMPLE_FIXTURES.get(sample_id)
    if not cfg:
        valid_keys = ", ".join(SAMPLE_FIXTURES.keys())
        raise KeyError(f"Sample '{sample_id}' not found. Available samples: {valid_keys}")

    fits_bytes = generate_synthetic_fits_fixture(
        ra_center=cfg["ra"],
        dec_center=cfg["dec"],
        width=cfg["width"],
        height=cfg["height"],
        pixel_scale_arcsec=cfg["pixel_scale"],
        projection=cfg["projection"],
        target_name=cfg["title"],
    )

    return read_fits_image(fits_bytes, filename=f"{sample_id}.fits")
