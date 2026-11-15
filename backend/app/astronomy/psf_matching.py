"""SPHEREx Point Spread Function (PSF) Homogenization Engine (Milestone 5).
Computes common target PSF without deconvolution, convolves sharper epoch
with empirical matching kernel using quadrature formula sigma_kernel = sqrt(sigma_target^2 - sigma_native^2),
and rigorously propagates correlated variance.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Any, Tuple, Optional
from scipy.ndimage import gaussian_filter


def estimate_effective_fwhm(psf_data: Any) -> float:
    """Estimate effective FWHM in pixels from a 2D array, 3D cube, or FITS Table."""
    if psf_data is None:
        return 1.5

    # Check for FITS Table (FITS_rec or TableHDU with 'EPSF' column)
    if hasattr(psf_data, "names") or hasattr(psf_data, "columns"):
        try:
            col_name = "EPSF" if "EPSF" in psf_data.names else ("PSF" if "PSF" in psf_data.names else None)
            if col_name:
                mid_idx = len(psf_data) // 2
                p2d = psf_data[mid_idx][col_name]
            else:
                return 1.5
        except Exception:
            return 1.5
    elif isinstance(psf_data, np.ndarray):
        if psf_data.ndim == 3:
            mid_idx = psf_data.shape[0] // 2
            p2d = psf_data[mid_idx]
        elif psf_data.ndim == 2:
            p2d = psf_data
        else:
            return 1.5
    else:
        return 1.5

    p2d = np.asarray(p2d, dtype=np.float64)
    s = np.sum(p2d)
    if s > 0:
        p_norm = p2d / s
    else:
        return 1.5

    ny, nx = p_norm.shape
    yc, xc = (ny - 1) / 2.0, (nx - 1) / 2.0
    y_idx, x_idx = np.indices((ny, nx))

    r2 = (x_idx - xc) ** 2 + (y_idx - yc) ** 2
    var_r = np.sum(p_norm * r2)
    sigma = np.sqrt(max(var_r / 2.0, 0.25))
    fwhm = float(sigma * 2.35482)
    return max(fwhm, 1.0)


def match_psf_pair(
    image1: np.ndarray,
    variance1: Optional[np.ndarray],
    image2: np.ndarray,
    variance2: Optional[np.ndarray],
    fwhm1: float = 1.5,
    fwhm2: float = 1.5,
    target_fwhm: Optional[float] = None,
) -> Dict[str, Any]:
    """Match PSF between two epochs by convolving the sharper image to the target PSF.

    Parameters:
    -----------
    image1, image2 : 2D float arrays
    variance1, variance2 : 2D float arrays of variance or None
    fwhm1, fwhm2 : Effective FWHM in pixels of image 1 and image 2
    target_fwhm : Explicit target FWHM (if None, max(fwhm1, fwhm2) is used)

    Returns:
    --------
    Dict containing:
      - 'matched_image1': 2D array
      - 'matched_image2': 2D array
      - 'matched_variance1': 2D array or None
      - 'matched_variance2': 2D array or None
      - 'target_fwhm': float
      - 'convolved_epoch': 1, 2, 'both', or None (if already matched)
      - 'matching_sigma': float (in pixels)
    """
    sigma1 = fwhm1 / 2.35482
    sigma2 = fwhm2 / 2.35482

    if target_fwhm is None:
        target_fwhm = max(fwhm1, fwhm2)
    sigma_target = target_fwhm / 2.35482

    out_img1 = np.copy(image1)
    out_img2 = np.copy(image2)
    out_var1 = np.copy(variance1) if variance1 is not None else None
    out_var2 = np.copy(variance2) if variance2 is not None else None

    # Check if both images already match target FWHM within tolerance (0.05 pix)
    if abs(sigma1 - sigma_target) < 0.05 and abs(sigma2 - sigma_target) < 0.05:
        return {
            "matched_image1": out_img1,
            "matched_image2": out_img2,
            "matched_variance1": out_var1,
            "matched_variance2": out_var2,
            "target_fwhm": float(target_fwhm),
            "convolved_epoch": None,
            "matching_sigma": 0.0,
        }

    convolved_epoch = None
    matching_sigma = 0.0

    # Convolve image 1 if sharper than target
    if sigma1 < sigma_target - 0.02:
        sigma_m1 = np.sqrt(max(sigma_target ** 2 - sigma1 ** 2, 0.001))
        out_img1 = gaussian_filter(image1, sigma=sigma_m1, mode="reflect")
        convolved_epoch = 1
        matching_sigma = float(sigma_m1)

        if variance1 is not None:
            var_scale = 1.0 / (4.0 * np.pi * (sigma_m1 ** 2))
            out_var1 = gaussian_filter(variance1, sigma=sigma_m1 * np.sqrt(2.0), mode="reflect") * min(var_scale, 1.0)
            out_var1 = np.maximum(out_var1, variance1 * min(var_scale, 1.0))

    # Convolve image 2 if sharper than target
    if sigma2 < sigma_target - 0.02:
        sigma_m2 = np.sqrt(max(sigma_target ** 2 - sigma2 ** 2, 0.001))
        out_img2 = gaussian_filter(image2, sigma=sigma_m2, mode="reflect")
        convolved_epoch = 2 if convolved_epoch is None else "both"
        matching_sigma = float(sigma_m2) if matching_sigma == 0.0 else max(matching_sigma, float(sigma_m2))

        if variance2 is not None:
            var_scale = 1.0 / (4.0 * np.pi * (sigma_m2 ** 2))
            out_var2 = gaussian_filter(variance2, sigma=sigma_m2 * np.sqrt(2.0), mode="reflect") * min(var_scale, 1.0)
            out_var2 = np.maximum(out_var2, variance2 * min(var_scale, 1.0))

    return {
        "matched_image1": out_img1,
        "matched_image2": out_img2,
        "matched_variance1": out_var1,
        "matched_variance2": out_var2,
        "target_fwhm": float(target_fwhm),
        "convolved_epoch": convolved_epoch,
        "matching_sigma": float(matching_sigma),
    }
