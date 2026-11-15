import os
import sys
import glob
import hashlib
import numpy as np
from astropy.io import fits
from astropy.table import Table

sys.path.insert(0, 'backend')
from app.astronomy.spherex_psf import CALIB_DIR

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

cal_files = sorted(glob.glob(os.path.join(CALIB_DIR, "epsf_D*.fits")))
print(f"Inspecting {len(cal_files)} calibration files:")

for cf in cal_files:
    fname = os.path.basename(cf)
    sz = os.path.getsize(cf)
    sha = get_sha256(cf)
    print(f"\n=======================================================")
    print(f"File: {fname}")
    print(f"Size: {sz:,} bytes | SHA-256: {sha}")
    
    with fits.open(cf) as hdul:
        print("HDU Inventory:")
        for idx, h in enumerate(hdul):
            print(f"  HDU[{idx}] {h.name}: BITPIX={h.header.get('BITPIX')}, NAXIS={h.header.get('NAXIS')}")
        
        # Check Primary Header
        p_hdr = hdul[0].header
        keys = ['VERSION', 'CAL_VER', 'DETECTOR', 'OVERSAMP', 'SAMPLING', 'PIXSCALE', 'GRIDSIZE', 'NZONES', 'CREATOR', 'DATE']
        print("Primary Header metadata:")
        for k in keys:
            if k in p_hdr:
                print(f"  {k} = {p_hdr[k]}")
                
        # Check EPSF table
        epsf_hdu = hdul['EPSF']
        e_hdr = epsf_hdu.header
        print("EPSF Header metadata:")
        for k in keys + ['OVERSAMP', 'OVERSMPL', 'OSAMP', 'SAMPFAC', 'NAXIS1', 'NAXIS2', 'TFIELDS']:
            if k in e_hdr:
                print(f"  {k} = {e_hdr[k]}")
                
        tab = Table.read(epsf_hdu)
        print(f"Table dimensions: {len(tab)} rows x {len(tab.colnames)} columns")
        print(f"Columns: {tab.colnames}")
        
        # Kernel array shape & dtype
        k0 = tab['EPSF'][0]
        print(f"Kernel array shape: {k0.shape}, dtype: {k0.dtype}")
        
        # Check kernel normalizations across all zones
        k_sums = [np.sum(tab['EPSF'][i]) for i in range(len(tab))]
        k_peaks = [np.max(tab['EPSF'][i]) for i in range(len(tab))]
        print(f"Kernel sum across all {len(tab)} zones: min={np.min(k_sums):.6f}, max={np.max(k_sums):.6f}, mean={np.mean(k_sums):.6f}")
        print(f"Kernel peak across all {len(tab)} zones: min={np.min(k_peaks):.6f}, max={np.max(k_peaks):.6f}, mean={np.mean(k_peaks):.6f}")
        
        # Zone coordinate ranges
        x_min, x_max = np.min(tab['XCENTER']), np.max(tab['XCENTER'])
        y_min, y_max = np.min(tab['YCENTER']), np.max(tab['YCENTER'])
        binx_min, binx_max = np.min(tab['BINX']), np.max(tab['BINX'])
        biny_min, biny_max = np.min(tab['BINY']), np.max(tab['BINY'])
        print(f"XCENTER range: [{x_min:.2f}, {x_max:.2f}], YCENTER range: [{y_min:.2f}, {y_max:.2f}]")
        print(f"BINX range: [{binx_min}, {binx_max}], BINY range: [{biny_min}, {biny_max}]")
        
        # Check unique bin grid
        unique_binx = np.unique(tab['BINX'])
        unique_biny = np.unique(tab['BINY'])
        print(f"Unique BINX count: {len(unique_binx)}, Unique BINY count: {len(unique_biny)}")
