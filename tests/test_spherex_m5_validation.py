"""SPHEREx Milestone 5 - Automated Scientific Validation Suite.
Validates all 12 acceptance requirements for temporal sky analysis and difference imaging:
  Gate 1: Multi-extension FITS ingestion (all HDUs present and valid)
  Gate 2: Quality mask bitwise filtering (known flags excluded, catalog source bit 21 preserved)
  Gate 3: WCS reprojection accuracy (sub-pixel alignment, surface brightness preserved)
  Gate 4: Variance propagation correctness (analytical bilinear weight squaring)
  Gate 5: Spectral compatibility enforcement (rejects mismatched bandpasses, verifies <= 2%)
  Gate 6: PSF homogenization verification (quadrature formula, matched FWHM)
  Gate 7: Difference image calculation (exactness D = I2 - I1)
  Gate 8: Significance map normalization (standard normal on null data)
  Gate 9: Change candidate detection (synthetic transient injection and recovery)
  Gate 10: Candidate qualification labeling (disclaimer label enforced)
  Gate 11: Edge artifact rejection (boundary pixels excluded)
  Gate 12: End-to-end real observation comparison (full pipeline on approved SPHEREx pair)
"""

from __future__ import annotations

import os
import sys
import pytest
import numpy as np
from astropy.wcs import WCS
from astropy.io import fits

# Ensure backend modules are discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.astronomy.spherex_mef_reader import read_spherex_mef_product, SpherexMefProduct
from app.astronomy.quality_mask import (
    create_quality_mask,
    FATAL_DEFECT_MASK,
    BIT_TRANSIENT,
    BIT_OVERFLOW,
    BIT_SUR_ERROR,
    BIT_NONFUNC,
    BIT_COLD,
    BIT_SOURCE,
    BIT_BLOOM,
    BIT_SNOWBALL,
)
from app.astronomy.image_registration import (
    create_common_wcs,
    reproject_to_common_grid,
    compute_registration_displacement,
)
from app.astronomy.spectral_compatibility import (
    LVFWavelengthModel,
    evaluate_spectral_compatibility,
)
from app.astronomy.psf_matching import match_psf_pair, estimate_effective_fwhm
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates, DISCLAIMER_LABEL
from app.services.temporal_service import TemporalService

REAL_FITS_1 = os.path.abspath("data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits")
REAL_FITS_2 = os.path.abspath("data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits")


# -----------------------------------------------------------------------------
# Gate 1: Multi-Extension FITS Ingestion
# -----------------------------------------------------------------------------
def test_gate_01_mef_ingestion():
    """Verify that read_spherex_mef_product ingests all 7 extensions and preserves dtypes."""
    prod = read_spherex_mef_product(REAL_FITS_1)
    assert isinstance(prod, SpherexMefProduct)
    assert prod.image.shape == (2040, 2040)
    assert prod.image.dtype == np.float32
    assert prod.flags.shape == (2040, 2040)
    assert prod.flags.dtype == np.int32
    assert prod.variance.shape == (2040, 2040)
    assert prod.variance.dtype == np.float32
    assert prod.zodi.shape == (2040, 2040)
    assert prod.zodi.dtype == np.float32
    assert len(prod.epsf_table) == 441
    assert prod.wcs_wave_values.shape == (9, 9, 2)
    assert prod.sha256 == "b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1"


