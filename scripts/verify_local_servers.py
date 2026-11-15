import urllib.request
import json

print("=== 1. Testing Frontend (http://localhost:3000) ===")
try:
    with urllib.request.urlopen("http://localhost:3000", timeout=5) as resp:
        print("Frontend HTTP status:", resp.status)
        content = resp.read().decode("utf-8")
        print("Frontend HTML length:", len(content), "bytes")
except Exception as e:
    print("Frontend error:", e)

print("\n=== 2. Testing Backend Status (http://127.0.0.1:8000/api/v1/spherex/status) ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/spherex/status", timeout=5) as resp:
        print("Backend status code:", resp.status)
        data = json.loads(resp.read().decode("utf-8"))
        print("Backend response:", data)
except Exception as e:
    print("Backend error:", e)

print("\n=== 3. Testing Backend Targets (http://127.0.0.1:8000/api/v1/targets) ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/targets", timeout=5) as resp:
        targets = json.loads(resp.read().decode("utf-8"))
        print(f"Returned {len(targets)} targets:")
        for t in targets:
            name = t.get('name')
            tid = t.get('id')
            ra = t.get('ra_deg')
            dec = t.get('dec_deg')
            obs = t.get('observations_available', 0)
            print(f"  - {name} ({tid}): RA={ra} deg, Dec={dec} deg, Epochs={obs}")
except Exception as e:
    print("Targets error:", e)
