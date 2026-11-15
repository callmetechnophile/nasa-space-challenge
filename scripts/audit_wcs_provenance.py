import os
import sys
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

files = [
    "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
    "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"
]

print("=== AUDIT 1: FITS PROVENANCE AND WCS EXTRACTION ===")
for fpath in files:
    fname = os.path.basename(fpath)
    print(f"\n--- File: {fname} ---")
    with fits.open(fpath) as hdul:
        print(f"Total HDUs: {len(hdul)}")
        for idx, h in enumerate(hdul):
            print(f"  HDU {idx}: name={h.name}, type={type(h).__name__}")

        p_hdr = hdul[0].header
        i_hdr = hdul["IMAGE"].header

        print("\nPrimary Header Provenance & Pointing:")
        for k in ["TELESCOP", "INSTRUME", "OBSID", "OBS_ID", "DETECTOR", "DATE-OBS", "MJD-OBS", "RA_PNT", "DEC_PNT", "PA_PNT", "BUNIT"]:
            print(f"  {k}: {p_hdr.get(k)}")

        print("\nIMAGE HDU Celestial WCS Parameters:")
        wcs_keys = [
            "CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CTYPE1", "CTYPE2",
            "CUNIT1", "CUNIT2", "CDELT1", "CDELT2",
            "PC1_1", "PC1_2", "PC2_1", "PC2_2",
            "CD1_1", "CD1_2", "CD2_1", "CD2_2",
            "A_ORDER", "B_ORDER", "AP_ORDER", "BP_ORDER",
            "DETECTOR", "DATE-OBS", "MJD-OBS", "BUNIT", "EQUINOX", "RADESYS"
        ]
        for k in wcs_keys:
            val = i_hdr.get(k)
            if val is not None:
                print(f"  {k}: {val}")

        # SIP sample coefficients
        print("\nSIP Coefficients Sample:")
        for prefix in ["A_", "B_", "AP_", "BP_"]:
            for i in range(3):
                for j in range(3):
                    key = f"{prefix}{i}_{j}"
                    val = i_hdr.get(key)
                    if val is not None and val != 0.0:
                        print(f"  {key} = {val}")

        # Evaluate Astropy WCS
        w = WCS(i_hdr)
        pix_center = [1020.5, 1020.5]
        ra_ref, dec_ref = w.all_pix2world([pix_center], 1)[0]
        print(f"\nCalculated Image Center Pixel (1020.5, 1020.5):")
        print(f"  RA = {ra_ref:.8f} deg, Dec = {dec_ref:.8f} deg")

        # Corners
        corners = w.all_pix2world([[1, 1], [2040, 1], [2040, 2040], [1, 2040]], 1)
        print("Calculated Detector Corners (1-based [x, y]):")
        for c_idx, (r, d) in enumerate(corners):
            print(f"  Corner {c_idx+1}: RA={r:.6f} deg, Dec={d:.6f} deg")