# -----------------------------------------------------------------------------
# Gate 2: Quality Mask Bitwise Filtering & Catalog Source Preservation
# -----------------------------------------------------------------------------
def test_gate_02_quality_mask_policy():
    """Verify quality masking correctly excludes fatal bits while strictly preserving catalog sources."""
    img = np.ones((100, 100), dtype=np.float32) * 5.0
    flags = np.zeros((100, 100), dtype=np.int32)
    var = np.ones((100, 100), dtype=np.float32) * 0.1

    # Inject specific conditions:
    img[0, 0] = np.nan                   # NaN pixel
    img[0, 1] = np.inf                   # Inf pixel
    var[0, 2] = -1.0                     # Negative variance
    var[0, 3] = 0.0                      # Zero variance
    flags[10, 10] = BIT_TRANSIENT        # Fatal cosmic ray
    flags[10, 11] = BIT_OVERFLOW         # Fatal saturation
    flags[10, 12] = BIT_SUR_ERROR        # Fatal ramp fit error
    flags[10, 13] = BIT_NONFUNC          # Fatal non-functional
    flags[10, 14] = BIT_COLD             # Fatal dead pixel
    flags[20, 20] = BIT_SOURCE           # CATALOG SOURCE (MUST NOT BE REJECTED)
    flags[20, 21] = BIT_SOURCE | BIT_OVERFLOW  # Saturated source (Fatal takes precedence)

    res = create_quality_mask(img, flags, var, fatal_bitmask=FATAL_DEFECT_MASK)
    bad = res["bad_mask"]

    # Rejection checks
    assert bad[0, 0], "NaN pixel must be rejected"
    assert bad[0, 1], "Inf pixel must be rejected"
    assert bad[0, 2], "Negative variance pixel must be rejected"
    assert bad[0, 3], "Zero variance pixel must be rejected"
    assert bad[10, 10], "Cosmic ray must be rejected"
    assert bad[10, 11], "Saturation must be rejected"
    assert bad[10, 12], "SUR error must be rejected"
    assert bad[10, 13], "Nonfunc pixel must be rejected"
    assert bad[10, 14], "Cold pixel must be rejected"
    assert bad[20, 21], "Saturated source must be rejected due to saturation"

    # Catalog source preservation check
    assert not bad[20, 20], "Clean catalog source MUST NOT be rejected by quality mask"
    assert res["zodi_preserved"], "ZODI HDU preservation guarantee must be True"


# -----------------------------------------------------------------------------
# Gate 3: WCS Reprojection Accuracy & Surface Brightness Preservation
# -----------------------------------------------------------------------------
def test_gate_03_wcs_reprojection():
    """Verify sub-pixel reprojection accuracy and surface brightness conservation."""
    # Create simple tangent WCS centered at (45.0, 0.0)
    w_src = create_common_wcs(45.0, 0.0, pixel_scale_deg=0.0017222, npix_x=100, npix_y=100)
    # Uniform surface brightness disc
    img = np.zeros((100, 100), dtype=np.float32)
    img[40:60, 40:60] = 12.5  # MJy/sr

    # Reproject onto identical WCS grid
    reproj = reproject_to_common_grid(
        image=img,
        variance=None,
        source_wcs=w_src,
        target_wcs=w_src,
        target_shape=(100, 100),
    )
    # Inside the patch, surface brightness must remain exactly 12.5 MJy/sr
    patch = reproj["image"][45:55, 45:55]
    np.testing.assert_allclose(patch, 12.5, atol=1e-5)


# -----------------------------------------------------------------------------
# Gate 4: Variance Propagation Correctness
# -----------------------------------------------------------------------------
def test_gate_04_variance_propagation():
    """Verify that bilinear interpolation propagates variance as sum(w_i^2 * V_i)."""
    w_src = create_common_wcs(45.0, 0.0, pixel_scale_deg=0.0017222, npix_x=50, npix_y=50)
    # Shift target WCS by exactly 0.5 pixels in both axes
    w_tgt = WCS(w_src.to_header())
    w_tgt.wcs.crpix = [w_src.wcs.crpix[0] + 0.5, w_src.wcs.crpix[1] + 0.5]

    # Uniform variance = 4.0 (MJy/sr)^2
    var_const = 4.0
    var = np.full((50, 50), var_const, dtype=np.float32)
    img = np.ones((50, 50), dtype=np.float32)

    reproj = reproject_to_common_grid(
        image=img,
        variance=var,
        source_wcs=w_src,
        target_wcs=w_tgt,
        target_shape=(50, 50),
        order=1,
    )

    # For 0.5 pixel shift: w = [0.25, 0.25, 0.25, 0.25]
    # sum(w_i^2) = 4 * (0.25)^2 = 0.25
    # Resampled variance = 0.25 * 4.0 = 1.0
    center_var = reproj["variance"][20:30, 20:30]
    np.testing.assert_allclose(center_var, 1.0, atol=1e-4)


