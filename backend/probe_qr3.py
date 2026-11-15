import urllib.parse
import urllib.request
import io
from astropy.io.votable import parse_single_table

def check(coll, ra, dec, radius=1.0):
    pos_str = f"circle {ra} {dec} {radius}"
    url = f"https://irsa.ipac.caltech.edu/SIA?COLLECTION={coll}&POS={urllib.parse.quote(pos_str)}"
    req = urllib.request.Request(url, headers={"User-Agent": "SPHEREx-Explorer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            t = parse_single_table(io.BytesIO(resp.read()))
            print(f"{coll} at ({ra}, {dec}, r={radius}): {len(t.array)} matches")
            if len(t.array) > 0:
                print(f"  Sample: {t.array[0]['obs_id']} | {t.array[0]['access_url']}")
                return True
    except Exception as e:
        print(f"{coll} Error:", e)
    return False

if __name__ == "__main__":
    check("spherex_qr3", 270.0, 66.56, 1.0)
    check("spherex_qr3_deep", 270.0, 66.56, 1.0)
    check("spherex_qr3", 90.0, -66.56, 1.0)
    check("spherex_qr3_deep", 90.0, -66.56, 1.0)
    check("spherex_qr3", 150.1, 2.2, 1.0)
    check("spherex_qr3", 53.1, -27.8, 1.0) # CDF-S
    check("spherex_qr3_deep", 53.1, -27.8, 1.0)
