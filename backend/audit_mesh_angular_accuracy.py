"""Independent Scientific Audit: Spherical Mesh Angular Accuracy.
Evaluates at least 100 distributed image pixel positions per valid fixture,
computes reference RA/Dec using first-principles Calabretta & Greisen 2002 equations,
interpolates generated Three.js BufferGeometry coordinates,
de-projects back to RA/Dec using the application coordinate convention,
and reports Maximum Angular Error, RMS Angular Error, Radial Error, and UV Error.
"""

from __future__ import annotations

import os
import math
import json
import numpy as np
from astropy.io import fits

from app.astronomy.image_footprint import generate_spherical_mesh
from app.astronomy.fits_reader import read_fits_image

FIXTURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/fits"))

VALID_FIXTURES = [
    "1_standard_1024_tan.fits",
    "2_rotated_tan.fits",
    "3_nonsquare.fits",
    "4_negative_pixel_scale.fits",
    "5_cd_matrix.fits",
    "6_pc_matrix.fits",
    "7_ra_wraparound.fits",
    "10_nan_pixels.fits",
]


def first_principles_pix2world(hdr: fits.Header, x: float, y: float) -> tuple[float, float]:
    """Independent first-principles Gnomonic (TAN) transformation."""
    crpix1 = hdr["CRPIX1"] - 1.0
    crpix2 = hdr["CRPIX2"] - 1.0
    p1 = x - crpix1
    p2 = y - crpix2

    if "CD1_1" in hdr:
        xi = hdr["CD1_1"] * p1 + hdr.get("CD1_2", 0.0) * p2
        eta = hdr.get("CD2_1", 0.0) * p1 + hdr["CD2_2"] * p2
    elif "PC1_1" in hdr and "CDELT1" in hdr:
        cdelt1, cdelt2 = hdr["CDELT1"], hdr["CDELT2"]
        xi = cdelt1 * (hdr["PC1_1"] * p1 + hdr.get("PC1_2", 0.0) * p2)
        eta = cdelt2 * (hdr.get("PC2_1", 0.0) * p1 + hdr["PC2_2"] * p2)
    elif "CDELT1" in hdr:
        xi = hdr["CDELT1"] * p1
        eta = hdr["CDELT2"] * p2
    else:
        raise ValueError("No linear transformation matrix cards found in FITS header")

    R_deg = math.hypot(xi, eta)
    if R_deg == 0:
        return hdr["CRVAL1"] % 360.0, hdr["CRVAL2"]

    theta = math.atan2(1.0, math.radians(R_deg))
    phi = math.atan2(xi, -eta)

    a0 = math.radians(hdr["CRVAL1"])
    d0 = math.radians(hdr["CRVAL2"])
    phip = math.radians(hdr.get("LONPOLE", 180.0))

    dphi = phi - phip
    sin_d = math.sin(theta) * math.sin(d0) + math.cos(theta) * math.cos(d0) * math.cos(dphi)
    d = math.asin(max(-1.0, min(1.0, sin_d)))

    den = math.sin(theta) * math.cos(d0) - math.cos(theta) * math.sin(d0) * math.cos(dphi)
    num = -math.cos(theta) * math.sin(dphi)
    da = math.atan2(num, den)
    a = (a0 + da) % (2.0 * math.pi)

    return math.degrees(a) % 360.0, math.degrees(d)


def interpolate_mesh(mesh, u: float, v: float):
    """Interpolate 3D position and UV within generated spherical mesh."""
    nx = mesh.grid_density_x
    ny = mesh.grid_density_y
    stride = nx + 1
    verts = np.array(mesh.vertices).reshape(-1, 3)
    uvs = np.array(mesh.uvs).reshape(-1, 2)

    gx = u * nx
    gy = v * ny
    i = min(int(math.floor(gx)), nx - 1)
    j = min(int(math.floor(gy)), ny - 1)
    s = gx - i
    t = gy - j

    # Bilinear interpolation across cell vertices
    v00 = verts[j * stride + i]
    v10 = verts[j * stride + (i + 1)]
    v01 = verts[(j + 1) * stride + i]
    v11 = verts[(j + 1) * stride + (i + 1)]

    interp_pos = (1 - s) * (1 - t) * v00 + s * (1 - t) * v10 + (1 - s) * t * v01 + s * t * v11

    u00 = uvs[j * stride + i]
    u10 = uvs[j * stride + (i + 1)]
    u01 = uvs[(j + 1) * stride + i]
    u11 = uvs[(j + 1) * stride + (i + 1)]
    interp_uv = (1 - s) * (1 - t) * u00 + s * (1 - t) * u10 + (1 - s) * t * u01 + s * t * u11

    return interp_pos, interp_uv