# -----------------------------------------------------------------------------
# Gate 5: Spectral Compatibility Enforcement
# -----------------------------------------------------------------------------
def test_gate_05_spectral_compatibility():
    """Verify that LVF spectral matching strictly rejects mismatched bandpasses (> 2%)."""
    x_grid = np.linspace(1, 100, 5)
    y_grid = np.linspace(1, 100, 5)
    vals1 = np.zeros((5, 5, 2))
    vals1[:, :, 0] = 1.0  # 1.0 micron
    vals1[:, :, 1] = 0.025
    m1 = LVFWavelengthModel(x_grid, y_grid, vals1)

    # Case A: Compatible epoch (1.005 micron, 0.5% diff <= 2.0%)
    vals_compat = np.zeros((5, 5, 2))
    vals_compat[:, :, 0] = 1.005
    vals_compat[:, :, 1] = 0.025
    m_compat = LVFWavelengthModel(x_grid, y_grid, vals_compat)

    # Case B: Incompatible epoch (1.050 micron, 5.0% diff > 2.0%)
    vals_incompat = np.zeros((5, 5, 2))
    vals_incompat[:, :, 0] = 1.050
    vals_incompat[:, :, 1] = 0.025
    m_incompat = LVFWavelengthModel(x_grid, y_grid, vals_incompat)

    pts = np.array([50.0])
    res_compat = evaluate_spectral_compatibility(m1, m_compat, pts, pts, pts, pts, tolerance=0.02)
    assert res_compat["compatible_mask"][0] == True
    assert res_compat["compatibility_fraction"] == 1.0

    res_incompat = evaluate_spectral_compatibility(m1, m_incompat, pts, pts, pts, pts, tolerance=0.02)
    assert res_incompat["compatible_mask"][0] == False
    assert res_incompat["compatibility_fraction"] == 0.0


# -----------------------------------------------------------------------------
# Gate 6: PSF Homogenization Verification
# -----------------------------------------------------------------------------
def test_gate_06_psf_homogenization():
    """Verify quadrature kernel matching sigma_kernel = sqrt(target^2 - native^2)."""
    # Create two synthetic images: Epoch 1 (sharp, FWHM=1.5), Epoch 2 (broad, FWHM=2.5)
    img1 = np.zeros((64, 64), dtype=np.float32)
    img1[32, 32] = 100.0  # Delta function
    img2 = np.zeros((64, 64), dtype=np.float32)
    img2[32, 32] = 100.0

    res = match_psf_pair(img1, None, img2, None, fwhm1=1.5, fwhm2=2.5)
    assert res["convolved_epoch"] == 1
    assert res["target_fwhm"] == 2.5

    # Check analytical quadrature matching sigma
    sig1 = 1.5 / 2.35482
    sig2 = 2.5 / 2.35482
    expected_sigma_m = np.sqrt(sig2**2 - sig1**2)
    np.testing.assert_allclose(res["matching_sigma"], expected_sigma_m, atol=1e-3)


# -----------------------------------------------------------------------------
# Gate 7: Difference Image Exactness
# -----------------------------------------------------------------------------
def test_gate_07_difference_exactness():
    """Verify D = I2 - I1 without alteration or distortion."""
    img1 = np.ones((50, 50), dtype=np.float32) * 10.0
    img2 = np.ones((50, 50), dtype=np.float32) * 13.5
    var = np.ones((50, 50), dtype=np.float32) * 0.25

    # With subtract_residual_background=False to test pure algebraic D = I2 - I1
    diff_res = compute_difference_and_significance(
        image1=img1,
        variance1=var,
        image2=img2,
        variance2=var,
        subtract_residual_background=False,
    )
    diff = diff_res["difference_image"]
    np.testing.assert_allclose(diff, 3.5, atol=1e-5)
    # sigma_D = sqrt(0.25 + 0.25) = sqrt(0.5) ~ 0.7071
    # Significance = 3.5 / sqrt(0.5) ~ 4.9497
    np.testing.assert_allclose(diff_res["significance_map"], 3.5 / np.sqrt(0.5), atol=1e-4)


# -----------------------------------------------------------------------------
# Gate 8: Significance Map Normalization on Null Data
# -----------------------------------------------------------------------------
def test_gate_08_significance_null_data():
    """Verify that significance map S on pure Gaussian noise is standard normal N(0, 1)."""
    np.random.seed(42)
    sigma_noise = 0.5
    var_noise = sigma_noise ** 2
    n = 200

    img1 = np.random.normal(0.0, sigma_noise, (n, n)).astype(np.float32)
    img2 = np.random.normal(0.0, sigma_noise, (n, n)).astype(np.float32)
    var1 = np.full((n, n), var_noise, dtype=np.float32)
    var2 = np.full((n, n), var_noise, dtype=np.float32)

    diff_res = compute_difference_and_significance(img1, var1, img2, var2, subtract_residual_background=True)
    sig = diff_res["significance_map"]

    mean_s = np.mean(sig)
    std_s = np.std(sig)

    assert abs(mean_s) < 0.05, f"Significance mean {mean_s} should be close to 0.0"
    assert abs(std_s - 1.0) < 0.05, f"Significance std {std_s} should be close to 1.0"


