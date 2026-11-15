import requests

query = """
SELECT TOP 5 source_id, ra, dec, pmra, pmdec, parallax, phot_g_mean_mag
FROM "I/355/gaiadr3"
WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 132.76, -5.65, 0.05))
"""

for url in ["http://tapvizier.cds.unistra.fr/TAP/sync", "https://dc.zah.uni-heidelberg.de/tap/sync"]:
    try:
        r = requests.post(url, data={"REQUEST": "doQuery", "LANG": "ADQL", "QUERY": query}, timeout=8)
        print(url, "status:", r.status_code, "length:", len(r.text))
        if r.status_code == 200:
            print("Preview:\n", r.text[:300])
            break
    except Exception as e:
        print(url, "error:", e)
