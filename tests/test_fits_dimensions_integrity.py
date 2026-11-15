"""Test suite for FITS Dimension Integrity and Metadata Validation (Milestone 6.2.4).

Adversarial unit test coverage:
1. Valid SPHEREx IMAGE HDU (real calibrated Level-2 SPHEREx product).
2. Missing IMAGE with valid 2D VARIANCE HDU (rejects auxiliary fallback).
3. Missing IMAGE with valid 2D PSF HDU (rejects auxiliary fallback).
4. Single-image primary HDU (permits single 2D primary image).
5. Multiple ambiguous image extensions (rejects without target_hdu; resolves with target_hdu).
6. Floating-point dimension (rejects 1024.9, "1024.9").
7. Boolean dimension (rejects True, False).
8. Invalid string dimension (rejects "abc", "1024.9", "").
9. Zero and negative dimensions (rejects 0, -50).
10. Header/data shape mismatch (rejects NAXIS != data.shape).

Additional integration & boundary coverage:
- Square 1024x1024 image.
- Rectangular non-square 800x400 image.
- Missing NAXIS metadata (None / omitted).
- Out-of-bounds integer dimensions (> 2^31 - 1).
- Discovery service dynamic footprint validation.
- Discovery service skipping corrupted FITS.
"""

from __future__ import annotations

import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

import pytest
import numpy as np
from astropy.io import fits

from app.astronomy.fits_dimensions import (
    extract_and_validate_fits_dimensions,
    validate_strict_dimension_value,
    FitsDimensionValidationError,
    MAX_SUPPORTED_FITS_DIMENSION,
)
from app.services.spherex_discovery import SpherexDiscoveryService


REAL_FITS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits")
)


# =============================================================================
# 1. Ten Adversarial Unit Tests (M6.2.4 Specific)
# =============================================================================

def test_fits_dimensions_1_valid_spherex_image_hdu():
    """1. Valid SPHEREx IMAGE HDU in real calibrated Level-2 FITS product."""
    assert os.path.exists(REAL_FITS_PATH), f"Real FITS file not found: {REAL_FITS_PATH}"
    with fits.open(REAL_FITS_PATH) as hdul:
        naxis1, naxis2, hdr, img_hdu = extract_and_validate_fits_dimensions(hdul, filename="level2_2025W44.fits")
        assert naxis1 == 2040
        assert naxis2 == 2040
        assert img_hdu.data.shape == (2040, 2040)
        assert hdr["BITPIX"] == -32
        assert img_hdu.name == "IMAGE"


def test_fits_dimensions_2_missing_image_with_valid_2d_variance():
    """2. Missing IMAGE with valid 2D VARIANCE HDU.
    Must reject and never fall back to VARIANCE.
    """
    prim = fits.PrimaryHDU()
    prim.header["TELESCOP"] = "SPHEREx"
    var_data = np.ones((2040, 2040), dtype=np.float32)
    var_hdu = fits.ImageHDU(data=var_data, name="VARIANCE")
    hdul = fits.HDUList([prim, var_hdu])

    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="spx_missing_image_has_variance.fits")
    
    err_msg = str(exc_info.value)
    assert "missing required 'IMAGE' extension" in err_msg
    assert "fallback to auxiliary extensions (VARIANCE) is strictly prohibited" in err_msg


def test_fits_dimensions_3_missing_image_with_valid_2d_psf():
    """3. Missing IMAGE with valid 2D PSF HDU.
    Must reject and never fall back to PSF.
    """
    prim = fits.PrimaryHDU()
    prim.header["TELESCOP"] = "SPHEREx"
    psf_data = np.ones((101, 101), dtype=np.float32)
    psf_hdu = fits.ImageHDU(data=psf_data, name="PSF")
    hdul = fits.HDUList([prim, psf_hdu])

    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="spx_missing_image_has_psf.fits")

    err_msg = str(exc_info.value)
    assert "missing required 'IMAGE' extension" in err_msg
    assert "fallback to auxiliary extensions (PSF) is strictly prohibited" in err_msg


