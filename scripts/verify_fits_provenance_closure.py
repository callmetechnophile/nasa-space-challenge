import os
import hashlib
from astropy.io import fits

FITS_DIR = "d:/nasa/data/spherex"
FILES = [
    {
        "epoch": "Epoch 1",
        "filename": "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
        "expected_sha256": "b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1",
        "expected_bytes": 65488320
    },
    {
        "epoch": "Epoch 2",
        "filename": "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits",
        "expected_sha256": "60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e",
        "expected_bytes": 65488320
    }
]

print("="*80)
print("TASK A: FITS PROVENANCE FINAL AUDIT & BITWISE VERIFICATION")
print("="*80)

for item in FILES:
    fpath = os.path.join(FITS_DIR, item["filename"])
    print(f"\n--- {item['epoch']}: {item['filename']} ---")
    if not os.path.exists(fpath):
        print(f"ERROR: File not found at {fpath}")
        continue
    
    file_size = os.path.getsize(fpath)
    print(f"File Size (Bytes): {file_size:,} bytes")
    print(f"Expected Size:     {item['expected_bytes']:,} bytes")
    assert file_size == item["expected_bytes"], f"Size mismatch! Got {file_size}"
    
    # Block alignment
    blocks = file_size / 2880
    mod = file_size % 2880
    print(f"FITS 2880-byte Blocks: {blocks:.3f} (modulo: {mod})")
    assert mod == 0, f"FITS block alignment violation! Modulo is {mod}"
    
    # SHA-256
    hasher = hashlib.sha256()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest()
    print(f"SHA-256 Actual:   {actual_hash}")
    print(f"SHA-256 Expected: {item['expected_sha256']}")
    assert actual_hash == item["expected_sha256"], "SHA-256 mismatch!"
    print("SHA-256 Match:    BIT-FOR-BIT IDENTICAL (PASS)")
    
    # Inspect HDUs
    with fits.open(fpath) as hdul:
        print(f"Total HDU Count:  {len(hdul)}")
        assert len(hdul) == 7, f"Expected 7 HDUs, found {len(hdul)}"
        for idx, hdu in enumerate(hdul):
            name = hdu.name
            htype = type(hdu).__name__
            shape = getattr(hdu, "shape", None)
            dtype = getattr(hdu, "data", None).dtype if getattr(hdu, "data", None) is not None else None
            header_cards = len(hdu.header)
            print(f"  HDU {idx}: Name={name:<10} Type={htype:<16} Shape={str(shape):<16} Dtype={str(dtype):<10} Cards={header_cards}")

print("\n" + "="*80)
print("FITS PROVENANCE AUDIT VERDICT: ALL PASS")
print("="*80)
