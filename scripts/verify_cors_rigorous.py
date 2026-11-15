import httpx

BACKEND_URL = "http://127.0.0.1:8000"
TEST_ORIGINS = [
    ("Authorized Localhost", "http://localhost:3000"),
    ("Authorized Loopback", "http://127.0.0.1:3000"),
    ("Unauthorized External", "http://unauthorized-evil.com")
]

print("="*80)
print("TASK C: RIGOROUS CORS PREFLIGHT & APPLICATION REQUEST AUDIT")
print("="*80)

with httpx.Client(base_url=BACKEND_URL, timeout=10.0) as client:
    for label, origin in TEST_ORIGINS:
        print(f"\n--- Testing Origin: {label} ({origin}) ---")
        
        # 1. Preflight Request (OPTIONS /health)
        preflight_headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
        res_preflight = client.options("/health", headers=preflight_headers)
        print(f"[Preflight OPTIONS /health]")
        print(f"  HTTP Status:                     {res_preflight.status_code}")
        print(f"  Access-Control-Allow-Origin:     {res_preflight.headers.get('access-control-allow-origin')}")
        print(f"  Access-Control-Allow-Credentials:{res_preflight.headers.get('access-control-allow-credentials')}")
        print(f"  Access-Control-Allow-Methods:    {res_preflight.headers.get('access-control-allow-methods')}")
        print(f"  Access-Control-Allow-Headers:    {res_preflight.headers.get('access-control-allow-headers')}")
        
        # 2. Application Request (GET /health)
        app_headers = {
            "Origin": origin
        }
        res_get = client.get("/health", headers=app_headers)
        print(f"[Application GET /health]")
        print(f"  HTTP Status:                     {res_get.status_code}")
        print(f"  Response Body:                   {res_get.json()}")
        print(f"  Access-Control-Allow-Origin:     {res_get.headers.get('access-control-allow-origin')}")
        print(f"  Access-Control-Allow-Credentials:{res_get.headers.get('access-control-allow-credentials')}")
        print(f"  Access-Control-Expose-Headers:   {res_get.headers.get('access-control-expose-headers')}")
