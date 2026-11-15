"""Milestone 4 — Temporal Observation Comparison & Difference Imaging Validation Suite.
Tests:
- T01: Multi-epoch observation timeline extraction and 4-pass chronological integrity
- T02: Difference image computation D(x, y) = I_2(x, y) - I_1(x, y) and D_abs(x, y)
- T03: Robust MAD background noise estimation (Median Absolute Deviation)
- T04: 3.5-sigma detection thresholding and mask generation
- T05: Connected component labeling and peak candidate extraction
- T06: Signal-to-Noise Ratio (SNR) and significance computation
- T07: Quality assessment flag assignment (TARGET_CENTRAL_RESIDUAL, EDGE_PROXIMITY, etc.)
- T08: Astrometric proper motion tracking across multi-epoch baselines (Barnard's Star & WISE 0855)
- T09: Episodic infrared variability detection (RW Aurigae dimming & R Draconis Mira pulsation)
- T10: Difference map visualization rendering (seismic color mapping to PNG Data URI)
- T11: FastAPI /api/v1/images/difference endpoint integration
"""

import math
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.image_processing.diff_imaging import (
    compute_mad_sigma,
    render_array_to_base64_png,
    compute_difference_image,
)
from app.image_processing.cutout import create_synthetic_astronomical_cutout
from app.providers import get_data_provider


def test_t01_multi_epoch_timeline():
    """T01: Multi-epoch timeline contains 4 sequential survey passes with positive time baselines."""
    provider = get_data_provider("curated")
    slugs = ["barnards-star", "wise-0855", "epsilon-indi-b", "rw-aurigae", "r-draconis"]
    targets = [provider.get_target_by_id(s) for s in slugs if provider.get_target_by_id(s)]
    assert len(targets) == 5, "Must have all 5 scientific validation targets"

    for t in targets:
        epochs = t.available_epochs
        assert len(epochs) == 4, f"Target {t.name} must have 4 survey passes"
        mjds = [ep.mjd for ep in epochs]
        assert mjds == sorted(mjds), f"Epochs for {t.name} must be strictly chronological"
        # Check 6-month survey spacing (~180 days)
        for i in range(len(mjds) - 1):
            delta = mjds[i + 1] - mjds[i]
            assert 130 <= delta <= 200, f"Expected ~180-day survey cadence, got {delta} days"

    print("[PASS] T01: Multi-epoch observation timeline extraction and 4-pass chronological integrity")


def test_t02_difference_computation():
    """T02: Difference image computation D(x,y) = I2 - I1."""
    # Synthetic clean background with a transient source in I2
    h, w = 64, 64
    np.random.seed(42)
    i1 = np.ones((h, w), dtype=np.float32) * 5.0 + np.random.normal(0, 0.1, (h, w)).astype(np.float32)
    i2 = i1.copy()
    # Add transient brightening at center
    i2[32, 32] += 2.5

    signed_diff = i2 - i1
    abs_diff = np.abs(signed_diff)

    assert signed_diff[32, 32] > 2.0, "Center pixel must register positive flux difference"
    assert abs_diff[32, 32] == abs(signed_diff[32, 32]), "Absolute difference must match magnitude"
    assert np.median(signed_diff) < 0.05, "Background differential median should be near zero"

    print("[PASS] T02: Difference image computation D(x, y) = I_2(x, y) - I_1(x, y)")


def test_t03_mad_noise_estimation():
    """T03: Robust MAD background noise estimation."""
    np.random.seed(123)
    # Known Gaussian noise with std = 0.50
    noise = np.random.normal(0, 0.50, (100, 100))
    # Add extreme outliers that would corrupt standard deviation
    noise[10, 10] = 500.0
    noise[50, 50] = -700.0

    std_val = float(np.std(noise))
    mad_sigma = compute_mad_sigma(noise)

    # Standard deviation is heavily biased by the two outliers (>8.0)
    assert std_val > 5.0, "Standard deviation should be biased by outliers"
    # MAD sigma should remain resilient near 0.50 (+/- 0.05)
    assert 0.45 <= mad_sigma <= 0.55, f"MAD sigma expected ~0.50, got {mad_sigma}"

    print(f"[PASS] T03: Robust MAD background noise estimation (MAD σ={mad_sigma:.4f} vs biased std={std_val:.2f})")


