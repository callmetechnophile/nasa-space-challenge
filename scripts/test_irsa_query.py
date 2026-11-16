import httpx
import sys

client = httpx.Client(timeout=10.0)
for coll in ['spherex_dr1', 'spherex_qr3']:
    url = f"https://irsa.ipac.caltech.edu/SIA?POS=circle+269.452083+4.693333+0.5&COLLECTION={coll}"
    print(f"\n--- Testing SIA {coll} ---")
    print("URL:", url)
    try:
        r = client.get(url, headers={"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0"})
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('content-type')}")
        print(f"Length: {len(r.content)}")
        print("Body preview:", r.text[:400])
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

print("\n--- Testing TAP ---")
tap_url = "https://irsa.ipac.caltech.edu/TAP/sync"
query_sql = """SELECT TOP 5 a.uri, p.planeid, p.energy_bandpassname
FROM spherex.artifact a
JOIN spherex.plane p ON a.planeid = p.planeid
WHERE 1 = CONTAINS(POINT('ICRS', 269.452083, 4.693333), p.poly)"""
try:
    r = client.post(tap_url, data={
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "QUERY": query_sql,
        "FORMAT": "votable",
    }, headers={"User-Agent": "SPHEREx-Temporal-Explorer/M6.3"})
    print(f"TAP Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type')}")
    print(f"Length: {len(r.content)}")
    print("TAP Body preview:", r.text[:400])
except Exception as e:
    print(f"TAP Exception: {type(e).__name__}: {e}")
