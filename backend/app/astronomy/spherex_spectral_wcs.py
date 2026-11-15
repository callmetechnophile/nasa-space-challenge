"""SPHEREx Dual WCS and Spectral Calibration Engine (Milestone 6.3).
Implements the official Caltech-IPAC IRSA tutorial convention for handling
spatial WCS (retaining SIP distortion) and alternate spectral WCS (key='W',
loaded with complete HDUList and disabling SIP only for the spectral WCS).
Extracts physical wavelength and bandwidth at arbitrary sky coordinates.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import astropy.units as u
from astropy.coordinates import SkyCoord

logger = logging.getLogger("spherex_spectral_wcs")


class SpherexSpectralWcsError(Exception):
    """Raised when spectral WCS extraction or evaluation fails."""
    pass


def load_dual_wcs_from_hdulist(
    hdul: fits.HDUList,
    image_extension: str = "IMAGE",
) -> Tuple[WCS, WCS]:
    """Load both the primary spatial WCS and the alternate spectral WCS from an authentic SPHEREx HDUList.
    Rules:
      1. Spatial WCS is loaded from image extension header with complete HDUList to resolve distortions.
         SIP distortion is explicitly preserved on the spatial WCS.
      2. Spectral WCS is loaded with key='W' and complete HDUList to resolve the WCS-WAVE lookup table.
      3. SIP distortion is explicitly disabled ONLY on the spectral WCS (spectral_wcs.sip = None),
         following the official Caltech-IPAC IRSA tutorial standard.
    """
    if image_extension not in hdul:
        raise SpherexSpectralWcsError(f"Extension '{image_extension}' not found in HDUList.")

    img_hdu = hdul[image_extension]
    header = img_hdu.header

    # 1. Primary spatial WCS (preserve SIP)
    try:
        spatial_wcs = WCS(header, fobj=hdul)
    except Exception as e:
        raise SpherexSpectralWcsError(f"Failed to load spatial WCS: {e}") from e

    # 2. Alternate spectral WCS (key='W', lookup table in WCS-WAVE)
    try:
        spectral_wcs = WCS(header=header, fobj=hdul, key="W")
        # Official tutorial requirement: disable SIP only for the spectral WCS
        spectral_wcs.sip = None
    except Exception as e:
        raise SpherexSpectralWcsError(f"Failed to load alternate spectral WCS (key='W'): {e}") from e

    return spatial_wcs, spectral_wcs


def compute_spectral_properties_at_sky_coord(
    hdul: fits.HDUList,
    sky_coord: SkyCoord,
    image_extension: str = "IMAGE",
) -> Dict[str, Any]:
    """Calculate the exact detector pixel, wavelength, and bandwidth at a given celestial coordinate.
    Evaluates wavelength response at the true sky position, not arbitrary detector coordinates.
    """
    spatial_wcs, spectral_wcs = load_dual_wcs_from_hdulist(hdul, image_extension=image_extension)

    # World to pixel conversion
    try:
        x_pix, y_pix = spatial_wcs.world_to_pixel(sky_coord)
    except Exception as e:
        raise SpherexSpectralWcsError(f"Failed to project sky coordinate to detector pixels: {e}") from e

    # Check detector boundary
    img_shape = hdul[image_extension].data.shape
    naxis2, naxis1 = img_shape
    in_bounds = (0.0 <= x_pix < naxis1) and (0.0 <= y_pix < naxis2)

    # Compute wavelength and bandwidth using spectral WCS
    wavelength_um = None
    bandwidth_um = None
    spectral_error = None

    if in_bounds:
        try:
            spectral_res = spectral_wcs.pixel_to_world(x_pix, y_pix)
            # Astropy spectral_wcs returns [wavelength, bandwidth] tuple
            if isinstance(spectral_res, (list, tuple)) and len(spectral_res) >= 2:
                w_coord, bw_qty = spectral_res[0], spectral_res[1]
                wavelength_um = float(w_coord.to(u.micrometer).value)
                bandwidth_um = float(bw_qty.to(u.micrometer).value)
            elif hasattr(spectral_res, "to"):
                wavelength_um = float(spectral_res.to(u.micrometer).value)
        except Exception as e:
            spectral_error = str(e)
            logger.warning("pixel_to_world failed on spectral WCS at (%.2f, %.2f): %s", x_pix, y_pix, e)

    # Read product metadata
    img_header = hdul[image_extension].header
    pri_header = hdul[0].header if len(hdul) > 0 else {}

    detector = img_header.get("DETECTOR", pri_header.get("DETECTOR", "UNKNOWN"))
    pipe_ver = pri_header.get("VERSION", img_header.get("VERSION", "UNKNOWN"))
    date_obs = pri_header.get("DATE-OBS", img_header.get("DATE-OBS", "UNKNOWN"))

    return {
        "detector": str(detector),
        "pixel_x": float(x_pix),
        "pixel_y": float(y_pix),
        "in_detector_bounds": bool(in_bounds),
        "detector_dimensions": (int(naxis1), int(naxis2)),
        "wavelength_um": wavelength_um,
        "bandwidth_um": bandwidth_um,
        "spectral_error": spectral_error,
        "pipeline_version": str(pipe_ver),
        "date_obs": str(date_obs),
        "spatial_wcs_type": str(spatial_wcs.wcs.ctype),
        "spatial_has_sip": bool(spatial_wcs.sip is not None),
        "spectral_wcs_type": str(spectral_wcs.wcs.ctype),
        "spectral_has_sip": bool(spectral_wcs.sip is not None),  # Should be False
        "wcs_provenance": "WCS-WAVE alternate key='W' (Caltech-IPAC IRSA standard)",
    }


def extract_spectral_properties(
    hdul: fits.HDUList,
    pixel_xy: Optional[Tuple[float, float]] = None,
    sky_coord: Optional[SkyCoord] = None,
    image_extension: str = "IMAGE",
) -> Dict[str, Any]:
    """Helper to extract physical wavelength and bandwidth at either a detector pixel or a sky coordinate."""
    spatial_wcs, spectral_wcs = load_dual_wcs_from_hdulist(hdul, image_extension=image_extension)
    if pixel_xy is not None:
        x_pix, y_pix = pixel_xy
    elif sky_coord is not None:
        x_pix, y_pix = spatial_wcs.world_to_pixel(sky_coord)
    else:
        # Default to center pixel
        shape = hdul[image_extension].data.shape
        x_pix, y_pix = shape[1] / 2.0, shape[0] / 2.0

    spectral_res = spectral_wcs.pixel_to_world(x_pix, y_pix)
    wavelength_um = None
    bandwidth_um = None
    if isinstance(spectral_res, (list, tuple)) and len(spectral_res) >= 2:
        wavelength_um = float(spectral_res[0].to(u.micrometer).value)
        bandwidth_um = float(spectral_res[1].to(u.micrometer).value)
    elif hasattr(spectral_res, "to"):
        wavelength_um = float(spectral_res.to(u.micrometer).value)

    return {
        "pixel_x": float(x_pix),
        "pixel_y": float(y_pix),
        "wavelength_um": wavelength_um,
        "bandwidth_um": bandwidth_um,
    }