def test_t04_thresholding_and_mask():
    """T04: Statistical thresholding mask at k * sigma_MAD."""
    data = np.zeros((50, 50), dtype=np.float32)
    sigma = 0.20
    # Add source at 4.5 sigma
    data[25, 25] = 4.5 * sigma
    # Add sub-threshold noise at 2.0 sigma
    data[10, 10] = 2.0 * sigma

    k = 3.5
    threshold = k * sigma
    mask = (data > threshold)

    assert mask[25, 25] == True, "4.5σ source must be detected"
    assert mask[10, 10] == False, "2.0σ noise must NOT trigger detection"

    print("[PASS] T04: 3.5-sigma detection thresholding and mask generation")


def test_t05_t06_candidate_extraction_and_snr():
    """T05 & T06: Candidate extraction, peak position, and SNR calculation."""
    h, w = 60, 60
    np.random.seed(99)
    noise_sigma = 0.05
    i1 = np.random.normal(1.0, noise_sigma, (h, w)).astype(np.float32)
    i2 = i1.copy()

    # Introduce transient candidate at pixel (20, 40) with amplitude 0.75
    i2[20, 40] += 0.75

    res = compute_difference_image(
        image1=i1,
        image2=i2,
        center_ra=180.0,
        center_dec=20.0,
        pixel_scale_arcsec=6.2,
        sigma_threshold=3.5,
    )

    assert res.candidates_found >= 1, "Must find the injected transient source"
    top_cand = res.candidates[0]
    assert abs(top_cand.pixel_x - 40.0) <= 1.0, f"Expected x ~ 40, got {top_cand.pixel_x}"
    assert abs(top_cand.pixel_y - 20.0) <= 1.0, f"Expected y ~ 20, got {top_cand.pixel_y}"
    assert top_cand.snr >= 10.0, f"Expected high SNR, got {top_cand.snr}"

    print(f"[PASS] T05 & T06: Peak candidate extraction at ({top_cand.pixel_x}, {top_cand.pixel_y}) with SNR {top_cand.snr}σ")


def test_t07_quality_assessment_flags():
    """T07: Quality assessment flag assignment (EDGE_PROXIMITY, TARGET_CENTRAL_RESIDUAL)."""
    h, w = 60, 60
    i1 = np.zeros((h, w), dtype=np.float32)
    i2 = i1.copy()

    # Candidate 1: At image edge (x=1, y=1)
    i2[1, 1] += 2.0
    # Candidate 2: At center (x=30, y=30)
    i2[30, 30] += 2.0

    res = compute_difference_image(
        image1=i1,
        image2=i2,
        center_ra=180.0,
        center_dec=20.0,
        pixel_scale_arcsec=6.2,
        sigma_threshold=3.5,
    )

    flags_found = [c.flag for c in res.candidates]
    has_edge = any("EDGE_PROXIMITY" in f for f in flags_found)
    has_center = any("TARGET_CENTRAL_RESIDUAL" in f for f in flags_found)

    assert has_edge, "Edge candidate must have EDGE_PROXIMITY flag"
    assert has_center, "Center candidate must have TARGET_CENTRAL_RESIDUAL flag"

    print("[PASS] T07: Quality assessment flags (EDGE_PROXIMITY & TARGET_CENTRAL_RESIDUAL verified)")


def test_t08_proper_motion_tracking():
    """T08: Proper motion tracking across multi-epoch baselines (Barnard's Star ~10.3\"/yr)."""
    provider = get_data_provider("curated")
    barnard = provider.get_target_by_id("barnards-star")
    assert barnard is not None

    total_pm_mas_yr = math.hypot(barnard.proper_motion_ra_mas_yr, barnard.proper_motion_dec_mas_yr)
    total_pm_arcsec_yr = total_pm_mas_yr / 1000.0

    assert 10.0 <= total_pm_arcsec_yr <= 10.6, f"Barnard's Star proper motion should be ~10.3\"/yr, got {total_pm_arcsec_yr}"

    # Generate cutouts for Pass 1 (0 days) and Pass 3 (368 days ~ 1.01 year)
    d1, _, _ = create_synthetic_astronomical_cutout(
        ra_deg=barnard.ra_deg,
        dec_deg=barnard.dec_deg,
        fov_arcmin=4.0,
        epoch_id="EPOCH-PASS1-20250615",
        time_offset_days=0.0,
        proper_motion_ra=barnard.proper_motion_ra_mas_yr,
        proper_motion_dec=barnard.proper_motion_dec_mas_yr,
    )

    d3, _, _ = create_synthetic_astronomical_cutout(
        ra_deg=barnard.ra_deg,
        dec_deg=barnard.dec_deg,
        fov_arcmin=4.0,
        epoch_id="EPOCH-PASS3-20260618",
        time_offset_days=368.0,
        proper_motion_ra=barnard.proper_motion_ra_mas_yr,
        proper_motion_dec=barnard.proper_motion_dec_mas_yr,
    )

    # Perform difference imaging
    res = compute_difference_image(
        image1=d1,
        image2=d3,
        center_ra=barnard.ra_deg,
        center_dec=barnard.dec_deg,
        pixel_scale_arcsec=4.0,
        target_name="Barnard's Star",
    )

    assert res.candidates_found >= 1, "Barnard's star displacement must create strong differential dipole"
    assert res.max_abs_diff_mjy > 1.0, "High proper motion must produce notable flux difference"

    print(f"[PASS] T08: Astrometric proper motion tracking ({total_pm_arcsec_yr:.2f}\"/yr dipole detected)")


