import urllib.request
import json
import time

for path in ["/health", "/api/v1/temporal/observations"]:
    url = f"https://skytrace-backend.bravewave-3f2f8e7c.eastus.azurecontainerapps.io{path}"
    print(f"Testing {url} ...")
    t0 = time.time()
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            print(f"  Status {resp.status} in {time.time()-t0:.2f}s")
            print("  Body snippet:", resp.read().decode()[:200])
    except Exception as e:
        print(f"  Error in {time.time()-t0:.2f}s:", e)
