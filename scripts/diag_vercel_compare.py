import httpx
import json
import time

payload = {
    "file1": "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
    "file2": "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits",
    "significance_threshold": 3.5,
    "spectral_tolerance": 0.02,
    "grid_size": 512,
    "subtract_background": True,
}

url = "https://skytracebysplinets.vercel.app/api/v1/temporal/compare"

print("Sending POST request to Vercel URL:", url)
t0 = time.time()
try:
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload)
        print(f"Status: {resp.status_code} in {time.time()-t0:.2f}s")
        print("Headers:", dict(resp.headers))
        print("Body:", resp.text)
except Exception as e:
    print(f"Error after {time.time()-t0:.2f}s: {e}")
