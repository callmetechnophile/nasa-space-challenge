import urllib.request
import json
import traceback

payload = {
    "file1": "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
    "file2": "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits",
    "significance_threshold": 3.5,
    "spectral_tolerance": 0.02,
    "grid_size": 512,
    "subtract_background": True,
}

azure_url = "https://skytrace-backend.bravewave-3f2f8e7c.eastus.azurecontainerapps.io/api/v1/temporal/compare"
print("Sending request to Azure backend:", azure_url)

req = urllib.request.Request(
    azure_url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = resp.status
        body = resp.read().decode("utf-8")
        print(f"Status: {status}")
        data = json.loads(body)
        print("Success! Keys:", list(data.keys()))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} {e.reason}")
    body = e.read().decode("utf-8")
    print(f"Response body: {body}")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
