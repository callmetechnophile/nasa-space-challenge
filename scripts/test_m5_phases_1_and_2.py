import os
import sys
import numpy as np

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.astronomy.spherex_mef_reader import read_spherex_mef_product
from app.astronomy.quality_mask import create_quality_mask, FATAL_DEFECT_MASK, BIT_SOURCE

f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
f2 = "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"

print("--- Testing Phase 1 MEF Ingestion ---")
prod1 = read_spherex_mef_product(f1)
print(f"Epoch 1 loaded: shape={prod1.image.shape}, dtype={prod1.image.dtype}, sha256={prod1.sha256[:16]}...")
print(f"  Flags shape={prod1.flags.shape}, Variance shape={prod1.variance.shape}, Zodi shape={prod1.zodi.shape}")
print(f"  EPSF rows={len(prod1.epsf_table)}, WCS-WAVE values shape={prod1.wcs_wave_values.shape}")

prod2 = read_spherex_mef_product(f2)
print(f"Epoch 2 loaded: shape={prod2.image.shape}, dtype={prod2.image.dtype}, sha256={prod2.sha256[:16]}...")
print(f"  Flags shape={prod2.flags.shape}, Variance shape={prod2.variance.shape}, Zodi shape={prod2.zodi.shape}")
print(f"  EPSF rows={len(prod2.epsf_table)}, WCS-WAVE values shape={prod2.wcs_wave_values.shape}")

print("\n--- Testing Phase 2 Quality Masking ---")
q1 = create_quality_mask(prod1.image, prod1.flags, prod1.variance, fatal_bitmask=FATAL_DEFECT_MASK)
print(f"Epoch 1 Quality Mask Summary:")
print(f"  Total pixels: {q1['total_pixels']:,}")
print(f"  Fatal flag rejections: {q1['flag_rejection_count']:,}")
print(f"  NaN / Inf rejections: {q1['nan_rejection_count']:,}")
print(f"  Variance rejections: {q1['variance_rejection_count']:,}")
print(f"  Preserved catalog sources: {q1['source_pixel_count']:,}")
print(f"  Total bad pixels: {q1['total_bad_pixels']:,} ({q1['bad_pixel_fraction']*100:.3f}%)")
print(f"  Total good pixels: {np.sum(q1['good_mask']):,} ({q1['good_pixel_fraction']*100:.3f}%)")

q2 = create_quality_mask(prod2.image, prod2.flags, prod2.variance, fatal_bitmask=FATAL_DEFECT_MASK)
print(f"Epoch 2 Quality Mask Summary:")
print(f"  Total pixels: {q2['total_pixels']:,}")
print(f"  Fatal flag rejections: {q2['flag_rejection_count']:,}")
print(f"  NaN / Inf rejections: {q2['nan_rejection_count']:,}")
print(f"  Variance rejections: {q2['variance_rejection_count']:,}")
print(f"  Preserved catalog sources: {q2['source_pixel_count']:,}")
print(f"  Total bad pixels: {q2['total_bad_pixels']:,} ({q2['bad_pixel_fraction']*100:.3f}%)")
print(f"  Total good pixels: {np.sum(q2['good_mask']):,} ({q2['good_pixel_fraction']*100:.3f}%)")

# Verify that clean catalog sources (BIT_SOURCE with no fatal defects) are 100% preserved
source_clean_1 = ((prod1.flags.astype(np.int64) & BIT_SOURCE) != 0) & ((prod1.flags.astype(np.int64) & FATAL_DEFECT_MASK) == 0)
clean_sources_rejected_1 = np.sum(source_clean_1 & q1['bad_mask'])
print(f"\nVerification: Number of clean catalog sources rejected by fatal mask in Epoch 1: {clean_sources_rejected_1}")
assert clean_sources_rejected_1 == 0, f"Error: {clean_sources_rejected_1} clean catalog sources were incorrectly rejected!"
print("Verification SUCCESS: Clean catalog sources are 100% preserved.")
