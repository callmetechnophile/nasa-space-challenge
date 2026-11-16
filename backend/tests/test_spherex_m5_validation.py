"""SPHEREx Milestone 5 Comprehensive Scientific Validation Test Suite.
Validates:
1. LVF spectral compatibility modeling and WAVE-TAB evaluation.
2. WCS common-grid reprojection and surface-brightness preservation.
3. Multi-extension quality masking and ZODI preservation.
4. PSF matching without deconvolution and variance propagation.
5. Numerical difference engine and significance mapping.
6. Conservative change candidate extraction with mandatory non-discovery disclaimer.
7. REST API routes for temporal comparison.
"""

import os
import pytest
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from fastapi.testclient import TestClient

from app.main import app
from app.astronomy.spectral_compatibility import (
    LVFWavelengthModel,
    evaluate_spectral_compatibility,
)
from app.astronomy.image_registration import (
    create_common_wcs,
    reproject_to_common_grid,
    compute_registration_displacement,
)
from app.astronomy.quality_mask import (
    create_quality_mask,
    DEFAULT_FATAL_MASK,
    BIT_TRANSIENT,
    BIT_COLD,
)
from app.astronomy.psf_matching import match_psf_pair, estimate_effective_fwhm
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates, DISCLAIMER_LABEL
from app.services.temporal_service import TemporalService

client = TestClient(app)

FIXTURES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/spherex/fixtures_m5")
)
REAL_FITS_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits",
    )
)


class TestSpectralCompatibility:
    """Validates Linear Variable Filter (LVF) transmission modeling and spectral equivalence."""

    def test_lvf_evaluation_and_interpolation(self):
        # Create 9x9 test grid covering Detector 1: 0.75 - 1.12 um
        x_grid = np.linspace(1, 2040, 9)
        y_grid = np.linspace(1, 2040, 9)
        values = np.zeros((9, 9, 2), dtype=np.float64)
        for i, y in enumerate(y_grid):
            lam = 0.75 + (2040.0 - y) / 2039.0 * (1.12 - 0.75)
            for j in range(9):
                values[i, j, 0] = lam
                values[i, j, 1] = lam / 40.0

        model = LVFWavelengthModel(x_grid, y_grid, values)
        # Check corners and center
        l_top, _ = model.evaluate(np.array([1020.0]), np.array([1.0]))
        l_bot, _ = model.evaluate(np.array([1020.0]), np.array([2040.0]))
        l_mid, _ = model.evaluate(np.array([1020.0]), np.array([1020.0]))

        assert np.isclose(l_top[0], 1.12, atol=1e-3)
        assert np.isclose(l_bot[0], 0.75, atol=1e-3)
        assert 0.75 < l_mid[0] < 1.12

    def test_spectral_compatibility_rule(self):
        model1 = LVFWavelengthModel.synthetic_default(detector=1)
        model2 = LVFWavelengthModel.synthetic_default(detector=1)

        # Same pixel coordinates -> relative difference must be exactly 0
        x = np.array([500.0, 1000.0])
        y = np.array([500.0, 1000.0])
        res = evaluate_spectral_compatibility(model1, model2, x, y, x, y, tolerance=0.02)
        assert res["compatibility_fraction"] == 1.0
        assert np.all(res["rel_diff"] < 1e-6)

        # Large shift along dispersion axis (Y shifted by 400 pixels) -> incompatible
        y_shifted = y + 400.0
        res_shift = evaluate_spectral_compatibility(model1, model2, x, y, x, y_shifted, tolerance=0.02)
        assert res_shift["compatibility_fraction"] < 1.0
        assert np.any(~res_shift["compatible_mask"])


