import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.ipac.irsa import Irsa
import requests

print("=== Testing SIA query ===")
try:
    coord = SkyCoord(ra=210.80227 * u.deg, dec=54.34895 * u.deg, frame="icrs")
    res_sia = Irsa.query_sia(pos=(coord, 0.05 * u.deg), collection=["spherex_dr1", "spherex_qr3"])
    print("SIA success! Found records:", len(res_sia))
except Exception as e:
    print("SIA error:", type(e), e)

print("\n=== Testing TAP sync ===")
try:
    q = "SELECT TOP 1 * FROM spherex.plane"
    res_tap = Irsa.query_tap(q)
    print("TAP success! Found rows:", len(res_tap))
except Exception as e:
    print("TAP error:", type(e), e)

print("\n=== Testing HTTP direct to TAP sync ===")
try:
    r = requests.post(
        "https://irsa.ipac.caltech.edu/TAP/sync",
        data={"REQUEST": "doQuery", "LANG": "ADQL", "QUERY": "SELECT TOP 1 table_name FROM tap_schema.tables"},
        timeout=15,
        headers={"User-Agent": "Antigravity/1.0"}
    )
    print("HTTP TAP sync status:", r.status_code)
    print("Response preview:", r.text[:200])
except Exception as e:
    print("HTTP TAP sync error:", type(e), e)
