import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath("backend"))
from app.astronomy.spherex_mef_reader import read_spherex_mef_product
from app.astronomy.quality_mask import create_quality_mask, FATAL_DEFECT_MASK, BIT_SOURCE

f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
prod1 = read_spherex_mef_product(f1)
flags = prod1.flags.astype(np.int64)

# Total source pixels:
has_source = (flags & BIT_SOURCE) != 0
print(f"Total pixels with BIT_SOURCE: {np.sum(has_source):,}")

# Pixels with BIT_SOURCE and NO fatal defect:
source_clean = has_source & ((flags & FATAL_DEFECT_MASK) == 0)
print(f"Clean catalog sources (no fatal defects): {np.sum(source_clean):,}")

# Pixels with BIT_SOURCE and fatal defects:
source_with_fatal = has_source & ((flags & FATAL_DEFECT_MASK) != 0)
print(f"Catalog sources with fatal defects (e.g. saturation, CR): {np.sum(source_with_fatal):,}")

# What fatal defects are present in source pixels?
for b in [0, 1, 2, 6, 11, 26, 27]:
    bit_val = 1 << b
    c = np.sum(has_source & ((flags & bit_val) != 0))
    if c > 0:
        print(f"  Bit {b} ({bit_val}): {c:,} source pixels")

q = create_quality_mask(prod1.image, prod1.flags, prod1.variance)
clean_sources_rejected = np.sum(source_clean & q['bad_mask'])
print(f"\nClean catalog sources rejected by quality mask: {clean_sources_rejected}")
assert clean_sources_rejected == 0
print("SUCCESS: 100% of clean catalog sources are preserved!")
