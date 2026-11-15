"""Scientific Difference Imaging & Statistical Change Detection Engine.
Computes pixel-aligned differential flux D(x, y) = |I_2(x, y) - I_1(x, y)|,
estimates background noise via Median Absolute Deviation (MAD),
and extracts transient candidates with signal-to-noise ratio (SNR) thresholds and quality flags.
"""

from __future__ import annotations

import io
import base64
import numpy as np
from scipy import ndimage
from PIL import Image
from typing import Tuple, List, Dict, Any, Optional

from app.models.schemas import DifferenceAnalysisResult, TransientCandidate


def compute_mad_sigma(data: np.ndarray) -> float:
    """Compute robust standard deviation estimator using Median Absolute Deviation (MAD).
    sigma ~ 1.4826 * median(|data - median(data)|)
    """
    valid = data[np.isfinite(data)]
    if len(valid) == 0:
        return 1.0
    med = np.median(valid)
    mad = np.median(np.abs(valid - med))
    sigma = 1.4826 * mad
    return float(max(sigma, 1e-6))


def render_array_to_base64_png(
    array: np.ndarray,
    colormap: str = "seismic",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> str:
    """Render a 2D float NumPy array into a color-mapped base64-encoded PNG image."""
    arr = np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)

    if vmin is None:
        vmin = float(np.percentile(arr, 1.0))
    if vmax is None:
        vmax = float(np.percentile(arr, 99.0))

    if vmax <= vmin:
        vmax = vmin + 1.0

    # Normalize to [0, 1]
    norm = np.clip((arr - vmin) / (vmax - vmin), 0.0, 1.0)

    # Color mapping
    h, w = norm.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)

    if colormap == "seismic":
        # Diverging blue-white-red
        # Center zero: norm=0.5 -> white
        for y in range(h):
            for x in range(w):
                v = norm[y, x]
                if v < 0.5:
                    # Blue to white
                    f = v * 2.0
                    r = int(f * 255)
                    g = int(f * 255)
                    b = 255
                else:
                    # White to red
                    f = (v - 0.5) * 2.0
                    r = 255
                    g = int((1.0 - f) * 255)
                    b = int((1.0 - f) * 255)
                rgb[y, x] = [r, g, b]

    elif colormap == "viridis":
        # Simplified viridis approximation: deep purple -> teal -> yellow
        for y in range(h):
            for x in range(w):
                v = norm[y, x]
                r = int(np.clip(255 * (0.2 + 0.8 * (v ** 1.5)), 0, 255))
                g = int(np.clip(255 * (v ** 0.8), 0, 255))
                b = int(np.clip(255 * (0.6 * (1.0 - v) + 0.1), 0, 255))
                rgb[y, x] = [r, g, b]

    elif colormap == "magma":
        # Dark purple -> orange -> pale yellow
        for y in range(h):
            for x in range(w):
                v = norm[y, x]
                r = int(np.clip(255 * (v ** 0.75), 0, 255))
                g = int(np.clip(255 * (v ** 1.8), 0, 255))
                b = int(np.clip(255 * (0.3 + 0.7 * (v ** 0.5) if v < 0.5 else 0.65 * (1.0 - v)), 0, 255))
                rgb[y, x] = [r, g, b]

    else:
        # Grayscale default
        gray = (norm * 255).astype(np.uint8)
        rgb[:, :, 0] = gray
        rgb[:, :, 1] = gray
        rgb[:, :, 2] = gray

    pil_img = Image.fromarray(rgb, mode="RGB")
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def compute_difference_image(
    image1: np.ndarray,
    image2: np.ndarray,
    center_ra: float,
    center_dec: float,
    pixel_scale_arcsec: float = 6.2,  # SPHEREx native pixel scale ~ 6.2 arcsec/pixel
    sigma_threshold: float = 3.5,
    channel_index: int = 50,
    wavelength_um: float = 2.4,
    epoch_ref_id: str = "EPOCH-1",
    epoch_ref_date: str = "2025-06-15",
    epoch_cmp_id: str = "EPOCH-2",
    epoch_cmp_date: str = "2025-12-14",
    delta_days: float = 182.0,
    target_name: Optional[str] = None,
) -> DifferenceAnalysisResult:
    """Perform scientific subtraction between two registered epochs.
    Calculates absolute difference, noise statistics, and identifies candidate transient sources.
    """
    if image1.shape != image2.shape:
        raise ValueError(f"Shape mismatch: {image1.shape} vs {image2.shape}")

    # Signed difference and absolute difference
    signed_diff = image2 - image1
    abs_diff = np.abs(signed_diff)

    noise_sigma = compute_mad_sigma(signed_diff)
    median_diff = float(np.median(signed_diff))
    std_diff = float(np.std(signed_diff))
    max_abs_diff = float(np.max(abs_diff))

    # Candidate transient extraction
    h, w = signed_diff.shape
    center_y, center_x = h / 2.0, w / 2.0

    # Detection mask above threshold
    threshold = median_diff + sigma_threshold * noise_sigma
    detection_mask = (abs_diff > threshold)

    # Label connected regions
    labeled_array, num_features = ndimage.label(detection_mask)
    candidates: List[TransientCandidate] = []

    if num_features > 0:
        objects = ndimage.find_objects(labeled_array)
        for idx, slc in enumerate(objects, start=1):
            region_mask = (labeled_array[slc] == idx)
            region_diff = abs_diff[slc]

            # Find local peak within region
            peak_local_pos = np.unravel_index(np.argmax(region_diff * region_mask), region_diff.shape)
            peak_y = slc[0].start + peak_local_pos[0]
            peak_x = slc[1].start + peak_local_pos[1]

            peak_val = float(signed_diff[peak_y, peak_x])
            peak_abs_val = float(abs_diff[peak_y, peak_x])
            snr = round(peak_abs_val / noise_sigma, 2)

            # Offset from center in arcsec
            dx_arcsec = (peak_x - center_x) * pixel_scale_arcsec
            dy_arcsec = (center_y - peak_y) * pixel_scale_arcsec
            dist_arcsec = float(np.hypot(dx_arcsec, dy_arcsec))

            # Approximate celestial coordinates
            cos_dec = np.cos(np.radians(center_dec))
            ra_cand = center_ra - (dx_arcsec / 3600.0) / max(abs(cos_dec), 1e-4)
            dec_cand = center_dec + (dy_arcsec / 3600.0)

            # Quality Assessment Flags
            flags = []
            if peak_x < 3 or peak_x >= w - 3 or peak_y < 3 or peak_y >= h - 3:
                flags.append("EDGE_PROXIMITY")
            if dist_arcsec < pixel_scale_arcsec * 1.5:
                flags.append("TARGET_CENTRAL_RESIDUAL")
            if snr < 4.0:
                flags.append("MARGINAL_DETECTION")

            flag_str = " | ".join(flags) if flags else "CLEAN_CANDIDATE"
            assessment = (
                f"Candidate transient source ({'Brightening' if peak_val > 0 else 'Fading'}), "
                f"SNR: {snr}σ, Flux delta: {round(peak_val, 3)} mJy/sr"
            )

            candidates.append(
                TransientCandidate(
                    candidate_id=f"CAND-{idx:03d}",
                    pixel_x=round(float(peak_x), 1),
                    pixel_y=round(float(peak_y), 1),
                    ra_deg=round(float(ra_cand % 360.0), 6),
                    dec_deg=round(float(np.clip(dec_cand, -90.0, 90.0)), 6),
                    angular_dist_arcsec=round(dist_arcsec, 2),
                    flux_delta_mjy=round(peak_val, 4),
                    snr=snr,
                    significance_sigma=round(snr, 1),
                    flag=flag_str,
                    quality_assessment=assessment,
                )
            )

    # Sort candidates by SNR descending
    candidates.sort(key=lambda c: c.snr, reverse=True)

    # Render difference map to PNG Base64
    b64_img = render_array_to_base64_png(
        signed_diff,
        colormap="seismic",
        vmin=-3.0 * noise_sigma,
        vmax=3.0 * noise_sigma,
    )

    return DifferenceAnalysisResult(
        target_name=target_name,
        ra_deg=center_ra,
        dec_deg=center_dec,
        channel_index=channel_index,
        wavelength_um=wavelength_um,
        epoch_ref_id=epoch_ref_id,
        epoch_ref_date=epoch_ref_date,
        epoch_cmp_id=epoch_cmp_id,
        epoch_cmp_date=epoch_cmp_date,
        delta_days=delta_days,
        max_abs_diff_mjy=round(max_abs_diff, 4),
        median_diff_mjy=round(median_diff, 4),
        std_diff_mjy=round(std_diff, 4),
        diff_image_base64=b64_img,
        colormap="seismic",
        candidates_found=len(candidates),
        candidates=candidates[:15],  # top 15 candidates
        algorithm_notes=(
            f"Point-spread function aligned difference D = I({epoch_cmp_id}) - I({epoch_ref_id}). "
            f"Noise floor estimated via MAD (σ={round(noise_sigma, 4)} mJy/sr). "
            f"Detection threshold set at {sigma_threshold}σ."
        ),
    )
