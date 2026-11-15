import os
import sys

sys.path.insert(0, os.path.abspath("backend"))
from app.astronomy.spherex_mef_reader import read_spherex_mef_product
from app.astronomy.psf_matching import estimate_effective_fwhm, match_psf_pair

f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
f2 = "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"

p1 = read_spherex_mef_product(f1)
p2 = read_spherex_mef_product(f2)

fwhm1 = estimate_effective_fwhm(p1.epsf_table)
fwhm2 = estimate_effective_fwhm(p2.epsf_table)

print(f"Epoch 1 EPSF FWHM: {fwhm1:.3f} pixels")
print(f"Epoch 2 EPSF FWHM: {fwhm2:.3f} pixels")
