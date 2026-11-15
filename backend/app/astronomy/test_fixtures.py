"""Scientific Test Fixture Generator for SPHEREx Milestone 3.
Generates 10 deterministic synthetic FITS fixtures using Astropy
with known reference coordinates, pixel scales, and projection matrices.
"""

from __future__ import annotations

import io
import math
from typing import Dict, Any, Tuple
import numpy as np

from astropy.io import fits
from astropy.wcs import WCS


def _create_synthetic_data(
    width: int,
    height: int,
    seed: int = 42,
    num_stars: int = 25,
    add_target: bool = True
) -> np.ndarray:
    """Generate realistic 2D float32 image array with background noise and stars."""
    rng = np.random.default_rng(seed)
    data = rng.normal(loc=120.0, scale=6.0, size=(height, width)).astype(np.float32)

    # Central target PSF
    if add_target:
        cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
        y_idx, x_idx = np.ogrid[:height, :width]
        psf = 500.0 * np.exp(-((x_idx - cx) ** 2 + (y_idx - cy) ** 2) / (2.0 * 2.0 ** 2))
        data += psf.astype(np.float32)

    # Random field stars
    y_idx, x_idx = np.ogrid[:height, :width]
    for _ in range(num_stars):
        sx = rng.uniform(10.0, width - 10.0)
        sy = rng.uniform(10.0, height - 10.0)
        flux = rng.uniform(50.0, 400.0)
        sigma = rng.uniform(1.2, 2.5)
        star = flux * np.exp(-((x_idx - sx) ** 2 + (y_idx - sy) ** 2) / (2.0 * sigma ** 2))
        data += star.astype(np.float32)

    return data


def create_fixture_1_standard_1024_tan() -> bytes:
    """1. Standard 1024 x 1024 TAN projection."""
    width, height = 1024, 1024
    data = _create_synthetic_data(width, height, seed=101, num_stars=60)

    w = WCS(naxis=2)
    w.wcs.crpix = [512.5, 512.5]
    w.wcs.crval = [180.0, 20.0]
    scale_deg = 1.0 / 3600.0  # 1.0 arcsec / pixel
    w.wcs.cdelt = [-scale_deg, scale_deg]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]

    header = w.to_header()
    header["TELESCOP"] = "SPHEREx-Simulator"
    header["INSTRUME"] = "NIR-Spectrometer"
    header["OBJECT"] = "Standard 1024x1024 Field"
    header["FILTER"] = "Band 1 (0.75-1.11um)"
    header["DATE-OBS"] = "2026-03-01T12:00:00"

    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_2_rotated_tan() -> bytes:
    """2. Rotated TAN projection (30.0 deg position angle East of North)."""
    width, height = 512, 512
    data = _create_synthetic_data(width, height, seed=102, num_stars=30)

    w = WCS(naxis=2)
    w.wcs.crpix = [256.5, 256.5]
    w.wcs.crval = [60.0, -15.0]
    scale_deg = 2.0 / 3600.0  # 2.0 arcsec/px
    rot_rad = math.radians(30.0)

    cd1_1 = -scale_deg * math.cos(rot_rad)
    cd1_2 = scale_deg * math.sin(rot_rad)
    cd2_1 = scale_deg * math.sin(rot_rad)
    cd2_2 = scale_deg * math.cos(rot_rad)

    w.wcs.cd = np.array([[cd1_1, cd1_2], [cd2_1, cd2_2]])
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]

    header = w.to_header()
    header["TELESCOP"] = "SPHEREx-Simulator"
    header["OBJECT"] = "Rotated TAN Field 30deg"
    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_3_nonsquare() -> bytes:
    """3. Non-square image (800 x 400)."""
    width, height = 800, 400
    data = _create_synthetic_data(width, height, seed=103, num_stars=35)

    w = WCS(naxis=2)
    w.wcs.crpix = [400.5, 200.5]
    w.wcs.crval = [45.0, 30.0]
    scale_deg = 1.5 / 3600.0  # 1.5 arcsec/px
    w.wcs.cdelt = [-scale_deg, scale_deg]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]

    header = w.to_header()
    header["TELESCOP"] = "SPHEREx-Simulator"
    header["OBJECT"] = "Non-Square Rectangular Field 800x400"
    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_4_negative_pixel_scale() -> bytes:
    """4. Negative pixel-scale image (explicit negative CDELT1 for East-left)."""
    width, height = 512, 512
    data = _create_synthetic_data(width, height, seed=104, num_stars=25)

    w = WCS(naxis=2)
    w.wcs.crpix = [256.5, 256.5]
    w.wcs.crval = [120.0, 10.0]
    scale_deg = 1.8 / 3600.0
    w.wcs.cdelt = [-scale_deg, scale_deg]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]

    header = w.to_header()
    header["OBJECT"] = "Negative Pixel Scale CDELT1"
    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_5_cd_matrix() -> bytes:
    """5. Image using CD matrix exclusively (45 deg rotation, 2.5 arcsec/px)."""
    width, height = 512, 512
    data = _create_synthetic_data(width, height, seed=105, num_stars=25)

    scale_deg = 2.5 / 3600.0
    rot_rad = math.radians(45.0)

    cd1_1 = -scale_deg * math.cos(rot_rad)
    cd1_2 = scale_deg * math.sin(rot_rad)
    cd2_1 = scale_deg * math.sin(rot_rad)
    cd2_2 = scale_deg * math.cos(rot_rad)

    header = fits.Header()
    header["SIMPLE"] = True
    header["BITPIX"] = -32
    header["NAXIS"] = 2
    header["NAXIS1"] = width
    header["NAXIS2"] = height
    header["CRPIX1"] = 256.5
    header["CRPIX2"] = 256.5
    header["CRVAL1"] = 210.0
    header["CRVAL2"] = -30.0
    header["CD1_1"] = cd1_1
    header["CD1_2"] = cd1_2
    header["CD2_1"] = cd2_1
    header["CD2_2"] = cd2_2
    header["CTYPE1"] = "RA---TAN"
    header["CTYPE2"] = "DEC--TAN"
    header["CUNIT1"] = "deg"
    header["CUNIT2"] = "deg"
    header["OBJECT"] = "CD Matrix Representation Field"

    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_6_pc_matrix() -> bytes:
    """6. Image using PC matrix with CDELT (15 deg rotation)."""
    width, height = 512, 512
    data = _create_synthetic_data(width, height, seed=106, num_stars=25)

    w = WCS(naxis=2)
    w.wcs.crpix = [256.5, 256.5]
    w.wcs.crval = [300.0, 45.0]
    scale_deg = 2.0 / 3600.0
    w.wcs.cdelt = [-scale_deg, scale_deg]

    rot_rad = math.radians(15.0)
    pc1_1 = math.cos(rot_rad)
    pc1_2 = -math.sin(rot_rad)
    pc2_1 = math.sin(rot_rad)
    pc2_2 = math.cos(rot_rad)

    w.wcs.pc = np.array([[pc1_1, pc1_2], [pc2_1, pc2_2]])
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]

    header = w.to_header()
    header["OBJECT"] = "PC Matrix Representation Field"
    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_7_ra_wraparound() -> bytes:
    """7. RA wraparound image near 359.99 deg."""
    width, height = 512, 512
    data = _create_synthetic_data(width, height, seed=107, num_stars=30)

    w = WCS(naxis=2)
    w.wcs.crpix = [256.5, 256.5]
    w.wcs.crval = [359.99, 0.0]
    scale_deg = 3.0 / 3600.0  # 3.0 arcsec/px
    w.wcs.cdelt = [-scale_deg, scale_deg]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]

    header = w.to_header()
    header["OBJECT"] = "RA Wraparound Meridian Field (359.99 deg)"
    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_8_invalid_wcs() -> bytes:
    """8. FITS file with invalid / non-celestial WCS."""
    width, height = 256, 256
    data = _create_synthetic_data(width, height, seed=108, num_stars=10)

    header = fits.Header()
    header["SIMPLE"] = True
    header["BITPIX"] = -32
    header["NAXIS"] = 2
    header["NAXIS1"] = width
    header["NAXIS2"] = height
    header["CTYPE1"] = "INVALID1"
    header["CTYPE2"] = "INVALID2"
    header["CRPIX1"] = 128.0
    header["CRPIX2"] = 128.0
    header["CRVAL1"] = 0.0
    header["CRVAL2"] = 0.0
    header["OBJECT"] = "Invalid WCS Fixture"

    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_9_no_wcs() -> bytes:
    """9. FITS file completely lacking WCS metadata cards."""
    width, height = 256, 256
    data = _create_synthetic_data(width, height, seed=109, num_stars=10)

    header = fits.Header()
    header["SIMPLE"] = True
    header["BITPIX"] = -32
    header["NAXIS"] = 2
    header["NAXIS1"] = width
    header["NAXIS2"] = height
    header["OBJECT"] = "No WCS Fixture"

    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