def test_fits_dimensions_4_single_image_primary():
    """4. Single-image primary HDU.
    Must permit a valid 2D primary image and extract dimensions.
    """
    data = np.zeros((512, 1024), dtype=np.float32)
    prim = fits.PrimaryHDU(data=data)
    hdul = fits.HDUList([prim])

    naxis1, naxis2, hdr, resolved_hdu = extract_and_validate_fits_dimensions(hdul, filename="single_primary.fits")
    assert naxis1 == 1024
    assert naxis2 == 512
    assert resolved_hdu is prim
    assert resolved_hdu.data.shape == (512, 1024)


def test_fits_dimensions_5_multiple_ambiguous_image_extensions():
    """5. Multiple ambiguous image extensions.
    Must reject when target_hdu is not specified; must resolve when target_hdu is specified.
    """
    prim = fits.PrimaryHDU()
    sci1 = fits.ImageHDU(data=np.ones((200, 200), dtype=np.float32), name="CHANNEL_A")
    sci2 = fits.ImageHDU(data=np.ones((400, 400), dtype=np.float32), name="CHANNEL_B")
    hdul = fits.HDUList([prim, sci1, sci2])

    # Unambiguous caller must be rejected if no target_hdu is specified
    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="ambiguous_channels.fits")
    err_msg = str(exc_info.value)
    assert "contains multiple ambiguous 2D image extensions" in err_msg
    assert "CHANNEL_A" in err_msg
    assert "CHANNEL_B" in err_msg

    # Specifying target_hdu by name resolves unambiguously
    n1, n2, _, hdu1 = extract_and_validate_fits_dimensions(hdul, filename="ambiguous_channels.fits", target_hdu="CHANNEL_A")
    assert (n1, n2) == (200, 200)
    assert hdu1.name == "CHANNEL_A"

    n1_b, n2_b, _, hdu2 = extract_and_validate_fits_dimensions(hdul, filename="ambiguous_channels.fits", target_hdu="CHANNEL_B")
    assert (n1_b, n2_b) == (400, 400)
    assert hdu2.name == "CHANNEL_B"

    # Specifying target_hdu by index resolves unambiguously
    n1_idx, n2_idx, _, hdu_idx = extract_and_validate_fits_dimensions(hdul, filename="ambiguous_channels.fits", target_hdu=1)
    assert (n1_idx, n2_idx) == (200, 200)
    assert hdu_idx is sci1


def test_fits_dimensions_6_floating_point_dimension():
    """6. Floating-point dimension (e.g. 1024.9).
    Must strictly reject non-integral float values and decimal strings.
    """
    with pytest.raises(FitsDimensionValidationError) as exc_float:
        validate_strict_dimension_value(1024.9, "NAXIS1", "float_dim.fits")
    assert "has non-integral float value for NAXIS1: 1024.9" in str(exc_float.value)

    with pytest.raises(FitsDimensionValidationError) as exc_float_str:
        validate_strict_dimension_value("1024.9", "NAXIS2", "float_str_dim.fits")
    assert "has non-integral numeric string for NAXIS2: '1024.9'" in str(exc_float_str.value)


def test_fits_dimensions_7_boolean_dimension():
    """7. Boolean dimension (True / False).
    In Python, bool is a subclass of int (isinstance(True, int) == True).
    Must explicitly reject boolean values without converting them to 1 or 0.
    """
    with pytest.raises(FitsDimensionValidationError) as exc_true:
        validate_strict_dimension_value(True, "NAXIS1", "bool_dim.fits")
    assert "has boolean value for NAXIS1: True" in str(exc_true.value)

    with pytest.raises(FitsDimensionValidationError) as exc_false:
        validate_strict_dimension_value(False, "NAXIS2", "bool_dim.fits")
    assert "has boolean value for NAXIS2: False" in str(exc_false.value)


def test_fits_dimensions_8_invalid_string_dimension():
    """8. Invalid string dimension ("abc", "1024.9", "").
    Must reject non-numeric strings, empty strings, and malformed strings.
    """
    with pytest.raises(FitsDimensionValidationError) as exc_abc:
        validate_strict_dimension_value("abc", "NAXIS1", "abc_dim.fits")
    assert "has invalid numeric string for NAXIS1: 'abc'" in str(exc_abc.value)

    with pytest.raises(FitsDimensionValidationError) as exc_empty:
        validate_strict_dimension_value("", "NAXIS1", "empty_dim.fits")
    assert "has empty string for NAXIS1" in str(exc_empty.value)

    with pytest.raises(FitsDimensionValidationError) as exc_whitespace:
        validate_strict_dimension_value("   ", "NAXIS2", "whitespace_dim.fits")
    assert "has empty string for NAXIS2" in str(exc_whitespace.value)


