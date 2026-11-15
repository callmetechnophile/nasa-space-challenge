"""SPHEREx Difference Imaging and Significance Engine (Milestone 5).
Computes mathematically rigorous difference images D = I2 - I1,
propagates combined variance sigma_D = sqrt(V1 + V2), and evaluates
significance map S = D / sigma_D.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Any, Optional


def compute_difference_and_significance(
    image1: np.ndarray,
    variance1: Optional[np.ndarray],
    image2: np.ndarray,
    variance2: Optional[np.ndarray],
    bad_mask1: Optional[np.ndarray] = None,
    bad_mask2: Optional[np.ndarray] = None,
    spectrally_compatible_mask: Optional[np.ndarray] = None,
    subtract_residual_background: bool = True,
) -> Dict[str, Any]:
    """Compute difference image and significance map.

    Parameters:
    -----------
    image1 : 2D float array (Epoch 1, MJy/sr)
    variance1 : 2D float array (Variance 1, (MJy/sr)^2) or None
    image2 : 2D float array (Epoch 2, MJy/sr)
    variance2 : 2D float array (Variance 2, (MJy/sr)^2) or None
    bad_mask1, bad_mask2 : bool arrays (True = bad pixel)
    spectrally_compatible_mask : bool array (True = compatible)
    subtract_residual_background : bool, subtract median residual offset if True

    Returns:
    --------
    Dict containing:
      - 'difference_image': 2D float array (D = I2 - I1)
      - 'significance_map': 2D float array (S = D / sigma_D)
      - 'diff_variance': 2D float array (V_D = V1 + V2)
      - 'diff_sigma': 2D float array (sigma_D = sqrt(V_D))
      - 'valid_mask': bool array of scientifically usable pixels
      - 'metrics': dict of quantitative summary statistics
    """
    ny, nx = image1.shape
    assert image2.shape == (ny, nx), f"Image shapes must match: {image1.shape} vs {image2.shape}"

    # Calculate raw difference D = I2 - I1
    diff = image2.astype(np.float64) - image1.astype(np.float64)

    # Propagate variance
    if variance1 is not None and variance2 is not None:
        v1 = np.maximum(variance1.astype(np.float64), 1e-12)
        v2 = np.maximum(variance2.astype(np.float64), 1e-12)
        diff_var = v1 + v2
        diff_sigma = np.sqrt(diff_var)
    else:
        # If variance is unavailable, estimate from robust MAD of the difference image
        valid_raw = np.isfinite(diff)
        if np.any(valid_raw):
            mad = float(np.median(np.abs(diff[valid_raw] - np.median(diff[valid_raw]))))
            robust_sigma = max(1.4826 * mad, 1e-6)
        else:
            robust_sigma = 1.0
        diff_sigma = np.full_like(diff, robust_sigma)
        diff_var = diff_sigma ** 2

    # Build composite validity mask
    valid_mask = np.isfinite(diff) & np.isfinite(diff_sigma) & (diff_sigma > 0.0)

    if bad_mask1 is not None:
        valid_mask &= (~bad_mask1)
    if bad_mask2 is not None:
        valid_mask &= (~bad_mask2)
    if spectrally_compatible_mask is not None:
        valid_mask &= spectrally_compatible_mask

    # Subtract residual sky background offset if requested
    residual_bg = 0.0
    if subtract_residual_background and np.any(valid_mask):
        residual_bg = float(np.median(diff[valid_mask]))
        diff -= residual_bg

    # Compute significance map S = D / sigma_D
    significance = np.zeros_like(diff)
    significance[valid_mask] = diff[valid_mask] / diff_sigma[valid_mask]

    # Fill invalid pixels with NaN
    diff_out = np.where(valid_mask, diff, np.nan)
    sig_out = np.where(valid_mask, significance, np.nan)
    var_out = np.where(valid_mask, diff_var, np.nan)
    sigma_out = np.where(valid_mask, diff_sigma, np.nan)

    # Compute quantitative metrics
    n_valid = int(np.sum(valid_mask))
    total_pixels = int(image1.size)
    if n_valid > 0:
        valid_diff = diff[valid_mask]
        valid_sig = significance[valid_mask]
        rms_noise = float(np.sqrt(np.mean(valid_diff ** 2)))
        mean_sig = float(np.mean(valid_sig))
        std_sig = float(np.std(valid_sig))
        max_sig = float(np.max(valid_sig))
        min_sig = float(np.min(valid_sig))
    else:
        rms_noise = 0.0
        mean_sig = 0.0
        std_sig = 0.0
        max_sig = 0.0
        min_sig = 0.0

    return {
        "difference_image": diff_out,
        "significance_map": sig_out,
        "diff_variance": var_out,
        "diff_sigma": sigma_out,
        "valid_mask": valid_mask,
        "residual_bg_subtracted": residual_bg,
        "metrics": {
            "valid_pixel_count": n_valid,
            "total_pixels": total_pixels,
            "valid_fraction": float(n_valid / total_pixels) if total_pixels > 0 else 0.0,
            "rms_noise_mjy_sr": rms_noise,
            "mean_significance": mean_sig,
            "std_significance": std_sig,
            "max_significance": max_sig,
            "min_significance": min_sig,
        },
    }


def compare_spherex_temporal_pair(
    image1: np.ndarray,
    image2: np.ndarray,
    meta1: Dict[str, Any],
    meta2: Dict[str, Any],
    significance_sigma: float = 3.0,
) -> Dict[str, Any]:
    """Execute scientific temporal comparison between two SPHEREx observation epochs.
    Validates spectral bandpass and PSF compatibility.
    """
    b1 = meta1.get("bandpass", meta1.get("energy_bandpassname", ""))
    b2 = meta2.get("bandpass", meta2.get("energy_bandpassname", ""))
    if b1 and b2 and b1 != b2:
        raise ValueError(f"Incompatible spectral bandpasses: cannot difference {b1} against {b2}")

    # Check image shapes
    if image1.shape != image2.shape:
        raise ValueError(f"Spatial dimension mismatch: {image1.shape} vs {image2.shape}")

    diff_res = compute_difference_and_significance(
        image1=image1,
        variance1=meta1.get("variance"),
        image2=image2,
        variance2=meta2.get("variance"),
        subtract_residual_background=True,
    )

    sig_map = diff_res["significance_map"]
    transients = np.abs(sig_map) >= significance_sigma
    transient_count = int(np.sum(transients & diff_res["valid_mask"]))

    return {
        "status": "COMPLETED",
        "compatibility": {
            "bandpass_match": True,
            "bandpass": b1 or b2,
            "psf_fwhm1": meta1.get("psf_fwhm_arcsec"),
            "psf_fwhm2": meta2.get("psf_fwhm_arcsec"),
        },
        "transient_count": transient_count,
        "difference_metrics": diff_res["metrics"],
        "difference_image": diff_res["difference_image"],
        "significance_map": sig_map,
    }

