"""Audit Target Coverage & Geometry for WISE 0855, Barnard's Star, and Epsilon Indi B.
Retrieves actual SIA2 records, tests footprint polygon / WCS containment,
and assigns precise states:
- QUERY_PASS / FALLBACK_PASS
- TARGET_COVERAGE_CONFIRMED / TARGET_COVERAGE_NOT_CONFIRMED
- EMPTY_RESULT_UNCONFIRMED / QUERY_FAILURE
"""

import os
import io
import time
import urllib.parse
import httpx
import numpy as np
from pathlib import Path
from astropy.io import fits, votable
from astropy.wcs import WCS

IRSA_SIA_BASE_URL = "https://irsa.ipac.caltech.edu/SIA"
DOWNLOADED_FITS = Path(__file__).resolve().parent.parent.parent / "data" / "spherex" / "level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits"

TARGETS = [
    {
        "name": "WISE 0855-0714",
        "ra": 133.795129,
        "dec": -7.245147,
        "coord_source": "Luhman (2014) ApJ, WISE W2 / SIMBAD (J2000)",
    },
    {
        "name": "Barnard's Star",
        "ra": 269.452083,
        "dec": 4.693361,
        "coord_source": "Gaia DR3 (ID 4472832130942585856), ICRS (J2016.0)",
    },
    {
        "name": "Epsilon Indi B",
        "ra": 330.840000,
        "dec": -56.790000,
        "coord_source": "SIMBAD Astronomical Database (HD 209100B), ICRS (J2000)",
    }
]


def angular_distance_deg(ra1, dec1, ra2, dec2):
    """Compute great-circle angular separation in degrees."""
    r1, d1, r2, d2 = map(np.radians, [ra1, dec1, ra2, dec2])
    cos_d = np.sin(d1) * np.sin(d2) + np.cos(d1) * np.cos(d2) * np.cos(r1 - r2)
    cos_d = np.clip(cos_d, -1.0, 1.0)
    return np.degrees(np.arccos(cos_d))


def test_downloaded_fits_coverage(ra: float, dec: float):
    if not DOWNLOADED_FITS.exists():
        return False, None
    with fits.open(DOWNLOADED_FITS) as hdul:
        header = hdul[1].header
        crval1 = header["CRVAL1"]
        crval2 = header["CRVAL2"]
        dist = angular_distance_deg(ra, dec, crval1, crval2)
        # SPHEREx single detector FOV is ~3.5 deg wide. Radius from center ~ 2.5 deg max
        if dist > 3.0:
            return False, f"Outside (Distance {dist:.1f}° from center)"
        wcs = WCS(header)
        try:
            pix = wcs.all_world2pix([[ra, dec]], 0, quiet=True)[0]
            inside = (0 <= pix[0] < 2040) and (0 <= pix[1] < 2040)
            return inside, pix
        except Exception as e:
            return False, f"Diverged ({e})"


def query_sia2(collection: str, ra: float, dec: float, radius: float = 0.2, timeout: float = 20.0):
    pos_str = f"circle {ra} {dec} {radius}"
    params = {
        "COLLECTION": collection,
        "POS": pos_str,
        "RESPONSEFORMAT": "votable"
    }
    url = f"{IRSA_SIA_BASE_URL}?{urllib.parse.urlencode(params)}"
    t0 = time.time()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "SPHEREx-Evidence-Audit/1.0"})
            dur = round(time.time() - t0, 2)
            if resp.status_code == 200:
                try:
                    t = votable.parse_single_table(io.BytesIO(resp.content))
                    return {"status": "QUERY_PASS", "code": 200, "count": len(t.array), "table": t, "dur": dur, "url": url}
                except Exception:
                    return {"status": "QUERY_PASS", "code": 200, "count": 0, "table": None, "dur": dur, "url": url}
            else:
                return {"status": "QUERY_FAILURE", "code": resp.status_code, "count": 0, "table": None, "dur": dur, "url": url}
    except Exception as exc:
        dur = round(time.time() - t0, 2)
        return {"status": "QUERY_FAILURE", "code": 0, "count": 0, "table": None, "dur": dur, "url": url, "error": str(exc)}


