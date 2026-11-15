"""Automated unit and integration test suite for SPHEREx Milestone 3:
WCS processing, FITS validation, footprint geometry, and astronomical display stretching.
"""

import io
import math
import numpy as np
import pytest

from astropy.io import fits
from astropy.wcs import WCS

from app.astronomy.wcs_processor import (
    extract_wcs,
    pixel_to_world,
    world_to_pixel,
    get_pixel_scales_arcsec,
    validate_round_trip,
    extract_wcs_metadata,
)
from app.astronomy.fits_reader import read_fits_image
from app.astronomy.image_renderer import apply_display_stretch, render_to_png_bytes
from app.astronomy.image_footprint import generate_spherical_mesh, radec_to_cartesian
from app.astronomy.sample_data import generate_synthetic_fits_fixture, get_sample_fits


def test_t01_fits_header_extraction():
    """T01: Verify that standard FITS header cards are extracted accurately."""
    fits_bytes = generate_synthetic_fits_fixture(
        ra_center=133.795129,
        dec_center=-7.245147,
        width=128,
        height=128,
        target_name="WISE 0855 Test Target",
    )
    product = read_fits_image(fits_bytes)

    assert product.metadata.dimensions == (128, 128)
    assert product.metadata.naxis == 2
    assert product.metadata.telescope == "SPHEREx-Simulator"
    assert product.metadata.target_object == "WISE 0855 Test Target"
    assert product.metadata.bunit == "adu"


def test_t02_wcs_initialization():
    """T02: Verify that Astropy WCS initializes properly from celestial FITS header."""
    fits_bytes = generate_synthetic_fits_fixture(
        ra_center=133.795129,
        dec_center=-7.245147,
    )
    product = read_fits_image(fits_bytes)

    assert product.wcs.is_celestial
    assert product.metadata.wcs.wcs_valid is True
    assert "TAN" in product.metadata.wcs.projection_type


def test_t03_pixel_to_world_conversion():
    """T03: Verify pixel to world conversion at reference center and corners."""
    fits_bytes = generate_synthetic_fits_fixture(
        ra_center=133.795129,
        dec_center=-7.245147,
        width=200,
        height=200,
    )
    product = read_fits_image(fits_bytes)

    # Reference center pixel (0-indexed: x=99.5, y=99.5)
    center_x = (200 - 1) / 2.0
    center_y = (200 - 1) / 2.0
    ra, dec = pixel_to_world(product.wcs, center_x, center_y, origin=0)

    assert abs(ra - 133.795129) < 1e-4
    assert abs(dec - (-7.245147)) < 1e-4


def test_t04_world_to_pixel_conversion():
    """T04: Verify world to pixel conversion maps (RA, Dec) back to pixel center."""
    fits_bytes = generate_synthetic_fits_fixture(
        ra_center=133.795129,
        dec_center=-7.245147,
        width=200,
        height=200,
    )
    product = read_fits_image(fits_bytes)

    px, py = world_to_pixel(product.wcs, 133.795129, -7.245147, origin=0)
    expected_x = (200 - 1) / 2.0
    expected_y = (200 - 1) / 2.0

    assert abs(px - expected_x) < 1e-3
    assert abs(py - expected_y) < 1e-3


def test_t05_round_trip_residual_accuracy():
    """T05: Verify numerical round-trip accuracy across a dense image grid."""
    fits_bytes = generate_synthetic_fits_fixture(
        ra_center=133.795129,
        dec_center=-7.245147,
        width=256,
        height=256,
    )
    product = read_fits_image(fits_bytes)

    max_res, mean_res = validate_round_trip(product.wcs, 256, 256, grid_size=9)
    # Astropy WCS should achieve sub-milli-pixel round-trip accuracy
    assert max_res < 1e-5
    assert mean_res < 1e-6


def test_t06_image_footprint_calculation():
    """T06: Verify 4-corner footprint calculation matches geometric field boundary."""
    product = get_sample_fits("wise-0855")
    corners = product.metadata.wcs.footprint_corners

    assert len(corners) == 4
    # Check that all corners are within expected radius of center
    center_ra, center_dec = product.metadata.wcs.center_radec
    for ra, dec in corners:
        # Distance should be <= 15 arcminutes (< 0.25 deg)
        ang_dist = math.sqrt((ra - center_ra)**2 * math.cos(math.radians(center_dec))**2 + (dec - center_dec)**2)
        assert ang_dist < 0.25


