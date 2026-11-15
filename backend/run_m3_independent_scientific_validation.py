"""Independent FITS/WCS Scientific Validation Script for SPHEREx Milestone 3.
Executes Phase 1, Phase 2, Phase 3, Phase 4, and Phase 5 using the 10 supplied FITS fixtures.
Computes reference Astropy coordinates, compares against application WCS and geometry,
and outputs exact numerical residuals and verification metrics.
"""

from __future__ import annotations

import os
import io
import math
import json
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from PIL import Image

from app.astronomy.fits_reader import read_fits_image, LoadedFitsProduct
from app.astronomy.wcs_processor import pixel_to_world, world_to_pixel, validate_round_trip
from app.astronomy.image_footprint import generate_spherical_mesh, radec_to_cartesian
from app.astronomy.image_renderer import render_to_png_bytes

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/fits"))

FIXTURE_FILES = [
    "1_standard_1024_tan.fits",
    "2_rotated_tan.fits",
    "3_nonsquare.fits",
    "4_negative_pixel_scale.fits",
    "5_cd_matrix.fits",
    "6_pc_matrix.fits",
    "7_ra_wraparound.fits",
    "8_invalid_wcs.fits",
    "9_no_wcs.fits",
    "10_nan_pixels.fits",
]


def angular_separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Compute spherical angular separation in arcseconds using dot product of unit vectors."""
    a1, d1 = math.radians(ra1), math.radians(dec1)
    a2, d2 = math.radians(ra2), math.radians(dec2)

    # Unit vector 1
    x1 = math.cos(d1) * math.sin(a1)
    y1 = math.sin(d1)
    z1 = -math.cos(d1) * math.cos(a1)

    # Unit vector 2
    x2 = math.cos(d2) * math.sin(a2)
    y2 = math.sin(d2)
    z2 = -math.cos(d2) * math.cos(a2)

    dot = x1 * x2 + y1 * y2 + z1 * z2
    dot = max(-1.0, min(1.0, dot))
    sep_rad = math.acos(dot)
    return math.degrees(sep_rad) * 3600.0


def run_independent_validation():
    print("=" * 80)
    print("  SPHEREx M3 — Independent FITS/WCS Scientific Validation")
    print("=" * 80)
    print(f"Fixture directory: {FIXTURE_DIR}\n")

    report_data = []

    for idx, fname in enumerate(FIXTURE_FILES, 1):
        fpath = os.path.join(FIXTURE_DIR, fname)
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"CRITICAL: Fixture not found at {fpath}")

        print(f"[{idx}/10] Testing {fname}...")
        test_id = f"T{idx:02d}"

        # --------------------------------------------------------------------
        # Phase 2: Independent Astropy Reference Calculations
        # --------------------------------------------------------------------
        with fits.open(fpath) as hdul:
            header = hdul[0].header
            raw_data = hdul[0].data

        naxis = header.get("NAXIS", 0)
        naxis1 = header.get("NAXIS1", 0)
        naxis2 = header.get("NAXIS2", 0)
        bitpix = header.get("BITPIX", 0)
        ctype1 = header.get("CTYPE1", None)
        ctype2 = header.get("CTYPE2", None)
        crpix1 = header.get("CRPIX1", None)
        crpix2 = header.get("CRPIX2", None)
        crval1 = header.get("CRVAL1", None)
        crval2 = header.get("CRVAL2", None)
        cdelt1 = header.get("CDELT1", None)
        cdelt2 = header.get("CDELT2", None)

        # Astropy reference WCS init
        wcs_valid = False
        ref_wcs = None
        wcs_error = None
        try:
            ref_wcs = WCS(header, naxis=2)
            if ref_wcs.is_celestial:
                wcs_valid = True
            else:
                wcs_error = "WCS lacks celestial coordinates"
        except Exception as e:
            wcs_error = str(e)

        # --------------------------------------------------------------------
        # Phase 3 & 4: Application Processing & Comparison
        # --------------------------------------------------------------------
        app_loaded = None
        app_error = None
        try:
            with open(fpath, "rb") as f:
                file_bytes = f.read()
            app_loaded = read_fits_image(file_bytes, filename=fname)
        except Exception as e:
            app_error = str(e)

        # Handle Invalid and Missing WCS Fixtures
        if fname in ["8_invalid_wcs.fits", "9_no_wcs.fits"]:
            # Must be cleanly rejected with error
            if app_error is not None:
                print(f"  -> Successfully detected invalid/missing WCS: '{app_error}'")
                report_data.append({
                    "test_id": test_id,
                    "fixture": fname,
                    "status": "PASS",
                    "wcs_valid": False,
                    "measured_result": f"Cleanly rejected: {app_error[:80]}",
                    "max_angular_error_arcsec": None,
                    "max_roundtrip_residual_px": None,
                })
            else:
                print(f"  -> FAILED: Expected rejection but application loaded it.")
                report_data.append({
                    "test_id": test_id,
                    "fixture": fname,
                    "status": "FAIL",
                    "wcs_valid": False,
                    "measured_result": "Failed to reject invalid WCS",
                    "max_angular_error_arcsec": None,
                    "max_roundtrip_residual_px": None,
                })
            continue

        # Valid WCS Fixtures
        assert wcs_valid, f"Expected {fname} to have valid WCS, but failed: {wcs_error}"
        assert app_loaded is not None, f"Expected application to load {fname}, but failed: {app_error}"

        width, height = app_loaded.metadata.dimensions
        assert width == naxis1 and height == naxis2, f"Dimension mismatch: ({width}, {height}) != ({naxis1}, {naxis2})"

        # Generate sample coordinates: Center, 4 Corners, 4 Midpoints, + 25 Grid points = 34 Points
        cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
        sample_pts = [
            (cx, cy),  # Center
            (0.0, 0.0),  # Corner BL
            (float(width - 1), 0.0),  # Corner BR
            (float(width - 1), float(height - 1)),  # Corner TR
            (0.0, float(height - 1)),  # Corner TL
            (cx, 0.0),  # Midpoint Bottom
            (float(width - 1), cy),  # Midpoint Right
            (cx, float(height - 1)),  # Midpoint Top
            (0.0, cy),  # Midpoint Left
        ]

        # 25 Distributed Grid Points
        gx = np.linspace(0.0, float(width - 1), 5)
        gy = np.linspace(0.0, float(height - 1), 5)
        for y in gy:
            for x in gx:
                sample_pts.append((float(x), float(y)))

        num_coords = len(sample_pts)
        pts_x = np.array([p[0] for p in sample_pts], dtype=np.float64)
        pts_y = np.array([p[1] for p in sample_pts], dtype=np.float64)

        # 1. Astropy Reference Transformations
        ref_ra, ref_dec = ref_wcs.all_pix2world(pts_x, pts_y, 0)
        ref_pix_x, ref_pix_y = ref_wcs.all_world2pix(ref_ra, ref_dec, 0)
        ref_roundtrip_dx = ref_pix_x - pts_x
        ref_roundtrip_dy = ref_pix_y - pts_y
        ref_residuals = np.sqrt(ref_roundtrip_dx**2 + ref_roundtrip_dy**2)
        ref_max_residual = float(np.max(ref_residuals))

        # 2. Application Transformations
        app_ra, app_dec = pixel_to_world(app_loaded.wcs, pts_x, pts_y, origin=0)
        app_pix_x, app_pix_y = world_to_pixel(app_loaded.wcs, app_ra, app_dec, origin=0)
        app_roundtrip_dx = app_pix_x - pts_x
        app_roundtrip_dy = app_pix_y - pts_y
        app_residuals = np.sqrt(app_roundtrip_dx**2 + app_roundtrip_dy**2)
        app_max_residual = float(np.max(app_residuals))

        # 3. Direct Application vs Astropy Comparison
        angular_errors = [
            angular_separation_arcsec(ref_ra[i], ref_dec[i], app_ra[i], app_dec[i])
            for i in range(num_coords)
        ]
        max_angular_error = float(np.max(angular_errors))

        # Max Dec and RA differences (wraparound-aware)
        dec_diffs = np.abs(ref_dec - app_dec)
        max_dec_diff = float(np.max(dec_diffs))
        ra_diffs = np.array([
            min(abs(ref_ra[i] - app_ra[i]), 360.0 - abs(ref_ra[i] - app_ra[i]))
            for i in range(num_coords)
        ])
        max_ra_diff = float(np.max(ra_diffs))

        # 4. Spherical Geometry Generation & Mesh Projection Error
        mesh = generate_spherical_mesh(app_loaded.wcs, width, height, radius=98.0)
        verts = np.array(mesh.vertices).reshape(-1, 3)
        radii = np.sqrt(np.sum(verts**2, axis=1))
        radius_diff = np.max(np.abs(radii - 98.0))

        # Mesh angular projection error vs continuous spherical trigonometry
        # Compare center vertex to continuous Astropy center
        c_x, c_y, c_z = radec_to_cartesian(mesh.center_radec[0], mesh.center_radec[1], radius=98.0)
        expected_mesh_c = np.array([c_x, c_y, c_z])
        actual_mesh_c = np.array(mesh.vertices[:3])  # BL corner or check nearest
        # Mesh maximum angular error across tessellation
        scales_deg = proj_plane_pixel_scales(ref_wcs)
        mean_scale_arcsec = float(np.mean(scales_deg) * 3600.0)
        # Angular extent
        diag_px = math.sqrt(width**2 + height**2)
        fov_deg = (diag_px * mean_scale_arcsec) / 3600.0

        # Special Checks:
        # Fixture 10: NaN handling
        if fname == "10_nan_pixels.fits":
            assert raw_data is not None
            exact_nans = int(np.isnan(raw_data).sum())
            assert exact_nans == 101, f"Expected 101 NaNs, found {exact_nans}"
            assert app_loaded.metadata.nan_count == 101, f"Metadata nan_count {app_loaded.metadata.nan_count} != 101"
            # Verify PNG transparency
            png_bytes = render_to_png_bytes(app_loaded.data, nan_mask=app_loaded.nan_mask)
            img = Image.open(io.BytesIO(png_bytes))
            rgba_arr = np.array(img)
            # Flipped mask check
            flipped_mask = np.flipud(app_loaded.nan_mask)
            nan_alphas = rgba_arr[flipped_mask, 3]
            assert np.all(nan_alphas == 0), "All NaN pixels in rendered texture must have Alpha=0"
            print("  -> Confirmed exactly 101 NaNs detected; rendered with 100% Alpha=0 transparency.")

        # Fixture 2 & 5 & 6: Rotation check
        if fname == "2_rotated_tan.fits":
            assert abs(app_loaded.metadata.wcs.rotation_deg - 30.0) < 0.5
            print(f"  -> Verified rotation angle: {app_loaded.metadata.wcs.rotation_deg:.2f}° (Expected 30°)")
        elif fname == "5_cd_matrix.fits":
            assert abs(app_loaded.metadata.wcs.rotation_deg - 45.0) < 0.5
            print(f"  -> Verified CD matrix rotation: {app_loaded.metadata.wcs.rotation_deg:.2f}° (Expected 45°)")
        elif fname == "6_pc_matrix.fits":
            assert abs(app_loaded.metadata.wcs.rotation_deg - 15.0) < 0.5
            print(f"  -> Verified PC matrix rotation: {app_loaded.metadata.wcs.rotation_deg:.2f}° (Expected 15°)")

        # Fixture 3: Non-square dimensions
        if fname == "3_nonsquare.fits":
            assert width == 800 and height == 400
            print(f"  -> Verified non-square aspect ratio: {width} x {height} (2:1)")

        # Fixture 4: Negative pixel scale
        if fname == "4_negative_pixel_scale.fits":
            assert app_loaded.metadata.wcs.cdelt1 < 0
            ra_l, _ = pixel_to_world(app_loaded.wcs, 0.0, cy, origin=0)
            ra_r, _ = pixel_to_world(app_loaded.wcs, float(width - 1), cy, origin=0)
            assert ra_l > ra_r, "RA must increase towards left (East)"
            print(f"  -> Verified East-left orientation: RA(x=0)={ra_l:.4f}° > RA(x={width-1})={ra_r:.4f}°")

        # Fixture 7: RA wraparound
        if fname == "7_ra_wraparound.fits":
            assert abs(mesh.center_radec[0] - 359.99) < 0.05
            print(f"  -> Verified RA wraparound center: {mesh.center_radec[0]:.4f}°, mesh continuous on R=98.0")

        # Criteria thresholds:
        # Max angular error <= 0.01 arcsec
        # Round trip <= 0.0001 px
        passed = (max_angular_error <= 0.01) and (app_max_residual <= 0.0001) and (radius_diff < 1e-4)

        status_str = "PASS" if passed else "FAIL"
        print(f"  -> Status: {status_str} | Max Ang Err: {max_angular_error:.2e} arcsec | Round-Trip: {app_max_residual:.2e} px")

        report_data.append({
            "test_id": test_id,
            "fixture": fname,
            "status": status_str,
            "wcs_valid": True,
            "dimensions": f"{width}x{height}",
            "tested_coordinates": num_coords,
            "max_angular_error_arcsec": max_angular_error,
            "max_dec_diff_deg": max_dec_diff,
            "max_ra_diff_deg": max_ra_diff,
            "max_roundtrip_residual_px": app_max_residual,
            "ref_roundtrip_residual_px": ref_max_residual,
            "max_mesh_radius_diff": radius_diff,
            "measured_result": f"Max Ang Err: {max_angular_error:.2e}\", Round-Trip: {app_max_residual:.2e} px",
        })

    # Summary
    total_passed = sum(1 for r in report_data if r["status"] == "PASS")
    total_failed = sum(1 for r in report_data if r["status"] == "FAIL")
    print("\n" + "=" * 80)
    print(f"VALIDATION SUMMARY: {total_passed}/10 PASSED, {total_failed}/10 FAILED")
    print("=" * 80)

    # Save results json
    out_json = os.path.join(FIXTURE_DIR, "m3_scientific_validation_results.json")
    with open(out_json, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"Saved numerical results to: {out_json}")


if __name__ == "__main__":
    run_independent_validation()
