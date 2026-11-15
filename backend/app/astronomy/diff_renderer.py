"""Diverging Scientific Difference and Significance Map PNG Renderers (Milestone 5).
Produces calibrated RGBA PNG textures for Three.js and Canvas difference overlays.
"""

from __future__ import annotations

import io
import base64
from typing import Optional
import numpy as np
from PIL import Image


def render_difference_png_bytes(
    diff_image: np.ndarray,
    vmax: Optional[float] = None,
    colormap: str = "diverging_bwr",
) -> bytes:
    """Render a difference image D = I2 - I1 to PNG with a diverging colormap.
    Negative values = Cyan/Blue (fading), Zero = Dark Grey, Positive = Red/Orange (brightening).
    Invalid/NaN pixels are 100% transparent.
    """
    valid = np.isfinite(diff_image)
    if vmax is None or vmax <= 0.0:
        if np.any(valid):
            vmax = float(np.percentile(np.abs(diff_image[valid]), 99.0))
            if vmax <= 0:
                vmax = 1.0
        else:
            vmax = 1.0

    # Symmetric scale: norm in [-1, 1]
    norm = np.clip(diff_image / vmax, -1.0, 1.0)
    norm_flipped = np.nan_to_num(np.flipud(norm), nan=0.0)
    valid_flipped = np.flipud(valid)

    h, w = norm_flipped.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    if colormap == "diverging_bwr":
        # Diverging blue-white-red / cyan-black-red
        # For x in [-1, 0]: blue/cyan to neutral dark
        # For x in [0, 1]: neutral dark to orange/red
        pos = np.clip(norm_flipped, 0.0, 1.0)
        neg = np.clip(-norm_flipped, 0.0, 1.0)

        # Base neutral gray (40, 40, 45) for near-zero valid pixels
        r = (neg * 30 + (1.0 - neg - pos) * 35 + pos * 240).astype(np.uint8)
        g = (neg * 140 + (1.0 - neg - pos) * 35 + pos * 60).astype(np.uint8)
        b = (neg * 255 + (1.0 - neg - pos) * 40 + pos * 40).astype(np.uint8)
        # Alpha: transparent outside valid, opaque where valid
        a = np.where(valid_flipped, 230, 0).astype(np.uint8)

    elif colormap == "diverging_gray":
        # Mid-gray is 0 (128, 128, 128)
        gray = np.clip(128.0 + norm_flipped * 127.0, 0, 255).astype(np.uint8)
        r = g = b = gray
        a = np.where(valid_flipped, 255, 0).astype(np.uint8)

    else:
        # Default grayscale
        gray = np.clip(128.0 + norm_flipped * 127.0, 0, 255).astype(np.uint8)
        r = g = b = gray
        a = np.where(valid_flipped, 255, 0).astype(np.uint8)

    rgba[:, :, 0] = r
    rgba[:, :, 1] = g
    rgba[:, :, 2] = b
    rgba[:, :, 3] = a

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_significance_png_bytes(
    significance_map: np.ndarray,
    threshold: float = 3.0,
    max_sigma: float = 8.0,
) -> bytes:
    """Render significance map S = D / sigma_D.
    Sub-threshold pixels (|S| < threshold) are transparent or dark.
    Significant positive excursions (S >= threshold) are bright orange/red.
    Significant negative excursions (S <= -threshold) are bright cyan/blue.
    """
    valid = np.isfinite(significance_map)
    sig_flipped = np.flipud(significance_map)
    valid_flipped = np.flipud(valid)

    h, w = sig_flipped.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Calculate absolute SNR above threshold
    abs_sig = np.abs(sig_flipped)
    is_significant = valid_flipped & (abs_sig >= threshold)
    intensity = np.clip((abs_sig - threshold) / max(max_sigma - threshold, 1.0), 0.0, 1.0)

    is_pos = is_significant & (sig_flipped > 0)
    is_neg = is_significant & (sig_flipped < 0)

    # Red/Orange for positive
    rgba[is_pos, 0] = np.clip(200 + intensity[is_pos] * 55, 0, 255).astype(np.uint8)
    rgba[is_pos, 1] = np.clip(60 + intensity[is_pos] * 120, 0, 255).astype(np.uint8)
    rgba[is_pos, 2] = 30
    rgba[is_pos, 3] = np.clip(180 + intensity[is_pos] * 75, 0, 255).astype(np.uint8)

    # Cyan/Blue for negative
    rgba[is_neg, 0] = 30
    rgba[is_neg, 1] = np.clip(140 + intensity[is_neg] * 100, 0, 255).astype(np.uint8)
    rgba[is_neg, 2] = np.clip(220 + intensity[is_neg] * 35, 0, 255).astype(np.uint8)
    rgba[is_neg, 3] = np.clip(180 + intensity[is_neg] * 75, 0, 255).astype(np.uint8)

    # Background valid pixels below threshold: very subtle neutral translucent overlay
    sub_thresh = valid_flipped & (~is_significant)
    rgba[sub_thresh, 0] = 20
    rgba[sub_thresh, 1] = 20
    rgba[sub_thresh, 2] = 25
    rgba[sub_thresh, 3] = 40  # low opacity background

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
