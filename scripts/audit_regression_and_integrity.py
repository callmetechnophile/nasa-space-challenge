import os
import hashlib
from pathlib import Path

files_to_check = [
    "backend/app/astronomy/fits_reader.py",
    "backend/app/astronomy/wcs_processor.py",
    "backend/app/astronomy/image_renderer.py",
    "backend/app/astronomy/image_footprint.py",
    "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
    "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits",
    "data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits"
]

print("=== AUDIT 6: REGRESSION AND SOURCE INTEGRITY CHECK ===")
for rel_path in files_to_check:
    p = Path(rel_path)
    if p.exists():
        data = p.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        size = len(data)
        mtime = p.stat().st_mtime
        print(f"File: {rel_path}")
        print(f"  Size: {size:,} bytes")
        print(f"  SHA-256: {sha}")
    else:
        print(f"File: {rel_path} MISSING!")
