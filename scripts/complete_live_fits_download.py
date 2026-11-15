import os
import time
import httpx
import hashlib
from astropy.io import fits

url = "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W30_2A/l2b-v27-2026-224/1/level2_2026W30_2A_0607_1D1_spx_l2b-v27-2026-224.fits"
dest = "d:/nasa/data/spherex/live_irsa_pipeline_test.fits"
total_size = 65540160
chunk_size = 4 * 1024 * 1024  # 4 MB chunks

print("Resuming live FITS download from IRSA...")
t0 = time.time()
current_size = os.path.getsize(dest) if os.path.exists(dest) else 0
print(f"Current on-disk size: {current_size:,} bytes")

headers = {"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0 (NASA Space Apps)"}

with open(dest, "ab" if current_size > 0 else "wb") as f_out:
    downloaded = current_size
    while downloaded < total_size:
        end = min(downloaded + chunk_size - 1, total_size - 1)
        req_headers = dict(headers)
        req_headers["Range"] = f"bytes={downloaded}-{end}"
        expected_len = end - downloaded + 1
        
        success = False
        for attempt in range(5):
            try:
                with httpx.Client(timeout=45.0, follow_redirects=True) as client:
                    resp = client.get(url, headers=req_headers)
                    if resp.status_code in (200, 206) and len(resp.content) == expected_len:
                        f_out.write(resp.content)
                        f_out.flush()
                        downloaded += len(resp.content)
                        pct = (downloaded / total_size) * 100.0
                        dur = time.time() - t0
                        rate = (downloaded / (1024*1024)) / dur if dur > 0 else 0
                        print(f"  Downloaded: {downloaded:,} / {total_size:,} ({pct:.1f}%) at {rate:.2f} MB/s", flush=True)
                        success = True
                        break
                    else:
                        print(f"  Attempt {attempt+1} got HTTP {resp.status_code}, len={len(resp.content)} (expected {expected_len})", flush=True)
            except Exception as e:
                print(f"  Attempt {attempt+1} exception: {e}", flush=True)
                time.sleep(2.0 * (attempt + 1))
        
        if not success:
            raise RuntimeError(f"Failed to download chunk starting at {downloaded}")

print(f"Download complete in {time.time() - t0:.2f} s! Final on-disk size: {os.path.getsize(dest):,} bytes")

# Calculate SHA-256
hasher = hashlib.sha256()
with open(dest, "rb") as f:
    for block in iter(lambda: f.read(1024*1024), b""):
        hasher.update(block)
sha = hasher.hexdigest()
print(f"SHA-256: {sha}")

# Validate FITS structure
print("\nValidating FITS structure via Astropy...")
with fits.open(dest) as hdul:
    print(f"HDUs Count: {len(hdul)}")
    for i, hdu in enumerate(hdul):
        print(f"  HDU {i}: Name={hdu.name:<12} Type={type(hdu).__name__:<16} Shape={str(getattr(hdu, 'shape', None)):<16}")
    assert len(hdul) >= 2
    assert "IMAGE" in hdul
    assert hdul[1].shape == (2040, 2040)
    print("FITS Structural Integrity: FULLY VALIDATED (PASS)")
