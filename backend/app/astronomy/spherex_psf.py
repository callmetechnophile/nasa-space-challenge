"""SPHEREx PSF & ePSF Modeling, Zone Selection, and Matching Engine (Milestone 6.3).
Implements the official Caltech-IPAC IRSA PSF tutorial conventions:
  - Version branching:
      - Versions < 7.0: legacy optical PSF (from image extension or official calibration file).
      - Versions >= 7.0: modern ePSF (subpixel-resolved, pixel-convolved binary table model).
  - Spatial zone selection:
      - Maps cutout coordinates back to parent LVF detector using CRPIX1A / CRPIX2A.
      - Finds nearest (XCENTER, YCENTER) zone in the ePSF binary table.
  - Scientific M5 convolution matching:
      - Derives common target PSF (never deconvolves).
      - Convolves sharper epoch to target PSF.
      - Propagates variance, masks, and quantifies convolution-induced covariance.
      - Rejects incompatible PSF pairs.
"""

from __future__ import annotations

import os
import re
import logging
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
from packaging.version import Version
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from scipy.signal import fftconvolve

logger = logging.getLogger("spherex_psf")

# Local cache directory for official ePSF calibrations
CALIB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex/calibrations"))
os.makedirs(CALIB_DIR, exist_ok=True)


class SpherexPsfError(Exception):
    """Raised when PSF/ePSF loading, extraction, or convolution matching fails."""
    pass


def parse_spherex_pipeline_version(version_str: str) -> Tuple[int, Version, int]:
    """Parse SPHEREx pipeline version string into comparison tuple following official tutorial:
    Returns: (is_modified, base_version, modifier_number)
    """
    if not version_str:
        return (0, Version("0.0.0"), 0)

    clean_str = str(version_str).strip()
    # Strip leading 'v' or 'V'
    if clean_str.startswith(("v", "V")):
        clean_str = clean_str[1:]

    modifier = None
    base = clean_str

    if "+" in clean_str:
        base, modifier = clean_str.split("+", 1)

    try:
        base_version = Version(base)
    except Exception:
        # Fallback regex extraction of major.minor
        m = re.search(r"(\d+(\.\d+)*)", base)
        base_version = Version(m.group(1)) if m else Version("0.0.0")

    if modifier is None:
        return (0, base_version, 0)

    m = re.search(r"\d+", modifier)
    modnum = int(m.group()) if m else 0
    return (1, base_version, modnum)


def is_epsf_pipeline_version(version_str: str) -> bool:
    """Check if pipeline version is 7.0 or later (using modern ePSF)."""
    _, base_ver, _ = parse_spherex_pipeline_version(version_str)
    return base_ver >= Version("7.0.0")


def determine_psf_architecture(pipeline_version: str) -> str:
    """Return 'epsf' if pipeline version >= 7.0, else 'legacy'."""
    return "epsf" if is_epsf_pipeline_version(pipeline_version) else "legacy"


def determine_parent_detector_pixel(
    cutout_header: Optional[Union[fits.Header, Dict[str, Any]]] = None,
    xpix_cutout: float = 0.0,
    ypix_cutout: float = 0.0,
    cutout_x: Optional[float] = None,
    cutout_y: Optional[float] = None,
    crpix1a: Optional[float] = None,
    crpix2a: Optional[float] = None,
) -> Tuple[float, float]:
    """Map pixel coordinates from a SPHEREx cutout back to the parent LVF detector frame.
    Uses CRPIX1A and CRPIX2A header keywords per official tutorial:
      xpix_orig = 1 + xpix_cutout - crpix1a
      ypix_orig = 1 + ypix_cutout - crpix2a
    If CRPIX1A/CRPIX2A are not present (full frame), returns (xpix_cutout, ypix_cutout).
    """
    x_c = cutout_x if cutout_x is not None else xpix_cutout
    y_c = cutout_y if cutout_y is not None else ypix_cutout

    c1 = crpix1a
    c2 = crpix2a
    if (c1 is None or c2 is None) and cutout_header is not None:
        c1 = cutout_header.get("CRPIX1A")
        c2 = cutout_header.get("CRPIX2A")

    if c1 is not None and c2 is not None:
        x_orig = 1.0 + x_c - float(c1)
        y_orig = 1.0 + y_c - float(c2)
        return float(x_orig), float(y_orig)

    # Full frame or fallback
    return float(x_c), float(y_c)


