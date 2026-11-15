"""FITS Dimension and Image HDU Integrity Validation Module (Milestone 6.2.4).
Enforces deterministic product-aware IMAGE HDU selection and strict integer metadata validation.

Rules:
1. SPHEREx MEF products:
   - Require the named 'IMAGE' extension.
   - Fallback to auxiliary extensions ('VARIANCE', 'FLAGS', 'ZODI', 'PSF', 'EPSF', 'WCS-WAVE')
     is strictly prohibited and raises FitsDimensionValidationError.
2. Single-image FITS products:
   - A single 2D primary HDU is permitted.
   - Dimensions are validated against the actual array shape.
3. Ambiguous products:
   - Multiple ambiguous 2D image extensions without an explicit target HDU are rejected.
   - Structured error includes filename, HDU indices, names, and array shapes.
4. Strict Integer Dimension Validation:
   - NAXIS1 and NAXIS2 must be strictly positive integers (1 <= dim <= 2^31 - 1).
   - Booleans, non-integral floats (e.g. 1024.9), invalid numeric strings, zero, and negative values
     are strictly rejected.
   - data.shape must strictly match (NAXIS2, NAXIS1).
"""

from __future__ import annotations

import logging
from typing import Tuple, Any, Optional, List
import numpy as np
from astropy.io import fits

logger = logging.getLogger("fits_dimensions")

MAX_SUPPORTED_FITS_DIMENSION = 2147483647  # 2^31 - 1 (FITS standard 32-bit signed integer limit)


class FitsDimensionValidationError(ValueError):
    """Raised when FITS image dimensions or headers fail structural integrity checks."""
    pass


def validate_strict_dimension_value(val: Any, name: str, filename: str) -> int:
    """Validates that a dimension value is a strict, positive integer within supported bounds.

    Rejects:
      - Boolean values (bool is a subclass of int in Python).
      - Non-integral floating-point values (e.g. 1024.9).
      - Invalid numeric strings (e.g. "abc", "1024.9", "").
      - Zero or negative dimensions (<= 0).
      - Missing dimensions (None).
      - Values outside supported 32-bit integer bounds (> 2^31 - 1).

    Returns:
        int: Validated positive integer dimension.
    """
    if val is None:
        raise FitsDimensionValidationError(f"IMAGE HDU in {filename} is missing {name} in header")

    # 1. Reject booleans (in Python, isinstance(True, int) is True, so must check bool first)
    if isinstance(val, bool):
        raise FitsDimensionValidationError(
            f"IMAGE HDU in {filename} has boolean value for {name}: {val!r} (expected positive integer)"
        )

    # 2. Reject non-integral floating-point values
    if isinstance(val, (float, np.floating)):
        if not np.isfinite(val) or not float(val).is_integer():
            raise FitsDimensionValidationError(
                f"IMAGE HDU in {filename} has non-integral float value for {name}: {val!r} (expected positive integer)"
            )
        parsed = int(val)
    elif isinstance(val, str):
        val_str = val.strip()
        if not val_str:
            raise FitsDimensionValidationError(f"IMAGE HDU in {filename} has empty string for {name}")
        # If string contains decimal point, reject as non-integral string
        if "." in val_str:
            raise FitsDimensionValidationError(
                f"IMAGE HDU in {filename} has non-integral numeric string for {name}: {val!r}"
            )
        try:
            parsed = int(val_str)
        except (ValueError, TypeError) as err:
            raise FitsDimensionValidationError(
                f"IMAGE HDU in {filename} has invalid numeric string for {name}: {val!r} ({err})"
            )
    elif isinstance(val, (int, np.integer)):
        parsed = int(val)
    else:
        raise FitsDimensionValidationError(
            f"IMAGE HDU in {filename} has unsupported type for {name}: {type(val).__name__} ({val!r})"
        )

    # 3. Reject zero or negative dimensions
    if parsed <= 0:
        raise FitsDimensionValidationError(
            f"IMAGE HDU in {filename} has non-positive dimension {name}={parsed} (expected > 0)"
        )

    # 4. Enforce supported integer bounds (32-bit signed integer space)
    if parsed > MAX_SUPPORTED_FITS_DIMENSION:
        raise FitsDimensionValidationError(
            f"IMAGE HDU in {filename} dimension {name}={parsed} exceeds maximum supported bounds ({MAX_SUPPORTED_FITS_DIMENSION})"
        )

    return parsed