def test_fits_dimensions_9_zero_and_negative_dimensions():
    """9. Zero and negative dimensions (0, -50).
    Must strictly reject dimensions <= 0.
    """
    with pytest.raises(FitsDimensionValidationError) as exc_zero:
        validate_strict_dimension_value(0, "NAXIS1", "zero_dim.fits")
    assert "has non-positive dimension NAXIS1=0" in str(exc_zero.value)

    with pytest.raises(FitsDimensionValidationError) as exc_neg:
        validate_strict_dimension_value(-50, "NAXIS2", "neg_dim.fits")
    assert "has non-positive dimension NAXIS2=-50" in str(exc_neg.value)


def test_fits_dimensions_10_header_data_shape_mismatch():
    """10. Header/data shape mismatch.
    When header states (1024, 1024) but array is (300, 500), must raise error.
    """
    data = np.zeros((300, 500), dtype=np.float32)
    hdu = fits.PrimaryHDU(data=data)
    hdu.header["NAXIS1"] = 1024
    hdu.header["NAXIS2"] = 1024
    hdul = fits.HDUList([hdu])

    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="mismatch.fits")
    assert "IMAGE HDU data shape (300, 500) does not match header dimensions (NAXIS2=1024, NAXIS1=1024)" in str(exc_info.value)


# =============================================================================
# Additional Edge Cases & Boundaries
# =============================================================================

def test_fits_dimensions_missing_naxis_metadata():
    """Verify missing NAXIS1 or NAXIS2 in header raises FitsDimensionValidationError."""
    data = np.zeros((200, 200), dtype=np.float32)
    hdu = fits.PrimaryHDU(data=data)
    del hdu.header["NAXIS1"]
    hdul = fits.HDUList([hdu])

    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="missing_naxis1.fits")
    assert "is missing NAXIS1 in header" in str(exc_info.value)

    hdu.header["NAXIS1"] = 200
    del hdu.header["NAXIS2"]
    with pytest.raises(FitsDimensionValidationError) as exc_info2:
        extract_and_validate_fits_dimensions(hdul, filename="missing_naxis2.fits")
    assert "is missing NAXIS2 in header" in str(exc_info2.value)


def test_fits_dimensions_exceeds_max_supported_bounds():
    """Verify dimension exceeding signed 32-bit limit (> 2^31 - 1) is rejected."""
    huge_val = MAX_SUPPORTED_FITS_DIMENSION + 1
    with pytest.raises(FitsDimensionValidationError) as exc_info:
        validate_strict_dimension_value(huge_val, "NAXIS1", "huge_dim.fits")
    assert "exceeds maximum supported bounds" in str(exc_info.value)


def test_fits_dimensions_valid_string_integer():
    """Verify valid numeric string representing an integer (e.g. '2040') is parsed safely."""
    val = validate_strict_dimension_value("2040", "NAXIS1", "str_int.fits")
    assert val == 2040
    assert isinstance(val, int)


def test_fits_dimensions_1024x1024_square():
    """Verify standard square 1024x1024 image dimensions are correctly derived."""
    data = np.zeros((1024, 1024), dtype=np.float32)
    hdu = fits.PrimaryHDU(data=data)
    hdul = fits.HDUList([hdu])

    naxis1, naxis2, hdr, resolved_hdu = extract_and_validate_fits_dimensions(hdul, filename="test_1024.fits")
    assert naxis1 == 1024
    assert naxis2 == 1024
    assert resolved_hdu.data.shape == (1024, 1024)


def test_fits_dimensions_800x400_non_square():
    """Verify rectangular non-square dimensions (NAXIS1=800, NAXIS2=400) are correctly validated."""
    data = np.ones((400, 800), dtype=np.float32)
    prim = fits.PrimaryHDU()
    img = fits.ImageHDU(data=data, name="IMAGE")
    hdul = fits.HDUList([prim, img])

    naxis1, naxis2, hdr, resolved_hdu = extract_and_validate_fits_dimensions(hdul, filename="test_800x400.fits")
    assert naxis1 == 800
    assert naxis2 == 400
    assert resolved_hdu.data.shape == (400, 800)