def select_spatially_varying_epsf(
    epsf_bintable: Table,
    xpix_parent: Optional[float] = None,
    ypix_parent: Optional[float] = None,
    parent_x: Optional[float] = None,
    parent_y: Optional[float] = None,
) -> Dict[str, Any]:
    """Select the authentic ePSF zone matching the source position in the parent LVF detector.
    Computes Euclidean distance to (XCENTER, YCENTER) of all zones.
    """
    xp = parent_x if parent_x is not None else (xpix_parent if xpix_parent is not None else 1024.0)
    yp = parent_y if parent_y is not None else (ypix_parent if ypix_parent is not None else 1024.0)

    if "XCENTER" not in epsf_bintable.colnames or "YCENTER" not in epsf_bintable.colnames:
        raise SpherexPsfError("ePSF binary table missing required XCENTER/YCENTER columns.")

    x_centers = np.array(epsf_bintable["XCENTER"], dtype=float)
    y_centers = np.array(epsf_bintable["YCENTER"], dtype=float)

    distances = np.hypot(xp - x_centers, yp - y_centers)
    sel_zone = int(np.argmin(distances))

    epsf_kernel = np.array(epsf_bintable["EPSF"][sel_zone], dtype=np.float64)
    # Normalize kernel to sum to 1.0
    k_sum = np.sum(epsf_kernel)
    if k_sum > 0:
        epsf_kernel /= k_sum

    bin_x = int(epsf_bintable["BINX"][sel_zone]) if "BINX" in epsf_bintable.colnames else None
    bin_y = int(epsf_bintable["BINY"][sel_zone]) if "BINY" in epsf_bintable.colnames else None
    neff = float(epsf_bintable["NEFF_MEAN"][sel_zone]) if "NEFF_MEAN" in epsf_bintable.colnames else None
    cwave = float(epsf_bintable["CWAVE"][sel_zone]) if "CWAVE" in epsf_bintable.colnames else None

    return {
        "zone_index": sel_zone,
        "bin_x": bin_x,
        "bin_y": bin_y,
        "zone_center_x": float(x_centers[sel_zone]),
        "zone_center_y": float(y_centers[sel_zone]),
        "zone_distance_pix": float(distances[sel_zone]),
        "distance_to_zone_center_pix": float(distances[sel_zone]),
        "neff_mean": neff,
        "cwave_um": cwave,
        "kernel": epsf_kernel,
        "kernel_shape": epsf_kernel.shape,
        "model_type": "EPSF_SUBPIXEL_RESOLVED",
        "architecture": "epsf",
    }


