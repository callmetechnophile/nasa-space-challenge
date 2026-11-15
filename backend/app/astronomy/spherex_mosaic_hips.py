"""SPHEREx Mosaic Tool & HiPS Cube Product Evaluation Engine (Milestone 6.3).
Documents the capabilities, specifications, and scientific boundaries of the
official NASA/IPAC IRSA Mosaic Tool and DR1 All-Sky HiPS Cube:
  - HiPS Cube: 102 spectral layers covering 0.75-5.00 um (Norder=5 HEALPix grid).
  - Mosaic Tool: Interactive wavelength-cube reprojection tool; no REST API exposed.
  - Scientific boundaries: Suitable for initial spatial/spectral visualization and
    navigation context, but NEVER as a substitute for individual time-stamped Level 2 epochs,
    nor for uncalibrated differencing against single-epoch observations.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("spherex_mosaic_hips")


class SpherexMosaicHiPSError(Exception):
    """Raised when mosaic or HiPS cube boundaries are violated."""
    pass


def evaluate_mosaic_differencing_compatibility(
    is_mosaic_reference: bool,
    has_validated_common_calibration: bool,
    has_pixel_covariance_model: bool,
) -> Dict[str, Any]:
    """Evaluate whether a mosaic or HiPS cube can be differenced against a single-epoch Level 2 observation.
    Official IRSA Constraint:
      Mosaics collect and reproject pixels from multiple visits at similar wavelengths.
      Differencing a mosaic against an individual Level 2 image introduces severe spatial
      covariance and flux-scale offsets unless a validated common calibration and uncertainty
      model is explicitly provided.
    """
    if is_mosaic_reference:
        if not (has_validated_common_calibration and has_pixel_covariance_model):
            return {
                "permitted": False,
                "verdict": "REJECTED",
                "reason": (
                    "Differencing a multi-visit mosaic against a single-epoch Level 2 image is prohibited "
                    "without an independently validated common calibration and pixel covariance model. "
                    "Mosaics must NOT be used as temporal time-series reference frames."
                ),
            }

    return {
        "permitted": True,
        "verdict": "PERMITTED",
        "reason": "Both reference and science frames are validated single-epoch Level 2 observations.",
    }


def get_dr1_hips_cube_specifications() -> Dict[str, Any]:
    """Return the official specifications and operational constraints for the SPHEREx DR1 HiPS Cube."""
    return {
        "product_name": "SPHEREx DR1 All-Sky HiPS Cube",
        "release": "Data Release 1 (DR1)",
        "spatial_scheme": "HEALPix (Hierarchical Equal Area isoLatitude Pixelization)",
        "healpix_order": 5,
        "total_spectral_layers": 102,
        "wavelength_range_um": (0.75, 5.00),
        "angular_resolution_arcsec": 6.2,
        "api_availability": {
            "hips_cube_tiles": True,
            "hips_cube_endpoint": "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/dr1/hips5_cube/",
            "interactive_mosaic_tool_api": False,  # Mosaic tool does not expose an API
        },
        "intended_use_cases": [
            "All-sky 3D visualization and broad navigation",
            "Target region spectral context across all 102 channels",
            "Spatial verification of diffuse astronomical structures (Milky Way, zodiacal light, nebulae)",
        ],
        "prohibited_use_cases": [
            "Do NOT use as time-domain observation epochs in the temporal player.",
            "Do NOT difference against Level 2 single exposures without full covariance modeling.",
            "Do NOT infer lightcurve variability from HiPS spectral slices.",
        ],
    }