def test_fits_dimensions_missing_image_hdu_no_candidates():
    """Verify an HDUList with no valid 2D IMAGE HDU raises FitsDimensionValidationError."""
    prim = fits.PrimaryHDU()
    col = fits.Column(name="flux", format="1E", array=np.array([1.0, 2.0]))
    tbl = fits.BinTableHDU.from_columns([col], name="TABLE")
    hdul = fits.HDUList([prim, tbl])

    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="table_only.fits")
    assert "contains no valid 2D scientific IMAGE HDU" in str(exc_info.value)


def test_discovery_service_uses_dynamic_dimensions_without_fallback(tmp_path):
    """Verify SpherexDiscoveryService dynamically uses actual FITS dimensions (e.g. 800x400)
    and does not fall back to 2040 or 2048.
    """
    width = 800
    height = 400
    data = np.ones((height, width), dtype=np.float32)

    hdr = fits.Header()
    hdr["NAXIS1"] = width
    hdr["NAXIS2"] = height
    hdr["CTYPE1"] = "RA---TAN"
    hdr["CTYPE2"] = "DEC--TAN"
    hdr["CRVAL1"] = 50.0
    hdr["CRVAL2"] = 10.0
    hdr["CRPIX1"] = 400.0
    hdr["CRPIX2"] = 200.0
    hdr["CDELT1"] = -0.001
    hdr["CDELT2"] = 0.001

    prim = fits.PrimaryHDU(header=hdr, data=data)
    fits_file = tmp_path / "custom_800x400.fits"
    prim.writeto(fits_file)

    service = SpherexDiscoveryService(data_dir=str(tmp_path))

    obs = service.discover_local_observations(ra=50.0, dec=10.0)
    assert len(obs) == 1
    assert obs[0]["file_name"] == "custom_800x400.fits"

    obs_out = service.discover_local_observations(ra=65.0, dec=25.0)
    assert len(obs_out) == 0


def test_discovery_service_skips_malformed_dimensions_cleanly(tmp_path):
    """Verify SpherexDiscoveryService skips corrupted FITS files with dimension mismatch
    without crashing or returning false detections.
    """
    data = np.ones((100, 100), dtype=np.float32)
    hdr = fits.Header()
    hdr["NAXIS1"] = 1000
    hdr["NAXIS2"] = 1000
    hdr["CRVAL1"] = 50.0
    hdr["CRVAL2"] = 10.0

    prim = fits.PrimaryHDU(header=hdr, data=data)
    fits_file = tmp_path / "corrupt_dims.fits"
    prim.writeto(fits_file)

    service = SpherexDiscoveryService(data_dir=str(tmp_path))
    obs = service.discover_local_observations(ra=50.0, dec=10.0)
    assert len(obs) == 0


# =============================================================================
# 4. Seven M6.2.5 Selector & Call-Path Enforcement Tests
# =============================================================================

def test_m6_2_5_1_spherex_mef_with_valid_image():
    """1. SPHEREx MEF with valid IMAGE extension (default call path)."""
    assert os.path.exists(REAL_FITS_PATH), f"Real FITS file not found: {REAL_FITS_PATH}"
    with fits.open(REAL_FITS_PATH) as hdul:
        n1, n2, hdr, img_hdu = extract_and_validate_fits_dimensions(hdul, filename="level2_2025W44.fits", target_hdu=None)
        assert n1 == 2040
        assert n2 == 2040
        assert img_hdu.name == "IMAGE"
        assert img_hdu.data.shape == (2040, 2040)


def test_m6_2_5_2_spherex_mef_missing_image_explicit_target_variance():
    """2. SPHEREx MEF missing IMAGE, with explicit target_hdu="VARIANCE".
    Must reject and never allow caller to use auxiliary VARIANCE as science image.
    """
    prim = fits.PrimaryHDU()
    prim.header["TELESCOP"] = "SPHEREx"
    var_hdu = fits.ImageHDU(data=np.ones((2040, 2040), dtype=np.float32), name="VARIANCE")
    hdul = fits.HDUList([prim, var_hdu])

    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="spx_missing_image.fits", target_hdu="VARIANCE")

    err = str(exc_info.value)
    assert "attempting to use auxiliary extension 'VARIANCE' as the science image is strictly prohibited" in err
    assert "VARIANCE" in err