def create_fixture_10_nan_pixels() -> bytes:
    """10. FITS file containing NaN, +Inf, and -Inf pixel values."""
    width, height = 512, 512
    data = _create_synthetic_data(width, height, seed=110, num_stars=25)

    # Insert explicit NaNs and Infs
    data[100:110, 100:110] = np.nan
    data[200:205, 200:205] = np.inf
    data[300:305, 300:305] = -np.inf
    data[0, 0] = np.nan
    data[height - 1, width - 1] = np.inf

    w = WCS(naxis=2)
    w.wcs.crpix = [256.5, 256.5]
    w.wcs.crval = [75.0, -25.0]
    scale_deg = 2.0 / 3600.0
    w.wcs.cdelt = [-scale_deg, scale_deg]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cunit = ["deg", "deg"]

    header = w.to_header()
    header["OBJECT"] = "NaN and Inf Pixels Test Field"
    hdu = fits.PrimaryHDU(data=data, header=header)
    buf = io.BytesIO()
    hdu.writeto(buf)
    return buf.getvalue()


ALL_FIXTURE_GENERATORS = {
    "1_standard_1024_tan": create_fixture_1_standard_1024_tan,
    "2_rotated_tan": create_fixture_2_rotated_tan,
    "3_nonsquare": create_fixture_3_nonsquare,
    "4_negative_pixel_scale": create_fixture_4_negative_pixel_scale,
    "5_cd_matrix": create_fixture_5_cd_matrix,
    "6_pc_matrix": create_fixture_6_pc_matrix,
    "7_ra_wraparound": create_fixture_7_ra_wraparound,
    "8_invalid_wcs": create_fixture_8_invalid_wcs,
    "9_no_wcs": create_fixture_9_no_wcs,
    "10_nan_pixels": create_fixture_10_nan_pixels,
}