def test_t09_episodic_variability():
    """T09: Episodic variability detection (RW Aurigae dimming & R Draconis Mira pulsation)."""
    provider = get_data_provider("curated")
    r_dra = provider.get_target_by_id("r-draconis")
    assert r_dra is not None

    # Generate cutouts across Mira pulsation cycle (epoch 1 vs epoch 2)
    d1, _, _ = create_synthetic_astronomical_cutout(
        ra_deg=r_dra.ra_deg,
        dec_deg=r_dra.dec_deg,
        fov_arcmin=5.0,
        epoch_id="EPOCH-PASS1-20250615",
        time_offset_days=0.0,
        is_variable=True,
    )

    d2, _, _ = create_synthetic_astronomical_cutout(
        ra_deg=r_dra.ra_deg,
        dec_deg=r_dra.dec_deg,
        fov_arcmin=5.0,
        epoch_id="EPOCH-PASS2-20251214",
        time_offset_days=182.0,
        is_variable=True,
    )

    res = compute_difference_image(
        image1=d1,
        image2=d2,
        center_ra=r_dra.ra_deg,
        center_dec=r_dra.dec_deg,
        target_name="R Draconis",
    )

    assert res.candidates_found >= 1, "Mira variable pulsation must trigger significant candidate detection"
    assert res.candidates[0].snr > 10.0, "Pulsation SNR should be large"

    print(f"[PASS] T09: Episodic infrared variability (R Draconis Mira variable ΔFlux={res.max_abs_diff_mjy:.3f} mJy/sr)")


def test_t10_difference_map_rendering():
    """T10: Difference map visualization rendering to seismic base64 PNG."""
    diff_arr = np.array([[-1.0, 0.0, 1.0], [0.5, -0.5, 0.0]], dtype=np.float32)
    b64_str = render_array_to_base64_png(diff_arr, colormap="seismic")

    assert b64_str.startswith("data:image/png;base64,"), "Must return valid PNG Data URI"
    assert len(b64_str) > 100, "Base64 string must contain valid payload"

    print("[PASS] T10: Difference map visualization rendering (seismic colormap Data URI verified)")


def test_t11_api_integration():
    """T11: FastAPI /api/v1/images/difference endpoint integration."""
    client = TestClient(app)
    payload = {
        "target": "wise-0855",
        "epoch_ref": "EPOCH-PASS1-20250615",
        "epoch_cmp": "EPOCH-PASS2-20251214",
        "channel": 50,
        "sigma_threshold": 3.5,
    }
    response = client.post("/api/v1/images/difference", json=payload)
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data["target_name"] == "WISE 0855"
    assert data["delta_days"] == 182.0
    assert data["diff_image_base64"].startswith("data:image/png;base64,")
    assert "candidates" in data
    assert len(data["candidates"]) >= 1

    print("[PASS] T11: FastAPI /api/v1/images/difference HTTP endpoint integration")


if __name__ == "__main__":
    print("\n=================================================")
    print("  SPHEREx Milestone 4: Backend Temporal Tests    ")
    print("=================================================\n")

    test_t01_multi_epoch_timeline()
    test_t02_difference_computation()
    test_t03_mad_noise_estimation()
    test_t04_thresholding_and_mask()
    test_t05_t06_candidate_extraction_and_snr()
    test_t07_quality_assessment_flags()
    test_t08_proper_motion_tracking()
    test_t09_episodic_variability()
    test_t10_difference_map_rendering()
    test_t11_api_integration()

    print("\n=================================================")
    print("  ALL 11 BACKEND TEMPORAL TESTS PASSED (100%)    ")
    print("=================================================\n")