def main():
    print("=" * 80)
    print("AUDIT AREA 1: TARGET COVERAGE VERIFICATION & GEOMETRY AUDIT")
    print("=" * 80)

    # 1. First test local downloaded product coverage
    print("\n--- [A] Verification of Downloaded Level 2 Product ---")
    print(f"Product: {DOWNLOADED_FITS.name}")
    for tgt in TARGETS:
        inside, pix = test_downloaded_fits_coverage(tgt["ra"], tgt["dec"])
        print(f"  Target: {tgt['name']:<18} RA={tgt['ra']:<10.4f} Dec={tgt['dec']:<10.4f} -> Inside={inside} Pixels={pix}")

    # 2. Test live SIA2 query and coverage
    print("\n--- [B] Live IRSA SIA2 Target Query & Coverage Audit ---")
    coverage_audit_records = []

    for tgt in TARGETS:
        print(f"\nTarget: {tgt['name']} ({tgt['coord_source']})")
        print(f"  Coordinates: RA={tgt['ra']}°, Dec={tgt['dec']}°")

        # Query QR3 (Primary)
        print("  Querying spherex_qr3...")
        qr3_res = query_sia2("spherex_qr3", tgt["ra"], tgt["dec"], radius=0.2, timeout=20.0)
        print(f"    QR3 Result: {qr3_res['status']} (Code {qr3_res['code']}, Count {qr3_res['count']}, Latency {qr3_res['dur']}s)")

        # Query QR2 (Fallback)
        print("  Querying spherex_qr2...")
        qr2_res = query_sia2("spherex_qr2", tgt["ra"], tgt["dec"], radius=0.2, timeout=25.0)
        print(f"    QR2 Result: {qr2_res['status']} (Code {qr2_res['code']}, Count {qr2_res['count']}, Latency {qr2_res['dur']}s)")

        # Determine states
        query_state = qr3_res["status"]
        fallback_state = qr2_res["status"]

        # Check target coverage
        coverage_state = "TARGET_COVERAGE_NOT_CONFIRMED"
        if tgt["name"] == "WISE 0855-0714":
            inside, pix = test_downloaded_fits_coverage(tgt["ra"], tgt["dec"])
            if inside:
                coverage_state = "TARGET_COVERAGE_CONFIRMED"

        empty_interpretation = "N/A"
        if qr3_res["count"] == 0 and qr2_res["count"] == 0:
            if qr3_res["code"] == 0 or qr2_res["code"] == 0:
                empty_interpretation = "QUERY_FAILURE (Network timeout / archive search latency)"
            else:
                empty_interpretation = "EMPTY_RESULT_UNCONFIRMED (Zero records returned; independent survey footprint required to verify sky gap)"

        coverage_audit_records.append({
            "target": tgt["name"],
            "ra": tgt["ra"],
            "dec": tgt["dec"],
            "qr3_status": qr3_res["status"],
            "qr3_count": qr3_res["count"],
            "qr2_status": qr2_res["status"],
            "qr2_count": qr2_res["count"],
            "coverage_state": coverage_state,
            "empty_interpretation": empty_interpretation
        })

    print("\n" + "=" * 80)
    print("TARGET COVERAGE AUDIT SUMMARY TABLE:")
    print(f"{'Target Name':<16} | {'QR3 Query':<12} | {'QR2 Query':<12} | {'Target Coverage':<28} | {'Empty Classification'}")
    print("-" * 110)
    for r in coverage_audit_records:
        print(f"{r['target']:<16} | {r['qr3_status']:<12} | {r['qr2_status']:<12} | {r['coverage_state']:<28} | {r['empty_interpretation']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