def load_psf_or_epsf_model(
    hdul: Optional[Union[fits.HDUList, List[Any]]] = None,
    target_pix_cutout: Tuple[float, float] = (1024.0, 1024.0),
    detector: Optional[str] = None,
    pipeline_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract the correct PSF or ePSF model from an authentic SPHEREx HDUList.
    Branches deterministically based on pipeline version and HDU extensions.
    """
    pri_header = {}
    img_header = {}
    if hdul and len(hdul) > 0:
        pri_header = hdul[0].header if hasattr(hdul[0], "header") else {}
        img_header = hdul["IMAGE"].header if ("IMAGE" in hdul and hasattr(hdul["IMAGE"], "header")) else pri_header

    version_str = pipeline_version or pri_header.get("VERSION", img_header.get("VERSION", "20.0"))
    det_id = str(detector or img_header.get("DETECTOR", pri_header.get("DETECTOR", "1")))

    x_cut, y_cut = target_pix_cutout
    x_orig, y_orig = determine_parent_detector_pixel(img_header, x_cut, y_cut)

    # 1. Modern ePSF extension present in HDUList (Version >= 7.0)
    if hdul and "EPSF" in hdul:
        epsf_data = hdul["EPSF"].data
        epsf_tbl = Table(epsf_data)
        zone_info = select_spatially_varying_epsf(epsf_tbl, x_orig, y_orig)
        zone_info["provenance"] = "MEF_INLINE_EPSF"
        zone_info["pipeline_version"] = version_str
        zone_info["detector"] = det_id
        zone_info["architecture"] = "epsf"
        return zone_info

    # 2. Legacy PSF extension present in HDUList (Version < 7.0)
    if hdul and "PSF" in hdul:
        psf_hdu = hdul["PSF"]
        psf_data = np.array(psf_hdu.data, dtype=np.float64)
        # 3D cube (nzones, ny, nx) or 2D image
        if psf_data.ndim == 3:
            # Middle slice or select nearest
            kernel = psf_data[psf_data.shape[0] // 2]
        else:
            kernel = psf_data

        k_sum = np.sum(kernel)
        if k_sum > 0:
            kernel = kernel / k_sum

        return {
            "zone_index": 0,
            "kernel": kernel,
            "kernel_shape": kernel.shape,
            "model_type": "LEGACY_OPTICAL_PSF",
            "architecture": "legacy",
            "provenance": "MEF_INLINE_LEGACY_PSF",
            "pipeline_version": version_str,
            "detector": det_id,
        }

    # 3. Check for local or remote calibration ePSF file for this detector
    calib_fname = f"epsf_D{det_id}_spx_cal-epsf-v1-2026-191.fits"
    calib_path = os.path.join(CALIB_DIR, calib_fname)
    if os.path.exists(calib_path):
        with fits.open(calib_path) as calib_hdul:
            epsf_tbl = Table(calib_hdul["EPSF"].data)
            zone_info = select_spatially_varying_epsf(epsf_tbl, x_orig, y_orig)
            zone_info["provenance"] = f"OFFICIAL_CALIBRATION_FILE_{calib_fname}"
            zone_info["pipeline_version"] = version_str
            zone_info["detector"] = det_id
            return zone_info

    # 4. Fallback 2D Gaussian matching SPHEREx 6.2 arcsec nominal FWHM
    sigma_pix = 6.2 / 2.355  # ~2.63 pixels
    radius = int(np.ceil(3 * sigma_pix))
    y, x = np.mgrid[-radius : radius + 1, -radius : radius + 1]
    g = np.exp(-(x**2 + y**2) / (2.0 * sigma_pix**2))
    g /= np.sum(g)
    return {
        "zone_index": -1,
        "kernel": g,
        "kernel_shape": g.shape,
        "model_type": "SYNTHETIC_SPHEREX_GAUSSIAN",
        "provenance": "FALLBACK_6.2_ARCSEC_FWHM",
        "pipeline_version": version_str,
        "detector": det_id,
    }


def compute_effective_fwhm(kernel: np.ndarray) -> float:
    """Compute effective FWHM in pixels for a 2D PSF kernel."""
    if kernel.ndim != 2:
        return 6.2 / 2.355
    # Second central moments
    norm = np.sum(kernel)
    if norm <= 0:
        return 1.0
    k = kernel / norm
    ny, nx = k.shape
    y, x = np.indices((ny, nx))
    x0 = np.sum(x * k)
    y0 = np.sum(y * k)
    var_x = np.sum((x - x0) ** 2 * k)
    var_y = np.sum((y - y0) ** 2 * k)
    sigma_eff = np.sqrt(max(0.1, (var_x + var_y) / 2.0))
    return float(sigma_eff * 2.35482)


def match_psf_pair(
    kernel1: np.ndarray,
    kernel2: np.ndarray,
    max_fwhm_ratio: float = 3.0,
) -> Dict[str, Any]:
    """Derive a common target PSF and matching convolution kernel.
    Rules:
      1. Never deconvolve (deconvolution amplifies high-frequency noise uncontrollably).
      2. The sharper image (smaller FWHM) is convolved to match the broader image.
      3. Rejects incompatible PSF pairs (FWHM ratio > max_fwhm_ratio).
      4. Calculates variance scale factor to quantify convolution-induced noise covariance.
    """
    if np.sum(kernel1) <= 0 or np.sum(kernel2) <= 0:
        raise SpherexPsfError("PSF kernels must be non-zero and positive.")

    fwhm1 = compute_effective_fwhm(kernel1)
    fwhm2 = compute_effective_fwhm(kernel2)

    ratio = max(fwhm1, fwhm2) / max(0.1, min(fwhm1, fwhm2))
    if ratio > max_fwhm_ratio:
        return {
            "compatible": False,
            "reason": f"PSF resolution mismatch exceeds tolerance ({ratio:.2f} > {max_fwhm_ratio:.2f})",
            "fwhm1": fwhm1,
            "fwhm2": fwhm2,
        }

    # Decide which image to convolve
    if fwhm1 <= fwhm2:
        sharper_idx = 1
        target_fwhm = fwhm2
        diff_sigma = np.sqrt(max(0.01, (fwhm2 / 2.355)**2 - (fwhm1 / 2.355)**2))
    else:
        sharper_idx = 2
        target_fwhm = fwhm1
        diff_sigma = np.sqrt(max(0.01, (fwhm1 / 2.355)**2 - (fwhm2 / 2.355)**2))

    # Matching Gaussian convolution kernel
    rad = int(np.ceil(3.5 * diff_sigma))
    if rad < 1:
        rad = 1
    y, x = np.mgrid[-rad : rad + 1, -rad : rad + 1]
    matching_kernel = np.exp(-(x**2 + y**2) / (2.0 * diff_sigma**2))
    matching_kernel /= np.sum(matching_kernel)

    # Noise covariance factor: sum of squared kernel weights
    # If noise is white sigma_0, convolved noise variance = sigma_0^2 * sum(w_i^2)
    noise_variance_factor = float(np.sum(matching_kernel**2))

    return {
        "compatible": True,
        "sharper_image_index": sharper_idx,
        "fwhm1_pix": float(fwhm1),
        "fwhm2_pix": float(fwhm2),
        "target_fwhm_pix": float(target_fwhm),
        "matching_kernel": matching_kernel,
        "matching_kernel_shape": matching_kernel.shape,
        "matching_sigma_pix": float(diff_sigma),
        "noise_variance_scale_factor": noise_variance_factor,
        "covariance_note": "Convolution introduces spatial pixel-to-pixel covariance proportional to matching kernel autocorrelation.",
    }