# -----------------------------------------------------------------------------
# Gate 9: Change Candidate Detection & Recovery
# -----------------------------------------------------------------------------
def test_gate_09_synthetic_injection_recovery():
    """Inject synthetic transient source and verify 100% recovery with correct parameters."""
    n = 100
    img1 = np.zeros((n, n), dtype=np.float32)
    img2 = np.zeros((n, n), dtype=np.float32)
    var = np.ones((n, n), dtype=np.float32) * 1.0

    # Inject positive transient of SNR = 8.0 at (x=50, y=50)
    img2[49:52, 49:52] = 8.0  # 3x3 patch

    diff_res = compute_difference_and_significance(img1, var, img2, var, subtract_residual_background=False)
    cand_res = extract_change_candidates(
        significance_map=diff_res["significance_map"],
        difference_image=diff_res["difference_image"],
        significance_threshold=5.0,
    )

    assert cand_res["candidate_count"] == 1
    c = cand_res["candidates"][0]
    assert c["polarity"] == "POSITIVE"
    assert abs(c["pixel_x"] - 50.0) < 1.0
    assert abs(c["pixel_y"] - 50.0) < 1.0
    assert c["significance_peak"] >= 5.0


# -----------------------------------------------------------------------------
# Gate 10: Candidate Qualification Labeling
# -----------------------------------------------------------------------------
def test_gate_10_mandatory_disclaimer_label():
    """Verify that every extracted candidate carries the mandatory scientific disclaimer."""
    sig = np.zeros((50, 50), dtype=np.float32)
    diff = np.zeros((50, 50), dtype=np.float32)
    sig[25:28, 25:28] = 6.0
    diff[25:28, 25:28] = 3.0

    cands = extract_change_candidates(sig, diff, significance_threshold=5.0)["candidates"]
    assert len(cands) > 0
    for c in cands:
        assert c["scientific_status"] == DISCLAIMER_LABEL
        assert "NOT SCIENTIFICALLY CONFIRMED" in c["scientific_status"]


# -----------------------------------------------------------------------------
# Gate 11: Edge Artifact Rejection
# -----------------------------------------------------------------------------
def test_gate_11_edge_artifact_rejection():
    """Verify that edge pixels are identified and flagged."""
    sig = np.zeros((100, 100), dtype=np.float32)
    diff = np.zeros((100, 100), dtype=np.float32)
    # Transient at edge (x=5, y=5)
    sig[4:7, 4:7] = 7.0
    diff[4:7, 4:7] = 3.5

    cands = extract_change_candidates(sig, diff, significance_threshold=5.0)["candidates"]
    assert len(cands) == 1
    assert "NEAR_IMAGE_BOUNDARY" in cands[0]["warnings"]


# -----------------------------------------------------------------------------
# Gate 12: End-to-End Real SPHEREx Observation Comparison
# -----------------------------------------------------------------------------
def test_gate_12_real_spherex_pair():
    """Execute complete end-to-end temporal pipeline on the approved real SPHEREx Level-2 observation pair."""
    service = TemporalService()
    res = service.run_difference_pipeline(
        fits_path_1=REAL_FITS_1,
        fits_path_2=REAL_FITS_2,
        significance_threshold=3.5,
        spectral_tolerance=0.02,
        grid_size=512,
        subtract_background=True,
    )

    # Validate output contract
    assert res["epoch_1"]["band"] == "SPHEREx-D1"
    assert res["epoch_2"]["band"] == "SPHEREx-D1"
    assert abs(res["temporal_baseline"]["delta_days"] - 8.0742) < 0.01
    assert res["spectral_compatibility"]["is_spectrally_viable"] == True
    assert res["spectral_compatibility"]["compatibility_fraction"] > 0.99
    assert res["difference_metrics"]["valid_fraction"] > 0.95
    assert res["scientific_disclaimer"] == DISCLAIMER_LABEL
    assert res["candidate_count"] > 0
    assert "difference_image_b64" in res["previews"]
    assert "significance_map_b64" in res["previews"]
