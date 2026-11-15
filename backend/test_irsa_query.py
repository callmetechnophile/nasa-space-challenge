import urllib.parse
import urllib.request
import io
from astropy.io.votable import parse_single_table

def query_sia(collection: str, pos: str, radius_deg: float = 0.05):
    pos_str = f"circle {pos} {radius_deg}"
    query_params = {
        "COLLECTION": collection,
        "POS": pos_str
    }
    encoded = urllib.parse.urlencode(query_params)
    url = f"https://irsa.ipac.caltech.edu/SIA?{encoded}"
    print(f"\n=======================================================")
    print(f"Querying: {collection} | POS: {pos_str}")
    print(f"URL: {url}")
    print(f"=======================================================")
    
    req = urllib.request.Request(url, headers={"User-Agent": "SPHEREx-3D-Explorer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"HTTP Status: {resp.status}")
            data = resp.read()
            table = parse_single_table(io.BytesIO(data))
            rows = table.array
            print(f"Returned Matches: {len(rows)}")
            if len(rows) > 0:
                for idx in range(min(5, len(rows))):
                    r = rows[idx]
                    print(f"\n  Match #{idx + 1}:")
                    print(f"    Obs ID:         {r['obs_id']}")
                    print(f"    Collection:     {r['obs_collection']}")
                    print(f"    Facility/Inst:  {r['facility_name']} / {r['instrument_name']}")
                    print(f"    Bandpass:       {r['energy_bandpassname']}")
                    print(f"    Center (RA,Dec):({r['s_ra']:.6f}, {r['s_dec']:.6f})")
                    print(f"    Dimensions:     {r['s_xel1']} x {r['s_xel2']}")
                    print(f"    Access Format:  {r['access_format']}")
                    print(f"    Est Size:       {r['access_estsize']} bytes ({r['access_estsize'] / (1024*1024):.2f} MB)")
                    print(f"    Access URL:     {r['access_url']}")
            return table
    except Exception as exc:
        print(f"HTTP / Query Error: {exc}")
        return None

if __name__ == "__main__":
    # Test 1: WISE 0855 in QR3
    t1 = query_sia("spherex_qr3", "133.795129 -7.245147", 0.05)
    
    # Test 2: WISE 0855 in QR2 fallback
    t2 = query_sia("spherex_qr2", "133.795129 -7.245147", 0.05)
    
    # Test 3: Larger radius if 0.05 had 0 matches
    if (t1 is None or len(t1.array) == 0) and (t2 is None or len(t2.array) == 0):
        print("\nTrying larger radius 0.5 deg around WISE 0855...")
        query_sia("spherex_qr3", "133.795129 -7.245147", 0.5)
        query_sia("spherex_qr2", "133.795129 -7.245147", 0.5)