def test_m6_2_5_3_spherex_mef_missing_image_explicit_target_psf():
    """3. SPHEREx MEF missing IMAGE, with explicit target_hdu="PSF".
    Must reject and never allow caller to use auxiliary PSF as science image.
    """
    prim = fits.PrimaryHDU()
    prim.header["TELESCOP"] = "SPHEREx"
    psf_hdu = fits.ImageHDU(data=np.ones((101, 101), dtype=np.float32), name="PSF")
    hdul = fits.HDUList([prim, psf_hdu])

    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="spx_missing_image_psf.fits", target_hdu="PSF")

    err = str(exc_info.value)
    assert "attempting to use auxiliary extension 'PSF' as the science image is strictly prohibited" in err
    assert "PSF" in err


def test_m6_2_5_4_spherex_mef_with_image_explicit_target_image():
    """4. SPHEREx MEF with IMAGE and explicit target_hdu="IMAGE".
    Must resolve IMAGE cleanly.
    Also verifies that calling target_hdu="VARIANCE" on this valid MEF is rejected.
    """
    prim = fits.PrimaryHDU()
    prim.header["TELESCOP"] = "SPHEREx"
    img_hdu = fits.ImageHDU(data=np.ones((2040, 2040), dtype=np.float32), name="IMAGE")
    var_hdu = fits.ImageHDU(data=np.ones((2040, 2040), dtype=np.float32), name="VARIANCE")
    hdul = fits.HDUList([prim, img_hdu, var_hdu])

    # Explicit target_hdu="IMAGE" succeeds
    n1, n2, _, resolved = extract_and_validate_fits_dimensions(hdul, filename="spx_valid.fits", target_hdu="IMAGE")
    assert (n1, n2) == (2040, 2040)
    assert resolved.name == "IMAGE"

    # Explicit target_hdu="VARIANCE" is strictly rejected even though VARIANCE exists in the file
    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="spx_valid.fits", target_hdu="VARIANCE")
    assert "attempting to use auxiliary extension 'VARIANCE' as the science image is strictly prohibited" in str(exc_info.value)


def test_m6_2_5_5_generic_multi_image_explicit_disambiguation():
    """5. Generic multi-image FITS with explicit disambiguation."""
    prim = fits.PrimaryHDU()
    ch_a = fits.ImageHDU(data=np.ones((200, 200), dtype=np.float32), name="CHANNEL_A")
    ch_b = fits.ImageHDU(data=np.ones((400, 400), dtype=np.float32), name="CHANNEL_B")
    hdul = fits.HDUList([prim, ch_a, ch_b])

    # Disambiguate by name
    n1_a, n2_a, _, hdu_a = extract_and_validate_fits_dimensions(hdul, filename="generic.fits", target_hdu="CHANNEL_A")
    assert (n1_a, n2_a) == (200, 200)
    assert hdu_a.name == "CHANNEL_A"

    n1_b, n2_b, _, hdu_b = extract_and_validate_fits_dimensions(hdul, filename="generic.fits", target_hdu="CHANNEL_B")
    assert (n1_b, n2_b) == (400, 400)
    assert hdu_b.name == "CHANNEL_B"

    # Disambiguate by index
    n1_idx, n2_idx, _, hdu_idx = extract_and_validate_fits_dimensions(hdul, filename="generic.fits", target_hdu=1)
    assert (n1_idx, n2_idx) == (200, 200)
    assert hdu_idx is ch_a


def test_m6_2_5_6_generic_ambiguous_multi_image_without_disambiguation():
    """6. Generic ambiguous multi-image FITS without explicit disambiguation.
    Must raise FitsDimensionValidationError and report candidates and available HDUs.
    """
    prim = fits.PrimaryHDU()
    ch_a = fits.ImageHDU(data=np.ones((200, 200), dtype=np.float32), name="CHANNEL_A")
    ch_b = fits.ImageHDU(data=np.ones((400, 400), dtype=np.float32), name="CHANNEL_B")
    hdul = fits.HDUList([prim, ch_a, ch_b])

    with pytest.raises(FitsDimensionValidationError) as exc_info:
        extract_and_validate_fits_dimensions(hdul, filename="ambiguous.fits", target_hdu=None)

    err = str(exc_info.value)
    assert "multiple ambiguous 2D image extensions" in err
    assert "CHANNEL_A" in err
    assert "CHANNEL_B" in err
    assert "available: ['PRIMARY', 'CHANNEL_A', 'CHANNEL_B']" in err


