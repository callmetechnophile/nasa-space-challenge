import time
import json
import httpx

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/v1"

results = []

def run_test(name, method, url, timeout=30.0, **kwargs):
    t0 = time.perf_counter()
    status = None
    elapsed_ms = 0
    content_type = ""
    error = None
    body_preview = ""
    success = False

    try:
        if method == "GET":
            r = httpx.get(url, timeout=timeout, **kwargs)
        elif method == "POST":
            r = httpx.post(url, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported method {method}")
        
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        status = r.status_code
        content_type = r.headers.get("content-type", "")
        
        if r.status_code in (200, 201):
            success = True
            try:
                data = r.json()
                if isinstance(data, list):
                    body_preview = f"List of {len(data)} items"
                elif isinstance(data, dict):
                    keys = list(data.keys())[:6]
                    body_preview = f"Dict with keys: {keys}"
                else:
                    body_preview = str(data)[:100]
            except Exception:
                body_preview = f"Binary/Raw {len(r.content)} bytes"
        else:
            error = f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        error = str(exc)

    res = {
        "name": name,
        "method": method,
        "url": url.replace(BASE_URL, ""),
        "status": status,
        "elapsed_ms": elapsed_ms,
        "content_type": content_type,
        "success": success,
        "body_preview": body_preview,
        "error": error
    }
    results.append(res)
    print(f"[{'PASS' if success else 'FAIL'}] {method} {res['url']} ({elapsed_ms}ms) -> {status or 'ERROR'}")
    if error:
        print(f"       Error: {error}")
    return res

print("=================================================================")
print("SKYTRACE LOCAL BACKEND ENDPOINT AUDIT")
print("=================================================================")

# 1. Health & Readiness
run_test("Health Check", "GET", f"{BASE_URL}/health")
run_test("Readiness Probe", "GET", f"{BASE_URL}/ready")
run_test("Root Info", "GET", f"{BASE_URL}/")

# 2. Coordinates
run_test("Coordinate Parse", "POST", f"{API_URL}/coordinates/parse", json={"ra": "133.7951", "dec": "-7.2451"})
run_test("Coordinate Convert", "GET", f"{API_URL}/coordinates/convert?ra=133.7951&dec=-7.2451")

# 3. Targets
run_test("List Validation Targets", "GET", f"{API_URL}/targets")
run_test("Get WISE 0855 Details", "GET", f"{API_URL}/targets/wise-0855")
run_test("M6 Target Validation Suite", "GET", f"{API_URL}/targets/m6-validation")
run_test("M6 Single Target Validation", "GET", f"{API_URL}/targets/m6-validation/wise-0855")

# 4. Spectral
run_test("List Spectral Bands", "GET", f"{API_URL}/spectral/bands")
run_test("Get Single Band Channel 50", "GET", f"{API_URL}/spectral/bands/50")
run_test("Get Spectral Profile for WISE 0855", "GET", f"{API_URL}/spectral/profile?target=wise-0855")

# 5. Observations
run_test("Get Observations by Target", "GET", f"{API_URL}/observations?target=wise-0855")
run_test("Get Observations by Coordinates", "GET", f"{API_URL}/observations?ra=133.7951&dec=-7.2451")

# 6. Images & FITS
run_test("List Sample Images", "GET", f"{API_URL}/images/samples")
run_test("Get Sample Image Layer", "GET", f"{API_URL}/images/sample/wise-0855?stretch=asinh&brightness=1.0&contrast=1.0&radius=98.0")

# 7. SPHEREx Archive Discovery
run_test("SPHEREx Cache Status", "GET", f"{API_URL}/spherex/status")
run_test("SPHEREx Archive Search", "POST", f"{API_URL}/spherex/search", json={"ra": 133.7951, "dec": -7.2451, "radius_arcmin": 10.0, "release": "QR3"})

# 8. Temporal Analysis
run_test("Temporal Observations List", "GET", f"{API_URL}/temporal/observations")
run_test("Temporal Benchmark Pairs", "GET", f"{API_URL}/temporal/benchmark-pairs")
run_test("Temporal Discovery Query", "GET", f"{API_URL}/temporal/discovery?ra=46.8444&dec=1.8322&fov=0.5")
run_test("Temporal Comparison Engine", "POST", f"{API_URL}/temporal/compare", json={
    "file1": "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
    "file2": "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits",
    "significance_threshold": 3.5,
    "spectral_tolerance": 0.05,
    "grid_size": 256,
    "subtract_background": True
})

print("\n=================================================================")
print(f"AUDIT SUMMARY: {sum(1 for r in results if r['success'])} / {len(results)} PASSED")
print("=================================================================")

with open("endpoint_audit_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
