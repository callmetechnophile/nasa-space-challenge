import requests

headers = {"User-Agent": "Antigravity-SPHEREx-Explorer/1.0"}

print("1. Testing SIA directly:")
try:
    r_sia = requests.get(
        "https://irsa.ipac.caltech.edu/SIA",
        params={"POS": "210.80227,54.34895", "SIZE": "0.1", "collection": "spherex_dr1"},
        timeout=10,
        headers=headers
    )
    print("SIA status:", r_sia.status_code, "Length:", len(r_sia.text))
    print(r_sia.text[:300])
except Exception as e:
    print("SIA error:", type(e), e)

print("\n2. Testing TAP sync directly:")
try:
    r_tap = requests.post(
        "https://irsa.ipac.caltech.edu/TAP/sync",
        data={"REQUEST": "doQuery", "LANG": "ADQL", "QUERY": "SELECT TOP 1 * FROM spherex.plane"},
        timeout=10,
        headers=headers
    )
    print("TAP status:", r_tap.status_code, "Length:", len(r_tap.text))
    print(r_tap.text[:300])
except Exception as e:
    print("TAP error:", type(e), e)

print("\n3. Testing TAP async directly:")
try:
    r_async = requests.post(
        "https://irsa.ipac.caltech.edu/TAP/async",
        data={"REQUEST": "doQuery", "LANG": "ADQL", "QUERY": "SELECT TOP 1 * FROM spherex.plane"},
        timeout=10,
        headers=headers
    )
    print("TAP async status:", r_async.status_code, "Length:", len(r_async.text))
    print(r_async.text[:300])
except Exception as e:
    print("TAP async error:", type(e), e)
