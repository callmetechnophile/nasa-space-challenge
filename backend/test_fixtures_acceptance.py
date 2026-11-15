"""Acceptance Test Suite for 10 Deterministic Synthetic FITS Fixtures.
Validates all 10 fixtures required by SPHEREx M3 Step 2 & Step 4:
1. Standard 1024 x 1024 TAN projection
2. Rotated TAN projection (30 deg)
3. Non-square image (800 x 400)
4. Negative pixel-scale image (CDELT1 < 0)
5. Image using CD matrix (45 deg)
6. Image using PC matrix (15 deg)
7. RA wraparound image near 359.99 deg
8. FITS file with invalid WCS (clean rejection)
9. FITS file without WCS (clean rejection)
10. FITS file containing NaN/Inf pixels (sanitization & rendering)
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from app.astronomy.fits_reader import read_fits_image
from app.astronomy.wcs_processor import (
    pixel_to_world,
    world_to_pixel,
    validate_round_trip,
    get_pixel_scales_arcsec,
)
from app.astronomy.image_footprint import generate_spherical_mesh
from app.astronomy.image_renderer import render_to_data_uri
from app.astronomy.test_fixtures import (
    create_fixture_1_standard_1024_tan,
    create_fixture_2_rotated_tan,
    create_fixture_3_nonsquare,
    create_fixture_4_negative_pixel_scale,
    create_fixture_5_cd_matrix,
    create_fixture_6_pc_matrix,
    create_fixture_7_ra_wraparound,
    create_fixture_8_invalid_wcs,
    create_fixture_9_no_wcs,
    create_fixture_10_nan_pixels,
)


def test_fixture_1_standard_1024_tan():
    """1. Standard 1024 x 1024 TAN projection fixture."""
    fits_bytes = create_fixture_1_standard_1024_tan()
    loaded = read_fits_image(fits_bytes, "fixture_1.fits")

    assert loaded.metadata.dimensions == (1024, 1024)
    assert loaded.metadata.wcs.projection_type == "TAN"
    assert abs(loaded.metadata.wcs.crval1 - 180.0) < 1e-5
    assert abs(loaded.metadata.wcs.crval2 - 20.0) < 1e-5
    assert abs(loaded.metadata.wcs.pixel_scale_arcsec - 1.0) < 1e-2

    # Numerical Round-trip validation across 1024x1024
    max_res, mean_res = validate_round_trip(loaded.wcs, 1024, 1024, grid_size=9)
    assert max_res < 0.0001, f"Round trip residual {max_res} px must be < 0.0001 px"
    print(f"[PASS] Fixture 1: Standard 1024x1024 TAN - Round-trip max residual: {max_res:.2e} px")


def test_fixture_2_rotated_tan():
    """2. Rotated TAN projection (30 deg)."""
    fits_bytes = create_fixture_2_rotated_tan()
    loaded = read_fits_image(fits_bytes, "fixture_2.fits")

    assert loaded.metadata.dimensions == (512, 512)
    assert abs(loaded.metadata.wcs.rotation_deg - 30.0) < 0.5
    assert abs(loaded.metadata.wcs.pixel_scale_arcsec - 2.0) < 1e-2

    max_res, _ = validate_round_trip(loaded.wcs, 512, 512, grid_size=9)
    assert max_res < 0.0001
    print(f"[PASS] Fixture 2: Rotated TAN (30 deg) - Round-trip max residual: {max_res:.2e} px")


def test_fixture_3_nonsquare():
    """3. Non-square image (800 x 400)."""
    fits_bytes = create_fixture_3_nonsquare()
    loaded = read_fits_image(fits_bytes, "fixture_3.fits")

    assert loaded.metadata.dimensions == (800, 400)
    assert abs(loaded.metadata.wcs.crval1 - 45.0) < 1e-5
    assert abs(loaded.metadata.wcs.crval2 - 30.0) < 1e-5

    max_res, _ = validate_round_trip(loaded.wcs, 800, 400, grid_size=9)
    assert max_res < 0.0001
    print(f"[PASS] Fixture 3: Non-square (800x400) - Round-trip max residual: {max_res:.2e} px")


def test_fixture_4_negative_pixel_scale():
    """4. Negative pixel-scale image (CDELT1 < 0)."""
    fits_bytes = create_fixture_4_negative_pixel_scale()
    loaded = read_fits_image(fits_bytes, "fixture_4.fits")

    assert loaded.metadata.wcs.cdelt1 is not None and loaded.metadata.wcs.cdelt1 < 0
    assert loaded.metadata.wcs.cdelt2 is not None and loaded.metadata.wcs.cdelt2 > 0

    # East-left test: Pixel at x=0 should have HIGHER RA than pixel at x=511
    ra_left, _ = pixel_to_world(loaded.wcs, 0.0, 255.5)
    ra_right, _ = pixel_to_world(loaded.wcs, 511.0, 255.5)
    assert ra_left > ra_right, "RA must increase toward the left (East)"

    max_res, _ = validate_round_trip(loaded.wcs, 512, 512)
    assert max_res < 0.0001
    print(f"[PASS] Fixture 4: Negative pixel-scale - Round-trip max residual: {max_res:.2e} px")


def test_fixture_5_cd_matrix():
    """5. Image using CD matrix (45 deg)."""
    fits_bytes = create_fixture_5_cd_matrix()
    loaded = read_fits_image(fits_bytes, "fixture_5.fits")

    assert "CD1_1" in loaded.header, "FITS header must contain CD1_1 card"
    assert abs(loaded.metadata.wcs.rotation_deg - 45.0) < 0.5
    assert abs(loaded.metadata.wcs.pixel_scale_arcsec - 2.5) < 1e-2

    max_res, _ = validate_round_trip(loaded.wcs, 512, 512)
    assert max_res < 0.0001
    print(f"[PASS] Fixture 5: CD Matrix - Round-trip max residual: {max_res:.2e} px")


def test_fixture_6_pc_matrix():
    """6. Image using PC matrix (15 deg)."""
    fits_bytes = create_fixture_6_pc_matrix()
    loaded = read_fits_image(fits_bytes, "fixture_6.fits")

    assert "PC1_1" in loaded.header or "PC1_1" in [k.strip() for k in loaded.header.keys()]
    assert abs(loaded.metadata.wcs.rotation_deg - 15.0) < 0.5

    max_res, _ = validate_round_trip(loaded.wcs, 512, 512)
    assert max_res < 0.0001
    print(f"[PASS] Fixture 6: PC Matrix - Round-trip max residual: {max_res:.2e} px")


def test_fixture_7_ra_wraparound():
    """7. RA wraparound image near 359.99 deg."""
    fits_bytes = create_fixture_7_ra_wraparound()
    loaded = read_fits_image(fits_bytes, "fixture_7.fits")

    mesh = generate_spherical_mesh(loaded.wcs, 512, 512, radius=98.0)
    assert mesh.vertex_count > 0
    assert len(mesh.indices) % 3 == 0

    # Ensure no vertex radius deviates from 98.0
    verts = np.array(mesh.vertices).reshape(-1, 3)
    radii = np.sqrt(np.sum(verts**2, axis=1))
    assert np.allclose(radii, 98.0, atol=1e-3)
    print(f"[PASS] Fixture 7: RA Wraparound - Spherical mesh generated with {mesh.vertex_count} vertices on R=98.0")


def test_fixture_8_invalid_wcs():
    """8. FITS file with invalid WCS is rejected."""
    fits_bytes = create_fixture_8_invalid_wcs()
    with pytest.raises(ValueError, match="Failed to initialize WCS|does not contain valid celestial"):
        read_fits_image(fits_bytes, "fixture_8.fits")
    print("[PASS] Fixture 8: Invalid WCS cleanly rejected")


def test_fixture_9_no_wcs():
    """9. FITS file completely lacking WCS metadata is rejected."""
    fits_bytes = create_fixture_9_no_wcs()
    with pytest.raises(ValueError, match="Failed to initialize WCS|does not contain valid celestial"):
        read_fits_image(fits_bytes, "fixture_9.fits")
    print("[PASS] Fixture 9: Missing WCS cleanly rejected")


def test_fixture_10_nan_pixels():
    """10. FITS file containing NaN and Inf pixels is sanitized."""
    fits_bytes = create_fixture_10_nan_pixels()
    loaded = read_fits_image(fits_bytes, "fixture_10.fits")

    assert not np.isnan(loaded.data).any(), "NaNs must be sanitized"
    assert not np.isinf(loaded.data).any(), "Infs must be sanitized"

    uri = render_to_data_uri(loaded.data, stretch="asinh")
    assert uri.startswith("data:image/png;base64,")
    print(f"[PASS] Fixture 10: NaN/Inf pixels sanitized cleanly; base64 PNG rendered ({len(uri)} chars)")
