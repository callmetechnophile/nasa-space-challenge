"""First-Principles Independent WCS Audit for SPHEREx Milestone 3.
Implements Calabretta & Greisen (2002) TAN projection equations completely from
scratch without invoking Astropy's WCS transformation methods.

Uses numerically stable great-circle angular separation via 3D unit vectors:
atan2(norm(cross(u1, u2)), dot(u1, u2))
and compares against the legacy acos(dot) method to quantify numerical precision differences.
"""

from __future__ import annotations

import os
import math
import json
import numpy as np
from astropy.io import fits

from app.astronomy.fits_reader import read_fits_image
from app.astronomy.wcs_processor import pixel_to_world

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


def unit_vector(ra_deg: float, dec_deg: float) -> np.ndarray:
    """Convert RA and Dec (in degrees) to a 3D unit vector on the sphere."""
    ra_rad = math.radians(ra_deg)
    dec_rad = math.radians(dec_deg)
    vec = np.array([
        math.cos(dec_rad) * math.cos(ra_rad),
        math.cos(dec_rad) * math.sin(ra_rad),
        math.sin(dec_rad)
    ], dtype=np.float64)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0.0 else vec


def stable_angular_separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Numerically stable great-circle separation using normalized unit vectors:
    atan2(norm(cross(u1, u2)), dot(u1, u2))
    Globally well-conditioned across all angular scales down to machine epsilon.
    """
    u1 = unit_vector(ra1, dec1)
    u2 = unit_vector(ra2, dec2)
    cross_norm = float(np.linalg.norm(np.cross(u1, u2)))
    dot_val = float(np.dot(u1, u2))
    return math.degrees(math.atan2(cross_norm, dot_val)) * 3600.0


def legacy_acos_angular_separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Legacy spherical law of cosines separation: acos(dot).
    Suffers from catastrophic floating-point cancellation near dot = 1.0.
    """
    a1, d1 = math.radians(ra1), math.radians(dec1)
    a2, d2 = math.radians(ra2), math.radians(dec2)
    dot = math.cos(d1) * math.cos(d2) * math.cos(a1 - a2) + math.sin(d1) * math.sin(d2)
    return math.degrees(math.acos(max(-1.0, min(1.0, dot)))) * 3600.0


def first_principles_tan_pix2world(hdr: fits.Header, x: float, y: float) -> tuple[float, float]:
    """Calculate celestial coordinates (RA, Dec in degrees) from first principles
    according to Calabretta & Greisen (2002) Gnomonic (TAN) equations.
    
    Pixel coordinate convention: 0-based index (origin=0), matching application convention.
    FITS CRPIX is 1-based, so intermediate pixel coordinates are:
      p1 = x - (CRPIX1 - 1.0)
      p2 = y - (CRPIX2 - 1.0)
    """
    crpix1 = hdr["CRPIX1"] - 1.0
    crpix2 = hdr["CRPIX2"] - 1.0
    p1 = x - crpix1
    p2 = y - crpix2

    # Linear transformation to intermediate world coordinates (xi, eta) in degrees:
    # Case A: Explicit CD matrix (CDi_j)
    if "CD1_1" in hdr:
        cd11 = hdr["CD1_1"]
        cd12 = hdr.get("CD1_2", 0.0)
        cd21 = hdr.get("CD2_1", 0.0)
        cd22 = hdr["CD2_2"]
        xi = cd11 * p1 + cd12 * p2
        eta = cd21 * p1 + cd22 * p2
    # Case B: PC matrix with separate CDELT (CDELTi * PCi_j)
    elif "PC1_1" in hdr and "CDELT1" in hdr:
        cdelt1 = hdr["CDELT1"]
        cdelt2 = hdr["CDELT2"]
        pc11 = hdr["PC1_1"]
        pc12 = hdr.get("PC1_2", 0.0)
        pc21 = hdr.get("PC2_1", 0.0)
        pc22 = hdr["PC2_2"]
        xi = cdelt1 * (pc11 * p1 + pc12 * p2)
        eta = cdelt2 * (pc21 * p1 + pc22 * p2)
    # Case C: Diagonal CDELT without rotation
    elif "CDELT1" in hdr:
        cdelt1 = hdr["CDELT1"]
        cdelt2 = hdr.get("CDELT2", abs(cdelt1))
        xi = cdelt1 * p1
        eta = cdelt2 * p2
    else:
        raise ValueError("Header contains no linear transformation cards (CD, PC, or CDELT)")

    # Gnomonic (TAN) projection to native spherical coordinates (phi, theta)
    R_deg = math.hypot(xi, eta)
    if R_deg == 0.0:
        return hdr["CRVAL1"] % 360.0, hdr["CRVAL2"]

    theta = math.atan2(1.0, math.radians(R_deg))
    phi = math.atan2(xi, -eta)

    # Native to celestial coordinate rotation (Euler angles) around fiducial point
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

    ra_deg = (math.degrees(a)) % 360.0
    dec_deg = math.degrees(d)

    return ra_deg, dec_deg