def extract_and_validate_fits_dimensions(
    hdul: fits.HDUList,
    filename: str = "<unknown>",
    target_hdu: Optional[str | int] = None,
) -> Tuple[int, int, fits.Header, Any]:
    """Inspects a FITS HDUList, identifies the scientific IMAGE HDU using deterministic
    product-aware policies, validates that NAXIS1 and NAXIS2 are strict positive integers,
    and asserts that the data array shape matches (NAXIS2, NAXIS1).

    Enforces:
    - SPHEREx MEF products strictly require the exact 'IMAGE' extension.
    - Caller input cannot override SPHEREx product semantics (e.g. target_hdu="VARIANCE" is rejected).
    - Auxiliary extensions ('VARIANCE', 'FLAGS', 'ZODI', 'PSF', 'EPSF', 'WCS-WAVE') can never be used
      as the science image under any call path.
    - Explicit target_hdu disambiguation is preserved for generic non-SPHEREx FITS.
    - Valid single-image PrimaryHDU is preserved.
    - Structured errors report product type, requested HDU, and available HDUs.

    Args:
        hdul: Open astropy fits.HDUList object.
        filename: Name of the FITS file (for structured error context).
        target_hdu: Explicitly requested HDU name or index (optional).

    Returns:
        Tuple of (naxis1, naxis2, image_header, image_hdu)

    Raises:
        FitsDimensionValidationError: If IMAGE HDU cannot be deterministically resolved,
                                     is an illegal auxiliary fallback, has invalid NAXIS
                                     dimensions, or data array shape does not match (NAXIS2, NAXIS1).
    """
    if len(hdul) == 0:
        raise FitsDimensionValidationError(f"FITS file {filename} is empty (0 HDUs)")

    auxiliary_names = {"VARIANCE", "FLAGS", "ZODI", "PSF", "EPSF", "WCS-WAVE"}
    present_aux = [h.name for h in hdul if (getattr(h, "name", None) or "").upper() in auxiliary_names]
    available_hdus = [getattr(h, "name", None) or f"HDU_{i}" for i, h in enumerate(hdul)]

    # 1. Product Identification
    # SPHEREx MEF product detection:
    # 1. Multi-extension FITS (len(hdul) > 1) with SPHEREx headers (TELESCOP or INSTRUME containing "SPHEREX"), OR
    # 2. Filename contains SPHEREx signatures ("SPHEREX" or "_SPX_"), OR
    # 3. Extension structure contains characteristic SPHEREx auxiliary suite (>= 2 SPHEREx auxiliary extensions)
    telescop = str(hdul[0].header.get("TELESCOP", "")).upper() if len(hdul) > 0 and hasattr(hdul[0], "header") else ""
    instrume = str(hdul[0].header.get("INSTRUME", "")).upper() if len(hdul) > 0 and hasattr(hdul[0], "header") else ""
    filename_upper = filename.upper()

    is_spherex_header = ("SPHEREX" in telescop) or ("SPHEREX" in instrume) or ("SPHEREX" in filename_upper) or ("_SPX_" in filename_upper)
    is_spherex_mef = (len(hdul) > 1) and (is_spherex_header or (len(present_aux) >= 2))

    # 2. Deterministic HDU Selection
    image_hdu = None

    if is_spherex_mef:
        # Check if caller requested an auxiliary extension (by name or index)
        requested_name = None
        if isinstance(target_hdu, str):
            requested_name = target_hdu.strip().upper()
        elif isinstance(target_hdu, int):
            if 0 <= target_hdu < len(hdul):
                requested_name = (getattr(hdul[target_hdu], "name", None) or "").upper()
            else:
                raise FitsDimensionValidationError(
                    f"SPHEREx MEF product {filename} has no HDU index {target_hdu} "
                    f"(valid range: 0..{len(hdul)-1}); available HDUs: {available_hdus}."
                )
        elif target_hdu is not None:
            raise FitsDimensionValidationError(
                f"Invalid target_hdu specification type {type(target_hdu).__name__}: {target_hdu!r}"
            )

        if requested_name in auxiliary_names:
            raise FitsDimensionValidationError(
                f"SPHEREx MEF product {filename}: attempting to use auxiliary extension {target_hdu!r} "
                f"as the science image is strictly prohibited. Requested HDU: {target_hdu!r}, available HDUs: {available_hdus}."
            )

        # SPHEREx MEF products strictly require the exact 'IMAGE' extension.
        if "IMAGE" not in hdul:
            found_str = ", ".join(present_aux) if present_aux else "none"
            raise FitsDimensionValidationError(
                f"SPHEREx MEF product {filename} is missing required 'IMAGE' extension "
                f"(requested_hdu={target_hdu!r}, available_hdus={available_hdus}); "
                f"fallback to auxiliary extensions ({found_str}) is strictly prohibited."
            )

        if target_hdu is not None and requested_name != "IMAGE":
            raise FitsDimensionValidationError(
                f"SPHEREx MEF product {filename} requires the exact 'IMAGE' extension as the science image "
                f"(requested_hdu={target_hdu!r}, available_hdus={available_hdus}). "
                "Overriding SPHEREx product semantics is strictly prohibited."
            )

        image_hdu = hdul["IMAGE"]

    else:
        # Non-SPHEREx Generic FITS product
        if target_hdu is not None:
            # Caller explicitly requested a specific HDU (by name or index).
            # Generic FITS products permit explicit selection of any valid extension,
            # including legitimate extensions named 'VARIANCE' or other custom names.
            if isinstance(target_hdu, str):
                if target_hdu not in hdul:
                    raise FitsDimensionValidationError(
                        f"Generic FITS file {filename} does not contain requested HDU {target_hdu!r}; available: {available_hdus}"
                    )
                image_hdu = hdul[target_hdu]
            elif isinstance(target_hdu, int):
                if target_hdu < 0 or target_hdu >= len(hdul):
                    raise FitsDimensionValidationError(
                        f"Generic FITS file {filename} has no HDU index {target_hdu} (valid range: 0..{len(hdul)-1}); available: {available_hdus}"
                    )
                image_hdu = hdul[target_hdu]
            else:
                raise FitsDimensionValidationError(
                    f"Invalid target_hdu specification type {type(target_hdu).__name__}: {target_hdu!r}"
                )
        else:
            # Search for 2D scientific image candidates
            candidates: List[Tuple[int, str, Any]] = []
            for idx, h in enumerate(hdul):
                if isinstance(h, (fits.ImageHDU, fits.PrimaryHDU)) and h.data is not None:
                    if getattr(h.data, "ndim", 0) == 2:
                        candidates.append((idx, h.name or f"HDU_{idx}", h))

            if len(candidates) == 0:
                raise FitsDimensionValidationError(
                    f"Generic FITS file {filename} contains no valid 2D scientific IMAGE HDU (available: {available_hdus})"
                )
            elif len(candidates) == 1:
                # Deterministic single-image candidate (e.g. single 2D primary or isolated 2D extension)
                image_hdu = candidates[0][2]
            else:
                # Multiple ambiguous 2D image extensions without explicit target_hdu
                cand_desc = [f"HDU {idx} ('{name}', shape {h.data.shape})" for idx, name, h in candidates]
                raise FitsDimensionValidationError(
                    f"Generic FITS file {filename} contains multiple ambiguous 2D image extensions [{'; '.join(cand_desc)}] "
                    f"without an explicit target HDU. Please specify target_hdu explicitly (available: {available_hdus})."
                )

    # 2. Extract and strictly validate NAXIS dimensions from header
    header = image_hdu.header

    naxis1_raw = header.get("NAXIS1")
    naxis2_raw = header.get("NAXIS2")

    naxis1 = validate_strict_dimension_value(naxis1_raw, "NAXIS1", filename)
    naxis2 = validate_strict_dimension_value(naxis2_raw, "NAXIS2", filename)

    # 3. Validate data array presence and shape
    if image_hdu.data is None:
        raise FitsDimensionValidationError(
            f"IMAGE HDU in {filename} contains no data array to validate dimensions against"
        )

    data = image_hdu.data
    if data.ndim != 2:
        raise FitsDimensionValidationError(
            f"IMAGE HDU data in {filename} has unsupported dimensionality: {data.ndim}D with shape {data.shape}, expected 2D"
        )

    expected_shape = (naxis2, naxis1)
    if data.shape != expected_shape:
        raise FitsDimensionValidationError(
            f"IMAGE HDU data shape {data.shape} does not match header dimensions (NAXIS2={naxis2}, NAXIS1={naxis1}) in {filename}"
        )

    return naxis1, naxis2, header, image_hdu