def run_mesh_accuracy_audit():
    print("=" * 85)
    print("  SPHEREx M3 — Spherical Mesh Angular Accuracy Independent Audit")
    print("=" * 85)

    results = []

    for fname in VALID_FIXTURES:
        fpath = os.path.join(FIXTURE_DIR, fname)
        with fits.open(fpath) as hdul:
            hdr = hdul[0].header

        w_px = hdr["NAXIS1"]
        h_px = hdr["NAXIS2"]

        with open(fpath, "rb") as fp:
            loaded = read_fits_image(fp.read(), filename=fname)

        mesh = generate_spherical_mesh(loaded.wcs, w_px, h_px, radius=98.0)

        # 121 sample points: 11 x 11 regular grid across detector (exceeds 100 requirement)
        xs = np.linspace(0.0, float(w_px - 1), 11)
        ys = np.linspace(0.0, float(h_px - 1), 11)

        ang_errs = []
        rad_errs = []
        uv_errs = []

        for y in ys:
            for x in xs:
                # 1. First-principles ground truth
                ra_ref, dec_ref = first_principles_pix2world(hdr, x, y)

                # 2. Interpolate mesh in 3D
                u = x / (w_px - 1)
                v = y / (h_px - 1)
                pos, uv_interp = interpolate_mesh(mesh, u, v)

                # 3. Radial error
                r_calc = float(np.linalg.norm(pos))
                rad_errs.append(abs(r_calc - 98.0))

                # 4. UV error
                uv_errs.append(math.hypot(uv_interp[0] - u, uv_interp[1] - v))

                # 5. De-project 3D mesh position back to RA/Dec
                # Application convention: +Y = NCP, -Y = SCP, -Z = RA 0 Dec 0, +X = RA 90 Dec 0
                dec_m = math.degrees(math.asin(max(-1.0, min(1.0, pos[1] / r_calc))))
                ra_m = math.degrees(math.atan2(pos[0], -pos[2])) % 360.0

                # 6. Angular separation (numerically stable vector method)
                u_ref = np.array([
                    math.cos(math.radians(dec_ref)) * math.cos(math.radians(ra_ref)),
                    math.cos(math.radians(dec_ref)) * math.sin(math.radians(ra_ref)),
                    math.sin(math.radians(dec_ref))
                ], dtype=np.float64)
                u_ref = u_ref / np.linalg.norm(u_ref)

                u_mesh = np.array([
                    math.cos(math.radians(dec_m)) * math.cos(math.radians(ra_m)),
                    math.cos(math.radians(dec_m)) * math.sin(math.radians(ra_m)),
                    math.sin(math.radians(dec_m))
                ], dtype=np.float64)
                u_mesh = u_mesh / np.linalg.norm(u_mesh)

                cross_norm = float(np.linalg.norm(np.cross(u_ref, u_mesh)))
                dot_val = float(np.dot(u_ref, u_mesh))
                sep_arcsec = math.degrees(math.atan2(cross_norm, dot_val)) * 3600.0
                ang_errs.append(sep_arcsec)

        max_ang = float(np.max(ang_errs))
        rms_ang = float(math.sqrt(np.mean(np.array(ang_errs) ** 2)))
        max_rad = float(np.max(rad_errs))
        max_uv = float(np.max(uv_errs))

        # Check thresholds
        # Note: Planar interpolation across 8 subdivisions on an astronomical patch introduces sagitta
        # sub-pixel tessellation error. Detector pixel size is ~ 1.0 to 3.0 arcsec.
        # Max angular error should be sub-pixel (< 0.05 arcseconds).
        status_str = "PASS" if max_ang < 0.05 else "FAIL"

        print(f"[{status_str}] {fname:<28s} | Tested: 121 pts | MaxAng: {max_ang:7.4f}\" | RMSAng: {rms_ang:7.4f}\" | MaxRad: {max_rad:7.5f} | MaxUV: {max_uv:7.2e}")

        results.append({
            "fixture": fname,
            "status": status_str,
            "tested_points": len(ang_errs),
            "max_angular_error_arcsec": max_ang,
            "rms_angular_error_arcsec": rms_ang,
            "max_radial_error_units": max_rad,
            "max_uv_error": max_uv,
            "grid_density": f"{mesh.grid_density_x}x{mesh.grid_density_y}",
        })

    out_file = os.path.join(FIXTURE_DIR, "m3_mesh_accuracy_audit_results.json")
    with open(out_file, "w") as fp:
        json.dump(results, fp, indent=2)
    print("=" * 85)
    print(f"Results saved to: {out_file}\n")
    return results


if __name__ == "__main__":
    run_mesh_accuracy_audit()
