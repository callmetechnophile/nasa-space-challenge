"""SPHEREx Common Celestial Grid Reprojection and Image Registration (Milestone 5).
Reprojects multi-epoch observations onto a common WCS tangent plane,
preserving surface brightness units (MJy/sr) and rigorously propagating variance
via analytical bilinear weight squaring: Var(I) = sum(w_i^2 * Var_i).
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Dict, Any, Optional
from astropy.wcs import WCS
from scipy.ndimage import map_coordinates


def create_common_wcs(
    ra_center: float,
    dec_center: float,
    pixel_scale_deg: float = 0.0017222,  # 6.2 arcsec per pixel
    npix_x: int = 512,
    npix_y: int = 512,
) -> WCS:
    """Create a standard TAN WCS for the common celestial target grid."""
    w = WCS(naxis=2)
    w.wcs.crpix = [npix_x / 2.0 + 0.5, npix_y / 2.0 + 0.5]
    w.wcs.cdelt = [-pixel_scale_deg, pixel_scale_deg]
    w.wcs.crval = [ra_center, dec_center]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    return w


def reproject_to_common_grid(
    image: np.ndarray,
    variance: Optional[np.ndarray],
    source_wcs: WCS,
    target_wcs: WCS,
    target_shape: Tuple[int, int] = (512, 512),
    order: int = 1,
) -> Dict[str, Any]:
    """Reproject an image and its variance map onto target_wcs.

    Parameters:
    -----------
    image : 2D float array (MJy/sr)
    variance : 2D float array (variance in (MJy/sr)^2) or None
    source_wcs : Astropy WCS for the source image
    target_wcs : Astropy WCS for the target grid
    target_shape : (height, width) of the target grid
    order : Interpolation order (1 = bilinear, 3 = cubic spline)

    Returns:
    --------
    Dict containing:
      - 'image': reprojected image on target grid (NaN outside valid footprint)
      - 'variance': reprojected variance map with rigorous noise propagation
      - 'source_x': 2D array of source X pixel coordinates (1-based)
      - 'source_y': 2D array of source Y pixel coordinates (1-based)
      - 'valid_mask': bool mask indicating pixels mapped from inside source image
      - 'ra': 2D array of celestial RA (deg)
      - 'dec': 2D array of celestial Dec (deg)
    """
    ny_tgt, nx_tgt = target_shape

    # Target pixel grid (0-based)
    y_tgt, x_tgt = np.mgrid[0:ny_tgt, 0:nx_tgt]
    # Convert to world coordinates (target_wcs uses 0-based origin=0)
    ra_tgt, dec_tgt = target_wcs.all_pix2world(x_tgt, y_tgt, 0)

    # Convert world coordinates to source pixel coordinates
    x_src, y_src = source_wcs.all_world2pix(ra_tgt, dec_tgt, 0)

    ny_src, nx_src = image.shape
    valid_mask = (
        np.isfinite(x_src)
        & np.isfinite(y_src)
        & (x_src >= 0.0)
        & (x_src <= nx_src - 1.0)
        & (y_src >= 0.0)
        & (y_src <= ny_src - 1.0)
    )

    coords = np.array([y_src, x_src])

    # Interpolate image surface brightness (MJy/sr preserved without flux alteration)
    reproj_image = map_coordinates(
        image, coords, order=order, mode="constant", cval=np.nan
    )
    reproj_image[~valid_mask] = np.nan

    # Rigorous analytical variance propagation for bilinear resampling (order=1)
    if variance is not None:
        if order == 1:
            # Var(sum w_i * I_i) = sum w_i^2 * Var(I_i) for independent noise
            x_safe = np.where(valid_mask, x_src, 0.0)
            y_safe = np.where(valid_mask, y_src, 0.0)

            x0 = np.floor(x_safe).astype(np.int64)
            x1 = np.clip(x0 + 1, 0, nx_src - 1)
            x0 = np.clip(x0, 0, nx_src - 1)

            y0 = np.floor(y_safe).astype(np.int64)
            y1 = np.clip(y0 + 1, 0, ny_src - 1)
            y0 = np.clip(y0, 0, ny_src - 1)

            wx = x_safe - np.floor(x_safe)
            wy = y_safe - np.floor(y_safe)

            w00 = (1.0 - wx) * (1.0 - wy)
            w10 = wx * (1.0 - wy)
            w01 = (1.0 - wx) * wy
            w11 = wx * wy

            v_arr = np.asarray(variance, dtype=np.float64)
            reproj_variance = (
                (w00 ** 2) * v_arr[y0, x0]
                + (w10 ** 2) * v_arr[y0, x1]
                + (w01 ** 2) * v_arr[y1, x0]
                + (w11 ** 2) * v_arr[y1, x1]
            )
            reproj_variance[~valid_mask] = np.nan
        else:
            reproj_variance = map_coordinates(
                variance, coords, order=order, mode="constant", cval=np.nan
            )
            reproj_variance[~valid_mask] = np.nan
    else:
        reproj_variance = None

    # Source 1-based pixel coordinates for WCS-WAVE lookup
    src_x_1based = np.where(valid_mask, x_src + 1.0, np.nan)
    src_y_1based = np.where(valid_mask, y_src + 1.0, np.nan)

    return {
        "image": reproj_image,
        "variance": reproj_variance,
        "source_x": src_x_1based,
        "source_y": src_y_1based,
        "valid_mask": valid_mask,
        "ra": ra_tgt,
        "dec": dec_tgt,
    }


def compute_registration_displacement(
    wcs1: WCS,
    wcs2: WCS,
    ra_eval: float,
    dec_eval: float,
) -> Dict[str, float]:
    """Compute the local pixel displacement vector (dx, dy) and angular separation
    between two WCS solutions at an evaluation point.
    """
    x1, y1 = wcs1.all_world2pix(ra_eval, dec_eval, 0)
    x2, y2 = wcs2.all_world2pix(ra_eval, dec_eval, 0)

    dx = float(x2 - x1)
    dy = float(y2 - y1)
    pix_offset = float(np.hypot(dx, dy))

    # Evaluate angular separation between the centers
    ra1_c, dec1_c = wcs1.wcs.crval
    ra2_c, dec2_c = wcs2.wcs.crval
    dra = np.radians(ra2_c - ra1_c) * np.cos(np.radians(0.5 * (dec1_c + dec2_c)))
    ddec = np.radians(dec2_c - dec1_c)
    ang_sep_arcsec = float(np.degrees(np.hypot(dra, ddec)) * 3600.0)

    return {
        "dx_pixels": dx,
        "dy_pixels": dy,
        "pixel_offset": pix_offset,
        "angular_separation_arcsec": ang_sep_arcsec,
    }
