import socket
import ssl
import time
import urllib.parse
import httpx
from astropy.io.votable import parse_single_table
import io
from astropy.io import fits
import hashlib

def test_dns():
    t0 = time.time()
    try:
        ip = socket.gethostbyname("irsa.ipac.caltech.edu")
        dt = time.time() - t0
        print(f"[DNS] PASS: irsa.ipac.caltech.edu -> {ip} in {dt:.3f}s")
        return True, ip
    except Exception as e:
        dt = time.time() - t0
        print(f"[DNS] FAIL: {e} in {dt:.3f}s")
        return False, str(e)

def test_tcp(ip):
    t0 = time.time()
    try:
        s = socket.create_connection((ip, 443), timeout=10.0)
        dt = time.time() - t0
        print(f"[TCP] PASS: Connected to {ip}:443 in {dt:.3f}s")
        s.close()
        return True
    except Exception as e:
        dt = time.time() - t0
        print(f"[TCP] FAIL: {e} in {dt:.3f}s")
        return False

def test_tls():
    t0 = time.time()
    try:
        context = ssl.create_default_context()
        with socket.create_connection(("irsa.ipac.caltech.edu", 443), timeout=15.0) as sock:
            with context.wrap_socket(sock, server_hostname="irsa.ipac.caltech.edu") as ssock:
                version = ssock.version()
                cipher = ssock.cipher()
                dt = time.time() - t0
                print(f"[TLS] PASS: {version}, cipher {cipher[0]} in {dt:.3f}s")
                return True
    except Exception as e:
        dt = time.time() - t0
        print(f"[TLS] FAIL: {e} in {dt:.3f}s")
        return False

def test_sia2_query(collection="spherex_qr3", ra=45.0, dec=0.0, radius=0.01, timeout=60.0):
    url = "https://irsa.ipac.caltech.edu/SIA"
    params = {
        "COLLECTION": collection,
        "POS": f"circle {ra} {dec} {radius}",
        "RESPONSEFORMAT": "votable"
    }
    encoded_url = f"{url}?{urllib.parse.urlencode(params)}"
    print(f"\n[SIA2] Querying {encoded_url} (timeout={timeout}s)...")
    t0 = time.time()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(
                encoded_url,
                headers={"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0 (NASA Space Apps)"}
            )
            dt = time.time() - t0
            print(f"[SIA2] Status: {resp.status_code}, Length: {len(resp.content)} bytes, Content-Type: {resp.headers.get('content-type')} in {dt:.3f}s")
            return resp
    except Exception as e:
        dt = time.time() - t0
        print(f"[SIA2] FAIL: {type(e).__name__}: {e} in {dt:.3f}s")
        return None

if __name__ == "__main__":
    ok, ip = test_dns()
    if ok:
        test_tcp(ip)
    test_tls()
    
    # Try query
    resp = test_sia2_query("spherex_qr3", 45.0, 0.0, 0.01, timeout=60.0)
    if not resp or resp.status_code != 200:
        print("[SIA2] Trying spherex_qr2...")
        resp = test_sia2_query("spherex_qr2", 45.0, 0.0, 0.01, timeout=60.0)

    if resp and resp.status_code == 200:
        print("[VOTable] Parsing VOTable...")
        try:
            table = parse_single_table(io.BytesIO(resp.content))
            rows = table.array
            print(f"[VOTable] PASS: Parsed {len(rows)} records from VOTable.")
            if len(rows) > 0:
                rec0 = rows[0]
                url_col = "access_url"
                access_url = None
                for field in table.fields:
                    if field.name == "access_url":
                        access_url = str(rec0[field.name])
                        if isinstance(access_url, bytes):
                            access_url = access_url.decode()
                print(f"[VOTable] First access_url: {access_url}")
                
                # Test downloading FITS or HEAD/range
                if access_url:
                    print(f"\n[DOWNLOAD] Testing download from {access_url}...")
                    t0 = time.time()
                    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
                        # Test streaming first 28800 bytes (10 FITS blocks)
                        head_resp = client.get(access_url, headers={"Range": "bytes=0-28799"})
                        dt = time.time() - t0
                        print(f"[DOWNLOAD] HTTP {head_resp.status_code}, received {len(head_resp.content)} bytes in {dt:.3f}s")
                        
                        # Validate FITS header
                        try:
                            hdr = fits.Header.fromstring(head_resp.content[:2880].decode('latin1', errors='replace'))
                            print(f"[FITS] PASS: Valid FITS header! SIMPLE={hdr.get('SIMPLE')}, EXTEND={hdr.get('EXTEND')}")
                        except Exception as fe:
                            print(f"[FITS] Header check: {fe}")
        except Exception as e:
            print(f"[VOTable] Parse FAIL: {e}")
