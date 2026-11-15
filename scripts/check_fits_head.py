import httpx
import time

url = "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W30_2A/l2b-v27-2026-224/1/level2_2026W30_2A_0607_1D1_spx_l2b-v27-2026-224.fits"
t0 = time.time()
with httpx.Client(timeout=30.0, follow_redirects=True) as client:
    r = client.head(url)
    dt = time.time() - t0
    print(f"Status: {r.status_code}")
    print(f"Content-Length: {r.headers.get('content-length')}")
    print(f"Content-Type: {r.headers.get('content-type')}")
    print(f"Time: {dt:.3f}s")
