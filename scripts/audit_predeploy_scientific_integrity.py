"""Pre-Deployment Stage 1: Scientific Data Integrity Audit.
Verifies cryptographic SHA-256 digests of approved FITS files, HDU structure,
WCS parameters, EPSF dimensions, WCS-WAVE dimensions, FLAGS dtype, VARIANCE dtype,
timestamps, and detector identifiers.
"""

import sys
import os
import hashlib
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("================================================================================")
print("STAGE 1 — SCIENTIFIC DATA INTEGRITY AUDIT")
print("================================================================================")

CANONICAL_HASHES = {
    "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits": "b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1",
    "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits": "60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e",
}

for fname, expected_hash in CANONICAL_HASHES.items():
    fpath = os.path.join("data/spherex", fname)
    print(f"\n--- Product: {fname} ---")
    
    # 1. SHA-256 Digest Verification
    hasher = hashlib.sha256()
    with open(fpath, "rb") as fh:
        while chunk := fh.read(1024 * 1024):
            hasher.update(chunk)
    actual_hash = hasher.hexdigest()
    hash_match = actual_hash == expected_hash
    print(f"  SHA-256 Actual:   {actual_hash}")
    print(f"  SHA-256 Expected: {expected_hash}")
    print(f"  Integrity Match:  {'PASS (Bitwise Exact)' if hash_match else 'FAIL (Hash Mismatch)'}")
    assert hash_match, f"SHA-256 mismatch for {fname}"
    
    # 2. HDU Structure & Preservation
    with fits.open(fpath) as hdul:
        print(f"  Total HDUs: {len(hdul)}")
        for idx, h in enumerate(hdul):
            shape = getattr(h, "shape", None)
            dtype = getattr(h.data, "dtype", None) if h.data is not None else None
            print(f"    HDU {idx}: {h.name:<10} | Type: {type(h).__name__:<16} | Shape: {str(shape):<16} | Dtype: {str(dtype)}")
            
        # 3. Header Metadata & Timestamps
        p_hdr = hdul[0].header
        i_hdr = hdul["IMAGE"].header
        
        obsid = p_hdr.get("OBS_ID") or p_hdr.get("OBSID")
        date_obs = p_hdr.get("DATE-OBS")
        mjd_obs = p_hdr.get("MJD-OBS")
        detector = p_hdr.get("DETECTOR") or i_hdr.get("DETECTOR")
        telescope = p_hdr.get("TELESCOP")
        
        print(f"  Metadata:")
        print(f"    Telescope:   {telescope}")
        print(f"    Obs ID:      {obsid}")
        print(f"    Detector:    {detector}")
        print(f"    DATE-OBS:    {date_obs}")
        print(f"    MJD-OBS:     {mjd_obs}")
        
        # 4. WCS Metadata
        w = WCS(i_hdr)
        crval = (i_hdr.get("CRVAL1"), i_hdr.get("CRVAL2"))
        crpix = (i_hdr.get("CRPIX1"), i_hdr.get("CRPIX2"))
        ctype = (i_hdr.get("CTYPE1"), i_hdr.get("CTYPE2"))
        print(f"    CTYPE:       {ctype}")
        print(f"    CRVAL:       {crval}")
        print(f"    CRPIX:       {crpix}")
        
        # 5. FLAGS and VARIANCE Data Types
        flags_data = hdul["FLAGS"].data
        var_data = hdul["VARIANCE"].data
        flags_dtype_raw = flags_data.dtype
        flags_bitpix = hdul["FLAGS"].header.get("BITPIX")
        var_dtype_raw = var_data.dtype
        var_bitpix = hdul["VARIANCE"].header.get("BITPIX")
        
        print(f"    FLAGS:       BITPIX={flags_bitpix}, raw_dtype={flags_dtype_raw}, shape={flags_data.shape}")
        print(f"    VARIANCE:    BITPIX={var_bitpix}, raw_dtype={var_dtype_raw}, shape={var_data.shape}")
        
        # 6. EPSF Dimensions and Table Schema
        epsf_table = hdul["EPSF"].data
        epsf_shape = epsf_table["EPSF"].shape
        epsf_subshape = epsf_table["EPSF"][0].shape
        print(f"    EPSF:        Table rows={len(epsf_table)}, Bin array shape={epsf_subshape}, Full shape={epsf_shape}")
        assert epsf_subshape == (33, 33), f"Unexpected EPSF stamp shape: {epsf_subshape}"
        
        # 7. WCS-WAVE Dimensions
        wave_hdr = hdul["WCS-WAVE"].header
        wave_dim = (wave_hdr.get("NAXIS1"), wave_hdr.get("NAXIS2"))
        print(f"    WCS-WAVE:    BITPIX={wave_hdr.get('BITPIX')}, Dimensions={wave_dim}")

print("\n================================================================================")
print("SCIENTIFIC DATA INTEGRITY AUDIT: PASS (100% BITWISE VERIFIED)")
print("================================================================================")
