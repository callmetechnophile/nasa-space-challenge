"""Unit tests for difference imaging and statistical transient detection."""

import numpy as np
import pytest
from app.image_processing.diff_imaging import (
    compute_mad_sigma,
    compute_difference_image,
)


def test_compute_mad_sigma():
    rng = np.random.default_rng(42)
    # Normal distribution with standard deviation 2.5
    data = rng.normal(loc=10.0, scale=2.5, size=(100, 100))
    sigma = compute_mad_sigma(data)
    assert pytest.approx(sigma, rel=0.1) == 2.5


def test_difference_imaging_identical():
    # Identical images should have ~0 difference and 0 candidates
    img = np.ones((45, 45), dtype=np.float32)
    res = compute_difference_image(
        image1=img,
        image2=img,
        center_ra=180.0,
        center_dec=0.0,
        sigma_threshold=4.0,
    )
    assert res.max_abs_diff_mjy == 0.0
    assert res.candidates_found == 0


def test_difference_imaging_with_transient_source():
    # Base image with background noise
    rng = np.random.default_rng(123)
    img1 = rng.normal(0.2, 0.02, size=(51, 51)).astype(np.float32)
    img2 = img1.copy()

    # Inject transient brightening at pixel (25, 25)
    img2[25, 25] += 1.5

    res = compute_difference_image(
        image1=img1,
        image2=img2,
        center_ra=133.795,
        center_dec=-7.245,
        sigma_threshold=3.5,
    )

    assert res.candidates_found >= 1
    top = res.candidates[0]
    assert pytest.approx(top.pixel_x, abs=1.0) == 25.0
    assert pytest.approx(top.pixel_y, abs=1.0) == 25.0
    assert top.snr > 10.0
    assert "data:image/png;base64," in res.diff_image_base64
