import os
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
from astropy.io import fits

url = "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W30_2A/l2b-v27-2026-224/1/level2_2026W30_2A_0607_1D1_spx_l2b-v27-2026-224.fits"
dest = "d:/nasa/data/spherex/live_irsa_pipeline_test.fits"
total_size = 65540160
chunk_size = 2 * 1024 * 1024  # 2 MB

# Prepare chunks
chunks = []
offset = 0
chunk_idx = 0
while offset < total_size:
    end = min(offset + chunk_size - 1, total_size - 1)
    chunks.append((chunk_idx, offset, end))
    offset = end + 1
    chunk_idx += 1

print(f"Total size: {total_size:,} bytes")
print(f"Total chunks: {len(chunks)} of {chunk_size / (1024*1024):.1f} MB each")

parts_dir = "d:/nasa/data/spherex/irsa_chunks"
os.makedirs(parts_dir, exist_ok=True)

headers = {"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0 (NASA Space Apps)"}

def download_chunk(item):
    c_idx, start_byte, end_byte = item
    part_path = os.path.join(parts_dir, f"chunk_{c_idx:03d}.part")
    expected_len = end_byte - start_byte + 1
    
    # Check if part already exists and is full length
    if os.path.exists(part_path) and os.path.getsize(part_path) == expected_len:
        return c_idx, expected_len, 0.0
    
    req_headers = dict(headers)
    req_headers["Range"] = f"bytes={start_byte}-{end_byte}"
    
    for attempt in range(5):
        try:
            t0 = time.time()
            with httpx.Client(timeout=45.0, follow_redirects=True) as client:
                r = client.get(url, headers=req_headers)
                if r.status_code in (200, 206) and len(r.content) == expected_len:
                    with open(part_path, "wb") as f_part:
                        f_part.write(r.content)
                    dt = time.time() - t0
                    return c_idx, expected_len, dt
                else:
                    print(f"Chunk {c_idx} attempt {attempt+1} got HTTP {r.status_code}, len={len(r.content)}")
        except Exception as e:
            print(f"Chunk {c_idx} attempt {attempt+1} error: {e}")
            time.sleep(2.0 * (attempt + 1))
            
    raise RuntimeError(f"Failed to download chunk {c_idx} after 5 attempts")

print("\nStarting concurrent download with 4 worker threads...")
t_start = time.time()
completed_bytes = 0

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(download_chunk, c): c for c in chunks}
    for f in as_completed(futures):
        c_idx, c_len, c_dt = f.result()
        completed_bytes += c_len
        pct = (completed_bytes / total_size) * 100.0
        elapsed = time.time() - t_start
        rate = (completed_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
        print(f"[{completed_bytes:,}/{total_size:,} {pct:5.1f}%] Chunk {c_idx:02d} done ({c_len:,} B in {c_dt:.1f}s) - Overall: {rate:.2f} MB/s", flush=True)

print(f"\nAll chunks downloaded in {time.time() - t_start:.2f} s! Assembling file...")
# Assemble in exact order
with open(dest, "wb") as f_dest:
    for c_idx, start_byte, end_byte in chunks:
        part_path = os.path.join(parts_dir, f"chunk_{c_idx:03d}.part")
        with open(part_path, "rb") as f_part:
            data = f_part.read()
            assert len(data) == (end_byte - start_byte + 1), f"Corrupted part {c_idx}"
            f_dest.write(data)

final_size = os.path.getsize(dest)
print(f"Assembled file size: {final_size:,} bytes")
assert final_size == total_size, f"Size mismatch: {final_size} != {total_size}"

# Clean up part files
for c_idx, _, _ in chunks:
    part_path = os.path.join(parts_dir, f"chunk_{c_idx:03d}.part")
    if os.path.exists(part_path):
        os.remove(part_path)
if os.path.exists(parts_dir):
    os.rmdir(parts_dir)

# Calculate SHA-256
hasher = hashlib.sha256()
with open(dest, "rb") as f:
    for block in iter(lambda: f.read(1024*1024), b""):
        hasher.update(block)
sha = hasher.hexdigest()
print(f"Final SHA-256: {sha}")

# Astropy inspection of all 7 HDUs
print("\n--- Validating all HDUs with Astropy ---")
with fits.open(dest) as hdul:
    print(f"Total HDUs: {len(hdul)}")
    assert len(hdul) == 7, f"Expected 7 HDUs, got {len(hdul)}"
    for i, hdu in enumerate(hdul):
        shape = getattr(hdu, "shape", None)
        dtype = getattr(hdu, "data", None).dtype if getattr(hdu, "data", None) is not None else None
        print(f"  HDU {i}: Name={hdu.name:<12} Type={type(hdu).__name__:<16} Shape={str(shape):<16} Dtype={str(dtype)}")
        assert hdu.header is not None
    
    # Check each required HDU
    assert hdul[0].name == "PRIMARY"
    assert hdul[1].name == "IMAGE" and hdul[1].shape == (2040, 2040)
    assert hdul[2].name == "FLAGS" and hdul[2].shape == (2040, 2040)
    assert hdul[3].name == "VARIANCE" and hdul[3].shape == (2040, 2040)
    assert hdul[4].name == "ZODI" and hdul[4].shape == (2040, 2040)
    assert hdul[5].name == "EPSF"
    assert hdul[6].name == "WCS-WAVE"

print("\nCOMPLETE FITS VALIDATION: ALL 7 HDUS VALIDATED SUCCESSFULLY (PASS)")
