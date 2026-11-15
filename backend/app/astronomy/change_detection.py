"""SPHEREx Conservative Change Candidate Extraction Engine (Milestone 5).
Performs connected-component labeling on significance maps, measures centroids,
polarities, and flags candidates with the mandatory scientific disclaimer:
'CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED'.
"""

from __future__ import annotations

import numpy as np
from typing import List, Dict, Any, Optional
from scipy.ndimage import label, center_of_mass
from astropy.wcs import WCS

DISCLAIMER_LABEL = "CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED"


def extract_change_candidates(
    significance_map: np.ndarray,
    difference_image: np.ndarray,
    wcs: Optional[WCS] = None,
    significance_threshold: float = 3.5,
    min_area_pixels: int = 3,
    max_area_pixels: int = 2000,
) -> Dict[str, Any]:
    """Extract statistically significant change candidates from a significance map.

    Parameters:
    -----------
    significance_map : 2D float array (S = D / sigma_D)
    difference_image : 2D float array (D in MJy/sr)
    wcs : Optional Astropy WCS for pixel-to-world conversion
    significance_threshold : Critical SNR threshold (default 3.5)
    min_area_pixels : Minimum connected component size in pixels (default 3)
    max_area_pixels : Maximum connected component size in pixels (default 2000)

    Returns:
    --------
    Dict containing:
      - 'candidates': list of candidate dictionaries
      - 'candidate_count': int
      - 'labeled_mask': 2D int array of labeled components
      - 'threshold': float
      - 'disclaimer': str
    """
    valid_sig = np.isfinite(significance_map)
    # Detect both positive and negative excursions
    pos_mask = valid_sig & (significance_map >= significance_threshold)
    neg_mask = valid_sig & (significance_map <= -significance_threshold)

    # 8-connectivity structure
    structure = np.ones((3, 3), dtype=int)

    # Label positive and negative components separately
    pos_labeled, num_pos = label(pos_mask, structure=structure)
    neg_labeled, num_neg = label(neg_mask, structure=structure)

    candidates: List[Dict[str, Any]] = []
    output_mask = np.zeros_like(significance_map, dtype=int)
    cid_counter = 1

    def process_components(labeled_arr, count, polarity):
        nonlocal cid_counter
        for comp_id in range(1, count + 1):
            comp_pixels = (labeled_arr == comp_id)
            area = int(np.sum(comp_pixels))
            if area < min_area_pixels or area > max_area_pixels:
                continue

            # Centroid weighted by |S|
            weights = np.abs(significance_map[comp_pixels])
            y_indices, x_indices = np.where(comp_pixels)
            w_sum = np.sum(weights)
            if w_sum > 0:
                yc = float(np.sum(y_indices * weights) / w_sum)
                xc = float(np.sum(x_indices * weights) / w_sum)
            else:
                yc = float(np.mean(y_indices))
                xc = float(np.mean(x_indices))

            # Peak significance and peak flux
            peak_sig = float(np.max(significance_map[comp_pixels])) if polarity == "POSITIVE" else float(np.min(significance_map[comp_pixels]))
            peak_flux = float(np.max(difference_image[comp_pixels])) if polarity == "POSITIVE" else float(np.min(difference_image[comp_pixels]))
            integrated_flux = float(np.sum(difference_image[comp_pixels]))

            # World coordinates
            ra_deg, dec_deg = None, None
            if wcs is not None:
                try:
                    world = wcs.all_pix2world([[xc, yc]], 0)
                    ra_deg = float(world[0][0])
                    dec_deg = float(world[0][1])
                except Exception:
                    pass

            # Warning flags
            warnings = []
            ny, nx = significance_map.shape
            if xc < 15 or xc > nx - 16 or yc < 15 or yc > ny - 16:
                warnings.append("NEAR_IMAGE_BOUNDARY")
            if area > 100:
                warnings.append("EXTENDED_EMISSION")

            candidate = {
                "candidate_id": f"SPX-CAND-{cid_counter:04d}",
                "component_index": cid_counter,
                "pixel_x": round(xc, 2),
                "pixel_y": round(yc, 2),
                "ra_deg": round(ra_deg, 6) if ra_deg is not None else None,
                "dec_deg": round(dec_deg, 6) if dec_deg is not None else None,
                "polarity": polarity,
                "significance_peak": round(peak_sig, 3),
                "peak_flux_mjy_sr": round(peak_flux, 4),
                "integrated_flux_mjy_sr": round(integrated_flux, 4),
                "area_pixels": area,
                "warnings": warnings,
                "scientific_status": DISCLAIMER_LABEL,
            }
            candidates.append(candidate)
            output_mask[comp_pixels] = cid_counter
            cid_counter += 1

    process_components(pos_labeled, num_pos, "POSITIVE")
    process_components(neg_labeled, num_neg, "NEGATIVE")

    # Sort candidates by descending absolute peak significance
    candidates.sort(key=lambda c: abs(c["significance_peak"]), reverse=True)

    return {
        "candidates": candidates,
        "candidate_count": len(candidates),
        "labeled_mask": output_mask,
        "threshold": significance_threshold,
        "disclaimer": DISCLAIMER_LABEL,
    }
