import os
import sys
import hashlib
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u

sys.path.insert(0, 'backend')

def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

print("=== ITEM 2 & 3: FITS PROVENANCE & FLAGS AUDIT ===")
fits_files = [
    'data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits',
    'data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits',
    'data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits'
]

for fp in fits_files:
    sz = os.path.getsize(fp)
    sha = file_sha256(fp)
    print(f"\n--- File: {fp} ---")
    print(f"Size: {sz} bytes")
    print(f"SHA-256: {sha}")
    with fits.open(fp) as hdul:
        print(f"HDU count: {len(hdul)}")
        for i, hdu in enumerate(hdul):
            name = hdu.name
            bitpix = hdu.header.get('BITPIX')
            naxis = hdu.header.get('NAXIS')
            shape = hdu.data.shape if hdu.data is not None else None
            dtype = hdu.data.dtype if hdu.data is not None else None
            print(f"  HDU[{i}] {name}: BITPIX={bitpix}, NAXIS={naxis}, shape={shape}, dtype={dtype}")
        
        # Primary header inspection
        p_hdr = hdul[0].header
        keys = ['DATE-OBS', 'MJD-OBS', 'DATE-BEG', 'DATE-END', 'OBS_ID', 'OBSID', 'DETECTOR', 'VERSION', 'CAL_VER', 'CREATOR', 'HISTORY', 'COMMENT']
        print("  Primary header keys:")
        for k in keys:
            if k in p_hdr:
                print(f"    {k} = {p_hdr[k]}")
        # Image header inspection
        if 'IMAGE' in hdul:
            im_hdr = hdul['IMAGE'].header
            print("  IMAGE header keys:")
            for k in ['DATE-OBS', 'MJD-OBS', 'NAXIS1', 'NAXIS2', 'CTYPE1', 'CTYPE2', 'CRVAL1', 'CRVAL2', 'CUNIT1', 'CUNIT2']:
                if k in im_hdr:
                    print(f"    {k} = {im_hdr[k]}")
        # FLAGS HDU inspection
        if 'FLAGS' in hdul:
            fl_data = hdul['FLAGS'].data
            print("  FLAGS data stats:")
            print(f"    dtype={fl_data.dtype}, min={fl_data.min()}, max={fl_data.max()}")
            unique, counts = np.unique(fl_data, return_counts=True)
            print(f"    unique values (first 10): {list(zip(unique[:10], counts[:10]))}")

