"""Astronomical Image Renderer for SPHEREx 3D Sky Explorer.
Transforms scientific FITS 2D numerical arrays into display-stretched,
color-calibrated PNG textures for WebGL rendering.
Supports: Linear, Logarithmic, and Asinh (Lupton) stretches.
"""

from __future__ import annotations

import io
import base64
from typing import Optional, Literal
import numpy as np
from PIL import Image

DisplayStretch = Literal["linear", "log", "asinh", "sqrt"]


def apply_display_stretch(
    data: np.ndarray,
    stretch: DisplayStretch = "asinh",
    vmin_pct: float = 0.5,
    vmax_pct: float = 99.5,
    asinh_beta: float = 10.0,
    brightness: float = 1.0,
    contrast: float = 1.0,
) -> np.ndarray:
    """Apply non-destructive astronomical display stretches.
    Preserves original scientific FITS data while generating 8-bit normalized intensities.
    """
    clean = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)

    # Robust percentile bounds
    vmin = float(np.percentile(clean, vmin_pct))
    vmax = float(np.percentile(clean, vmax_pct))

    if vmax <= vmin:
        vmax = vmin + 1.0

    # Linear normalization into [0, 1]
    norm = np.clip((clean - vmin) / (vmax - vmin), 0.0, 1.0)

    # Display stretch
    if stretch == "asinh":
        # Lupton et al. (1999) astronomical asinh stretch
        stretched = np.arcsinh(norm * asinh_beta) / np.arcsinh(asinh_beta)
    elif stretch == "log":
        # Log stretch with offset to preserve low-level background
        stretched = np.log1p(norm * 9.0) / np.log(10.0)
    elif stretch == "sqrt":
        stretched = np.sqrt(norm)
    else:  # "linear"
        stretched = norm

    # Apply contrast and brightness adjustments
    if contrast != 1.0:
        stretched = np.clip((stretched - 0.5) * contrast + 0.5, 0.0, 1.0)

    if brightness != 1.0:
        stretched = np.clip(stretched * brightness, 0.0, 1.0)

    return np.clip(stretched, 0.0, 1.0)


def render_to_png_bytes(
    data: np.ndarray,
    stretch: DisplayStretch = "asinh",
    colormap: str = "astronomical_ir",
    vmin_pct: float = 0.5,
    vmax_pct: float = 99.5,
    brightness: float = 1.0,
    contrast: float = 1.0,
    invert: bool = False,
    nan_mask: Optional[np.ndarray] = None,
) -> bytes:
    """Render 2D float array to PNG image bytes with RGBA transparency.
    FITS image convention: row 0 is at bottom (FITS standard).
    Pillow image convention: row 0 is at top.
    We flip vertically so the WebGL texture maps (0,0) at bottom-left correctly.
    If nan_mask is provided (or if data contains NaNs), missing pixels are rendered
    with 100% transparency (Alpha = 0) preserving missing-data semantics.
    """
    if nan_mask is None and (np.isnan(data).any() or np.isinf(data).any()):
        nan_mask = np.isnan(data) | np.isinf(data)

    stretched = apply_display_stretch(
        data,
        stretch=stretch,
        vmin_pct=vmin_pct,
        vmax_pct=vmax_pct,
        brightness=brightness,
        contrast=contrast,
    )

    if invert:
        stretched = 1.0 - stretched

    # Invert vertically to align FITS (Y-up) with WebGL UV (V-up)
    stretched_flipped = np.flipud(stretched)

    h, w = stretched_flipped.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Scientific visualization palette:
    # High-contrast infrared representation (cyan / ice / violet accents on deep black)
    # Background (near 0) is semi-transparent, high-intensity regions are fully opaque
    if colormap == "astronomical_ir":
        # Multi-color astronomical IR mapping
        r = (stretched_flipped ** 1.8 * 220 + stretched_flipped * 35).astype(np.uint8)
        g = (stretched_flipped ** 1.3 * 230 + stretched_flipped * 25).astype(np.uint8)
        b = (stretched_flipped * 255).astype(np.uint8)
        # Alpha: background is visible but subtle (0.9 to 1.0 for faint structures, 1.0 for stars)
        a = (np.clip(stretched_flipped * 2.0 + 0.7, 0.0, 1.0) * 255).astype(np.uint8)

        rgba[:, :, 0] = r
        rgba[:, :, 1] = g
        rgba[:, :, 2] = b
        rgba[:, :, 3] = a
    elif colormap == "grayscale":
        gray = (stretched_flipped * 255.0).astype(np.uint8)
        rgba[:, :, 0] = gray
        rgba[:, :, 1] = gray
        rgba[:, :, 2] = gray
        rgba[:, :, 3] = 255
    else:  # Monochrome cyan
        intensity = (stretched_flipped * 255.0).astype(np.uint8)
        rgba[:, :, 0] = (intensity * 0.4).astype(np.uint8)
        rgba[:, :, 1] = (intensity * 0.85).astype(np.uint8)
        rgba[:, :, 2] = intensity
        rgba[:, :, 3] = 255

    # Preserve missing-data semantics using transparency (Alpha = 0)
    if nan_mask is not None and np.any(nan_mask):
        nan_flipped = np.flipud(nan_mask)
        rgba[nan_flipped, 3] = 0
        rgba[nan_flipped, :3] = 0

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_to_data_uri(
    data: np.ndarray,
    stretch: DisplayStretch = "asinh",
    colormap: str = "astronomical_ir",
    brightness: float = 1.0,
    contrast: float = 1.0,
    nan_mask: Optional[np.ndarray] = None,
) -> str:
    """Render to base64 Data URI for direct browser texture loading."""
    png_bytes = render_to_png_bytes(
        data,
        stretch=stretch,
        colormap=colormap,
        brightness=brightness,
        contrast=contrast,
        nan_mask=nan_mask,
    )
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"