class TestImageRegistration:
    """Validates WCS reprojection onto common celestial grid."""

    def test_common_wcs_and_reprojection(self):
        target_wcs = create_common_wcs(ra_center=45.0, dec_center=0.0, npix_x=64, npix_y=64)
        assert target_wcs.is_celestial

        # Source image: 64x64 flat 5.0 MJy/sr
        src_img = np.full((64, 64), 5.0, dtype=np.float32)
        src_var = np.full((64, 64), 0.25, dtype=np.float32)
        src_wcs = create_common_wcs(ra_center=45.0, dec_center=0.0, npix_x=64, npix_y=64)

        reproj = reproject_to_common_grid(src_img, src_var, src_wcs, target_wcs, target_shape=(64, 64))
        # Surface brightness must be preserved across overlapping pixels
        assert np.mean(reproj["valid_mask"]) > 0.90
        valid = reproj["valid_mask"]
        assert np.allclose(reproj["image"][valid], 5.0, atol=1e-3)
        assert np.allclose(reproj["variance"][valid], 0.25, atol=1e-3)

    def test_registration_displacement_calculation(self):
        wcs1 = create_common_wcs(ra_center=45.0, dec_center=0.0)
        # Shift Epoch 2 by 0.001 deg in RA
        wcs2 = create_common_wcs(ra_center=45.001, dec_center=0.0)
        disp = compute_registration_displacement(wcs1, wcs2, 45.0, 0.0)
        assert disp["angular_separation_arcsec"] > 0.0
        assert np.isclose(disp["angular_separation_arcsec"], 3.6, atol=0.2)


class TestQualityMasking:
    """Validates 32-bit integer FLAGS masking and ZODI preservation."""

    def test_flags_bitmask_and_nans(self):
        img = np.ones((10, 10), dtype=np.float32)
        img[2, 2] = np.nan
        img[3, 3] = np.inf

        flags = np.zeros((10, 10), dtype=np.int32)
        flags[4, 4] = BIT_TRANSIENT  # FLAG_COSMIC_RAY
        flags[5, 5] = BIT_COLD        # FLAG_DEAD_PIXEL

        var = np.full((10, 10), 0.1, dtype=np.float32)
        var[6, 6] = -1.0  # Invalid negative variance

        qmask = create_quality_mask(img, flags, var)
        bad = qmask["bad_mask"]

        assert bad[2, 2]  # NaN
        assert bad[3, 3]  # Inf
        assert bad[4, 4]  # Cosmic Ray
        assert bad[5, 5]  # Dead Pixel
        assert bad[6, 6]  # Negative variance
        assert not bad[0, 0]  # Valid pixel
        assert qmask["zodi_preserved"] is True


class TestPSFMatching:
    """Validates PSF matching without deconvolution."""

    def test_psf_matching_sharp_epoch_convolution(self):
        img1 = np.zeros((31, 31), dtype=np.float32)
        img1[15, 15] = 100.0  # Sharp delta source in Epoch 1
        img2 = np.zeros((31, 31), dtype=np.float32)
        img2[15, 15] = 100.0

        var1 = np.full((31, 31), 1.0, dtype=np.float32)
        var2 = np.full((31, 31), 1.0, dtype=np.float32)

        # FWHM1 = 1.5, FWHM2 = 3.0 -> Epoch 1 must be convolved
        res = match_psf_pair(img1, var1, img2, var2, fwhm1=1.5, fwhm2=3.0)
        assert res["convolved_epoch"] == 1
        assert res["target_fwhm"] == 3.0
        # Peak of img1 should be smoothed/reduced by convolution
        assert res["matched_image1"][15, 15] < 100.0


class TestDifferenceEngineAndCandidateExtraction:
    """Validates mathematical difference calculation, significance mapping, and candidate labeling."""

    def test_difference_and_significance_math(self):
        img1 = np.full((20, 20), 10.0, dtype=np.float32)
        img2 = np.full((20, 20), 10.0, dtype=np.float32)
        # Inject transient in Epoch 2
        img2[10, 10] = 16.0

        var1 = np.full((20, 20), 0.5, dtype=np.float32)
        var2 = np.full((20, 20), 0.5, dtype=np.float32)

        diff_res = compute_difference_and_significance(img1, var1, img2, var2, subtract_residual_background=False)
        D = diff_res["difference_image"]
        S = diff_res["significance_map"]
        sigma_D = diff_res["diff_sigma"]

        # V_D = 0.5 + 0.5 = 1.0 -> sigma_D = 1.0
        assert np.isclose(sigma_D[10, 10], 1.0)
        # D[10, 10] = 16 - 10 = 6.0
        assert np.isclose(D[10, 10], 6.0)
        # S[10, 10] = 6.0 / 1.0 = 6.0 sigma
        assert np.isclose(S[10, 10], 6.0)

    def test_conservative_candidate_extraction_disclaimer(self):
        sig = np.zeros((50, 50), dtype=np.float32)
        diff = np.zeros((50, 50), dtype=np.float32)

        # Create connected component (area = 5 pixels) above 4 sigma
        sig[20:23, 20:22] = 5.0
        diff[20:23, 20:22] = 2.5

        # Create 1-pixel noise spike at (5, 5) which must be rejected (min_area >= 3)
        sig[5, 5] = 6.0
        diff[5, 5] = 3.0

        cand_res = extract_change_candidates(sig, diff, significance_threshold=3.5, min_area_pixels=3)
        assert cand_res["candidate_count"] == 1
        cand = cand_res["candidates"][0]
        assert cand["polarity"] == "POSITIVE"
        assert cand["significance_peak"] == 5.0
        assert cand["scientific_status"] == DISCLAIMER_LABEL