def test_m6_2_5_7_valid_single_image_primary_hdu():
    """7. Valid single-image PrimaryHDU."""
    data = np.zeros((512, 512), dtype=np.float32)
    prim = fits.PrimaryHDU(data=data)
    hdul = fits.HDUList([prim])

    n1, n2, hdr, resolved = extract_and_validate_fits_dimensions(hdul, filename="single_prim.fits", target_hdu=None)
    assert (n1, n2) == (512, 512)
    assert resolved is prim
    assert resolved.data.shape == (512, 512)


# =============================================================================
# 5. Milestone 6.2.6 Compatibility & Bypass-Prevention Tests
# =============================================================================

def test_m6_2_6_spherex_semantics_cannot_be_bypassed_via_index():
    """Verify SPHEREx auxiliary rejection cannot be bypassed by supplying HDU index."""
    prim = fits.PrimaryHDU()
    prim.header["TELESCOP"] = "SPHEREx"
    img_hdu = fits.ImageHDU(data=np.ones((2040, 2040), dtype=np.float32), name="IMAGE")
    var_hdu = fits.ImageHDU(data=np.ones((2040, 2040), dtype=np.float32), name="VARIANCE")
    psf_hdu = fits.ImageHDU(data=np.ones((101, 101), dtype=np.float32), name="PSF")
    hdul = fits.HDUList([prim, img_hdu, var_hdu, psf_hdu])

    # Index 2 is VARIANCE: must be strictly rejected
    with pytest.raises(FitsDimensionValidationError) as exc_var_idx:
        extract_and_validate_fits_dimensions(hdul, filename="spx_indexed.fits", target_hdu=2)
    assert "attempting to use auxiliary extension 2 as the science image is strictly prohibited" in str(exc_var_idx.value)

    # Index 3 is PSF: must be strictly rejected
    with pytest.raises(FitsDimensionValidationError) as exc_psf_idx:
        extract_and_validate_fits_dimensions(hdul, filename="spx_indexed.fits", target_hdu=3)
    assert "attempting to use auxiliary extension 3 as the science image is strictly prohibited" in str(exc_psf_idx.value)

    # Index 1 is IMAGE: must succeed
    n1, n2, _, resolved = extract_and_validate_fits_dimensions(hdul, filename="spx_indexed.fits", target_hdu=1)
    assert (n1, n2) == (2040, 2040)
    assert resolved.name == "IMAGE"


def test_m6_2_6_generic_fits_permits_explicit_variance_selection():
    """Verify non-SPHEREx generic FITS products allow explicit selection of a valid extension
    named VARIANCE when the caller explicitly requests it.
    """
    prim = fits.PrimaryHDU()
    prim.header["TELESCOP"] = "GENERIC_OBSERVATORY"
    sci_hdu = fits.ImageHDU(data=np.ones((300, 300), dtype=np.float32), name="SCIENCE")
    var_hdu = fits.ImageHDU(data=np.ones((300, 300), dtype=np.float32), name="VARIANCE")
    hdul = fits.HDUList([prim, sci_hdu, var_hdu])

    # Explicitly requesting target_hdu="VARIANCE" on generic FITS must succeed
    n1, n2, hdr, resolved = extract_and_validate_fits_dimensions(
        hdul, filename="generic_with_variance.fits", target_hdu="VARIANCE"
    )
    assert (n1, n2) == (300, 300)
    assert resolved.name == "VARIANCE"

    # Explicitly requesting target_hdu=2 (index of VARIANCE) must also succeed on generic FITS
    n1_idx, n2_idx, _, resolved_idx = extract_and_validate_fits_dimensions(
        hdul, filename="generic_with_variance.fits", target_hdu=2
    )
    assert (n1_idx, n2_idx) == (300, 300)
    assert resolved_idx.name == "VARIANCE"