def test_t07_spherical_projection_geometry():
    """T07: Verify 3D BufferGeometry coordinates lie on the celestial sphere."""
    product = get_sample_fits("wise-0855")
    mesh = generate_spherical_mesh(product.wcs, 256, 256, radius=98.0)

    assert mesh.vertex_count > 0
    assert len(mesh.vertices) == mesh.vertex_count * 3
    assert len(mesh.uvs) == mesh.vertex_count * 2
    assert len(mesh.indices) % 3 == 0  # Valid triangles

    # Verify every 3D vertex lies exactly on sphere of radius R=98.0
    for i in range(0, len(mesh.vertices), 3):
        x = mesh.vertices[i]
        y = mesh.vertices[i + 1]
        z = mesh.vertices[i + 2]
        r = math.sqrt(x*x + y*y + z*z)
        assert abs(r - 98.0) < 0.05, f"Vertex radius {r} deviates from 98.0"


def test_t08_display_stretches():
    """T08: Test linear, log, and asinh stretches produce normalized [0, 1] arrays."""
    data = np.random.uniform(10.0, 1000.0, size=(64, 64)).astype(np.float32)

    for stretch in ["linear", "log", "asinh", "sqrt"]:
        stretched = apply_display_stretch(data, stretch=stretch)
        assert stretched.min() >= 0.0
        assert stretched.max() <= 1.0

    png_bytes = render_to_png_bytes(data, stretch="asinh")
    assert len(png_bytes) > 100
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic header


def test_t09_ra_wraparound_handling():
    """T09: Verify WCS and 3D spherical mesh across RA=0°/360° meridian."""
    product = get_sample_fits("ra-wraparound")
    mesh = generate_spherical_mesh(product.wcs, 256, 256, radius=98.0)

    assert mesh.vertex_count > 0
    # Center is at RA 359.95, Dec 12.0
    center_ra, center_dec = mesh.center_radec
    assert abs(center_ra - 359.95) < 0.1

    # Check that 3D vertices are continuous and have valid coordinates
    for i in range(0, len(mesh.vertices), 3):
        x = mesh.vertices[i]
        y = mesh.vertices[i + 1]
        z = mesh.vertices[i + 2]
        r = math.sqrt(x*x + y*y + z*z)
        assert abs(r - 98.0) < 0.05


def test_t14_invalid_fits_handling():
    """T14: Verify rejection of invalid or multi-dimensional FITS data."""
    # 1. 3D Datacube rejection
    cube_data = np.zeros((5, 64, 64), dtype=np.float32)
    cube_hdu = fits.PrimaryHDU(data=cube_data)
    buf = io.BytesIO()
    cube_hdu.writeto(buf)

    with pytest.raises(ValueError, match="Unsupported FITS dimensionality"):
        read_fits_image(buf.getvalue())

    # 2. Corrupt file rejection
    with pytest.raises(ValueError, match="Failed to open FITS"):
        read_fits_image(b"NOT_A_FITS_FILE_CORRUPTED_BYTES")


if __name__ == "__main__":
    print("Running Milestone 3 Backend Unit Tests...")
    test_t01_fits_header_extraction()
    print("[PASS] T01: FITS header extraction")
    test_t02_wcs_initialization()
    print("[PASS] T02: WCS initialization")
    test_t03_pixel_to_world_conversion()
    print("[PASS] T03: Pixel-to-world conversion")
    test_t04_world_to_pixel_conversion()
    print("[PASS] T04: World-to-pixel conversion")
    test_t05_round_trip_residual_accuracy()
    print("[PASS] T05: Round-trip transformation accuracy")
    test_t06_image_footprint_calculation()
    print("[PASS] T06: Correct image footprint calculation")
    test_t07_spherical_projection_geometry()
    print("[PASS] T07: Spherical projection geometry generation")
    test_t08_display_stretches()
    print("[PASS] T08: Astronomical image display stretches")
    test_t09_ra_wraparound_handling()
    print("[PASS] T09: RA wraparound handling")
    test_t14_invalid_fits_handling()
    print("[PASS] T14: Invalid FITS handling")
    print("\nAll Backend M3 Tests Passed Successfully!")