class TestTemporalServiceAndFixtures:
    """Validates end-to-end temporal pipeline on synthetic fixtures and real data."""

    def test_fixtures_end_to_end(self):
        f1 = os.path.join(FIXTURES_DIR, "m5_synthetic_epoch1.fits")
        f2 = os.path.join(FIXTURES_DIR, "m5_synthetic_epoch2.fits")
        assert os.path.exists(f1)
        assert os.path.exists(f2)

        service = TemporalService()
        res = service.run_difference_pipeline(f1, f2, significance_threshold=3.5, grid_size=512)

        assert res["temporal_baseline"]["delta_days"] == 30.0
        assert res["spectral_compatibility"]["is_spectrally_viable"] is True
        assert res["candidate_count"] >= 2

        polarities = {c["polarity"] for c in res["candidates"]}
        assert "POSITIVE" in polarities
        assert "NEGATIVE" in polarities

        for c in res["candidates"]:
            assert c["scientific_status"] == DISCLAIMER_LABEL

    def test_real_fits_self_difference(self):
        if not os.path.exists(REAL_FITS_PATH):
            pytest.skip("Real SPHEREx FITS product not found")

        service = TemporalService()
        res = service.run_difference_pipeline(REAL_FITS_PATH, REAL_FITS_PATH, grid_size=256)

        assert res["difference_metrics"]["rms_noise_mjy_sr"] == 0.0
        assert res["candidate_count"] == 0
        assert res["spectral_compatibility"]["is_spectrally_viable"] is True


class TestTemporalApiRoutes:
    """Validates FastAPI temporal endpoints."""

    def test_api_benchmark_pairs(self):
        resp = client.get("/api/v1/temporal/benchmark-pairs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 3

    def test_api_observations(self):
        resp = client.get("/api/v1/temporal/observations")
        assert resp.status_code == 200
        data = resp.json()
        assert "observations" in data

    def test_api_compare_fixtures(self):
        f1 = os.path.join(FIXTURES_DIR, "m5_synthetic_epoch1.fits")
        f2 = os.path.join(FIXTURES_DIR, "m5_synthetic_epoch2.fits")

        payload = {
            "file1": f1,
            "file2": f2,
            "significance_threshold": 3.5,
            "spectral_tolerance": 0.02,
            "grid_size": 256,
        }
        resp = client.post("/api/v1/temporal/compare", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["candidate_count"] >= 2
        assert data["scientific_disclaimer"] == DISCLAIMER_LABEL

    def test_api_compare_missing_file_structured_error(self):
        payload = {
            "file1": "non_existent_epoch_1.fits",
            "file2": "non_existent_epoch_2.fits",
            "significance_threshold": 3.5,
            "spectral_tolerance": 0.02,
        }
        resp = client.post("/api/v1/temporal/compare", json=payload)
        assert resp.status_code == 404
        detail = resp.json()["detail"]
        assert isinstance(detail, dict)
        assert detail["stage"] == "FILE_INGESTION"
        assert detail["category"] == "MISSING_INPUT_FILE"
        assert "non_existent_epoch_1.fits" in detail["filename"]

    def test_api_compare_approved_real_pair(self):
        f1 = "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
        f2 = "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"
        payload = {
            "file1": f1,
            "file2": f2,
            "significance_threshold": 3.5,
            "spectral_tolerance": 0.02,
            "grid_size": 256,
        }
        resp = client.post("/api/v1/temporal/compare", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["comparison_status"] == "SUCCESS"
        assert "processing_duration_sec" in data
        assert data["processing_duration_sec"] > 0
        assert data["valid_pixel_count"] > 0
        assert data["provenance"]["provenance_state"] == "REAL_VERIFIED"
        assert data["candidate_count"] > 0