def run_first_principles_audit():
    print("=" * 105)
    print("  SPHEREx M3 — Independent First-Principles WCS Audit (Numerically Stable Vector Separation)")
    print("=" * 105)

    results = []

    for fname in VALID_FIXTURES:
        fpath = os.path.join(FIXTURE_DIR, fname)
        with fits.open(fpath) as hdul:
            hdr = hdul[0].header

        w_px = int(hdr["NAXIS1"])
        h_px = int(hdr["NAXIS2"])

        with open(fpath, "rb") as fp:
            loaded = read_fits_image(fp.read(), filename=fname)

        # 100 distributed points: 10 x 10 grid
        xs = np.linspace(0.0, float(w_px - 1), 10)
        ys = np.linspace(0.0, float(h_px - 1), 10)

        stable_errors = []
        legacy_errors = []
        ra_diffs = []
        dec_diffs = []

        for y in ys:
            for x in xs:
                ref_ra, ref_dec = first_principles_tan_pix2world(hdr, float(x), float(y))
                app_ra, app_dec = pixel_to_world(loaded.wcs, float(x), float(y), origin=0)

                sep_stable = stable_angular_separation_arcsec(ref_ra, ref_dec, app_ra, app_dec)
                sep_legacy = legacy_acos_angular_separation_arcsec(ref_ra, ref_dec, app_ra, app_dec)

                stable_errors.append(sep_stable)
                legacy_errors.append(sep_legacy)

                dec_diffs.append(abs(ref_dec - app_dec))
                dra = min(abs(ref_ra - app_ra), 360.0 - abs(ref_ra - app_ra))
                dra_cosd = dra * math.cos(math.radians(ref_dec))
                ra_diffs.append(dra_cosd)

        max_stable = float(np.max(stable_errors))
        rms_stable = float(math.sqrt(np.mean(np.array(stable_errors) ** 2)))
        max_legacy = float(np.max(legacy_errors))
        rms_legacy = float(math.sqrt(np.mean(np.array(legacy_errors) ** 2)))
        max_ra = float(np.max(ra_diffs))
        max_dec = float(np.max(dec_diffs))

        status = "PASS" if max_stable < 0.01 else "FAIL"

        print(f"[{status}] {fname:<28s} | Points: 100 | Stable Max: {max_stable:.4e}\" (RMS: {rms_stable:.4e}\") | Legacy Max: {max_legacy:.4e}\" | MaxRA*cosD: {max_ra:.2e}°")

        results.append({
            "fixture": fname,
            "status": status,
            "dimensions": f"{w_px}x{h_px}",
            "crval": [hdr["CRVAL1"], hdr["CRVAL2"]],
            "crpix": [hdr["CRPIX1"], hdr["CRPIX2"]],
            "points_tested": 100,
            "stable_max_angular_error_arcsec": max_stable,
            "stable_rms_angular_error_arcsec": rms_stable,
            "legacy_acos_max_angular_error_arcsec": max_legacy,
            "legacy_acos_rms_angular_error_arcsec": rms_legacy,
            "max_ra_diff_cos_dec_deg": max_ra,
            "max_dec_diff_deg": max_dec,
        })

    out_file = os.path.join(FIXTURE_DIR, "m3_first_principles_audit_results.json")
    with open(out_file, "w") as fp:
        json.dump(results, fp, indent=2)
    print("=" * 105)
    print(f"Audit results written to: {out_file}\n")
    return results


if __name__ == "__main__":
    run_first_principles_audit()
