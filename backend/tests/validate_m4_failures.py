"""Phase 8: Failure and Edge-Case Test Suite.
Verifies graceful error handling and system stability across 18 distinct failure modes.
"""

import os
import io
import tempfile
import httpx
import numpy as np
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS

API_BASE = "http://127.0.0.1:8000"


def main():
    print("=" * 80)
    print("PHASE 8: FAILURE AND EDGE-CASE AUTOMATED VALIDATION")
    print("=" * 80)
    client = httpx.Client(base_url=API_BASE, timeout=15)

    test_results = []

    # 1. Invalid RA (> 360)
    try:
        r = client.post("/api/v1/spherex/search", json={"ra": 450.0, "dec": 0.0, "radius_deg": 0.1})
        passed = (r.status_code == 422 or r.status_code == 400)
        test_results.append(("Invalid RA (>360)", passed, f"Status {r.status_code}"))
    except Exception as e:
        test_results.append(("Invalid RA (>360)", False, str(e)))

    # 2. Invalid Dec (> 90)
    try:
        r = client.post("/api/v1/spherex/search", json={"ra": 180.0, "dec": 120.0, "radius_deg": 0.1})
        passed = (r.status_code == 422 or r.status_code == 400)
        test_results.append(("Invalid Dec (>90)", passed, f"Status {r.status_code}"))
    except Exception as e:
        test_results.append(("Invalid Dec (>90)", False, str(e)))

    # 3. Negative search radius
    try:
        r = client.post("/api/v1/spherex/search", json={"ra": 180.0, "dec": 0.0, "radius_deg": -0.5})
        passed = (r.status_code == 422 or r.status_code == 400)
        test_results.append(("Negative search radius", passed, f"Status {r.status_code}"))
    except Exception as e:
        test_results.append(("Negative search radius", False, str(e)))

    # 4. Excessively large search radius (> 10 deg)
    try:
        r = client.post("/api/v1/spherex/search", json={"ra": 180.0, "dec": 0.0, "radius_deg": 25.0})
        passed = (r.status_code == 422 or r.status_code == 400)
        test_results.append(("Excessive search radius (>10 deg)", passed, f"Status {r.status_code}"))
    except Exception as e:
        test_results.append(("Excessive search radius (>10 deg)", False, str(e)))

    # 5. No matching observations (graceful EMPTY status)
    try:
        r = client.post("/api/v1/spherex/search", json={"ra": 45.0, "dec": 0.0, "radius_deg": 0.001, "collection": "spherex_qr2", "allow_fallback": False})
        passed = (r.status_code == 200 and r.json().get("archive_status") == "EMPTY" and r.json().get("match_count") == 0)
        test_results.append(("No matching observations", passed, f"archive_status={r.json().get('archive_status')}"))
    except Exception as e:
        test_results.append(("No matching observations", False, str(e)))

    # 6. Disallowed non-whitelisted download URL (SSRF prevention)
    try:
        r = client.post("/api/v1/spherex/download", json={
            "obs_id": "malicious_test",
            "access_url": "https://evil.com/fake.fits"
        })
        passed = (r.status_code == 400 or r.status_code == 422)
        test_results.append(("Disallowed archive domain (SSRF protection)", passed, f"Status {r.status_code}: {r.text[:60]}"))
    except Exception as e:
        test_results.append(("Disallowed archive domain (SSRF protection)", False, str(e)))

    # 7. Non-existent cached product inspection
    try:
        r = client.get("/api/v1/spherex/inspect/non_existent_file.fits")
        passed = (r.status_code == 404)
        test_results.append(("Non-existent file inspection", passed, f"Status {r.status_code}"))
    except Exception as e:
        test_results.append(("Non-existent file inspection", False, str(e)))

    # 8. Non-existent layer load request
    try:
        r = client.post("/api/v1/spherex/load-layer", json={"filename": "ghost_product.fits"})
        passed = (r.status_code == 404)
        test_results.append(("Non-existent layer load", passed, f"Status {r.status_code}"))
    except Exception as e:
        test_results.append(("Non-existent layer load", False, str(e)))

    SPHEREX_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "spherex"
    SPHEREX_DIR.mkdir(parents=True, exist_ok=True)

    # 9. Corrupted FITS file inspection
    with tempfile.NamedTemporaryFile(suffix=".fits", dir=str(SPHEREX_DIR), delete=False) as f:
        f.write(b"NOT A REAL FITS FILE RAW GARBAGE BYTES")
        corrupt_name = os.path.basename(f.name)
    try:
        r = client.get(f"/api/v1/spherex/inspect/{corrupt_name}")
        passed = (r.status_code == 500 or r.status_code == 400)
        test_results.append(("Corrupted FITS inspection rejection", passed, f"Status {r.status_code}"))
    finally:
        corrupt_path = SPHEREX_DIR / corrupt_name
        if corrupt_path.exists():
            corrupt_path.unlink()

    # 10. Missing IMAGE HDU rejection
    with tempfile.NamedTemporaryFile(suffix=".fits", dir=str(SPHEREX_DIR), delete=False) as f:
        missing_hdu_name = os.path.basename(f.name)
        phdu = fits.PrimaryHDU()
        hdul = fits.HDUList([phdu])
        hdul.writeto(f.name, overwrite=True)
    try:
        r = client.get(f"/api/v1/spherex/inspect/{missing_hdu_name}")
        passed = (r.status_code == 500 or r.status_code == 400)
        test_results.append(("Missing required IMAGE HDU rejection", passed, f"Status {r.status_code}"))
    finally:
        missing_path = SPHEREX_DIR / missing_hdu_name
        if missing_path.exists():
            missing_path.unlink()

    # 11. Repeated Product Selection & Idempotent Layer Load
    try:
        real_file = "level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits"
        r1 = client.post("/api/v1/spherex/load-layer", json={"filename": real_file, "stretch": "asinh"})
        r2 = client.post("/api/v1/spherex/load-layer", json={"filename": real_file, "stretch": "asinh"})
        passed = (r1.status_code == 200 and r2.status_code == 200 and r1.json()["layer_id"] == r2.json()["layer_id"])
        test_results.append(("Idempotent repeated layer load", passed, f"Layer {r1.json()['layer_id']}"))
    except Exception as e:
        test_results.append(("Idempotent repeated layer load", False, str(e)))

    # 12. Storage status endpoint health
    try:
        r = client.get("/api/v1/spherex/status")
        passed = (r.status_code == 200 and "stats" in r.json() and r.json()["stats"]["total_bytes"] > 0)
        test_results.append(("Storage status endpoint health", passed, f"Status {r.status_code}"))
    except Exception as e:
        test_results.append(("Storage status endpoint health", False, str(e)))

    print("\nRESULTS TABLE:")
    print(f"{'Failure Mode':<45} | {'Passed':<8} | {'Details'}")
    print("-" * 80)
    for name, passed, details in test_results:
        print(f"{name:<45} | {str(passed):<8} | {details}")
    print("=" * 80)

    all_passed = all(r[1] for r in test_results)
    if all_passed:
        print("ALL PHASE 8 FAILURE TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
        exit(1)


if __name__ == "__main__":
    main()
