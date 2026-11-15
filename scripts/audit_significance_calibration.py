import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath("backend"))
from app.services.temporal_service import TemporalService

f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
f2 = "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"

service = TemporalService()
print("Executing Temporal Difference Pipeline to retrieve full arrays...")
res = service.run_difference_pipeline(
    fits_path_1=f1,
    fits_path_2=f2,
    significance_threshold=3.5,
    spectral_tolerance=0.02,
    grid_size=512,
    subtract_background=True,
)

# To analyze the raw arrays directly, let's run the internal steps to get D, sigma_D, and S
from app.astronomy.spherex_mef_reader import read_spherex_mef_product
from app.astronomy.image_registration import create_common_wcs, reproject_to_common_grid
from app.astronomy.quality_mask import create_quality_mask, FATAL_DEFECT_MASK, BIT_SOURCE
from app.astronomy.spectral_compatibility import LVFWavelengthModel, evaluate_spectral_compatibility
from app.astronomy.difference_engine import compute_difference_and_significance

p1 = read_spherex_mef_product(f1)
p2 = read_spherex_mef_product(f2)

ra_center = 0.5 * (p1.wcs.wcs.crval[0] + p2.wcs.wcs.crval[0])
dec_center = 0.5 * (p1.wcs.wcs.crval[1] + p2.wcs.wcs.crval[1])
target_wcs = create_common_wcs(ra_center, dec_center, pixel_scale_deg=0.0017222, npix_x=512, npix_y=512)

rep1 = reproject_to_common_grid(p1.image, p1.variance, p1.wcs, target_wcs, target_shape=(512, 512))
rep2 = reproject_to_common_grid(p2.image, p2.variance, p2.wcs, target_wcs, target_shape=(512, 512))

flags1_rep = reproject_to_common_grid(p1.flags.astype(np.float32), None, p1.wcs, target_wcs, target_shape=(512, 512), order=0)["image"]
flags2_rep = reproject_to_common_grid(p2.flags.astype(np.float32), None, p2.wcs, target_wcs, target_shape=(512, 512), order=0)["image"]

q1 = create_quality_mask(rep1["image"], flags1_rep, rep1["variance"], fatal_bitmask=FATAL_DEFECT_MASK)
q2 = create_quality_mask(rep2["image"], flags2_rep, rep2["variance"], fatal_bitmask=FATAL_DEFECT_MASK)

wm1 = LVFWavelengthModel(p1.wcs_wave_x, p1.wcs_wave_y, p1.wcs_wave_values)
wm2 = LVFWavelengthModel(p2.wcs_wave_x, p2.wcs_wave_y, p2.wcs_wave_values)
spec = evaluate_spectral_compatibility(wm1, wm2, rep1["source_x"], rep1["source_y"], rep2["source_x"], rep2["source_y"])

diff_res = compute_difference_and_significance(
    rep1["image"], rep1["variance"],
    rep2["image"], rep2["variance"],
    bad_mask1=q1["bad_mask"],
    bad_mask2=q2["bad_mask"],
    spectrally_compatible_mask=spec["compatible_mask"],
    subtract_residual_background=True
)

diff = diff_res["difference_image"]
diff_sig = diff_res["diff_sigma"]
sig = diff_res["significance_map"]
valid = diff_res["valid_mask"]

# Identify source pixels from either epoch
is_source_1 = (flags1_rep.astype(np.int64) & BIT_SOURCE) != 0
is_source_2 = (flags2_rep.astype(np.int64) & BIT_SOURCE) != 0
source_mask = is_source_1 | is_source_2
source_free_mask = valid & (~source_mask)

print("\n=== AUDIT 3: REAL-DATA SIGNIFICANCE DISPERSION INVESTIGATION ===")
print(f"Overall Valid Pixels: {np.sum(valid):,} / {valid.size:,}")
print(f"Overall Difference Std: {np.nanstd(diff):.4f} MJy/sr")
print(f"Overall Expected Noise Mean (sigma_D): {np.nanmean(diff_sig):.4f} MJy/sr")
print(f"Overall Expected Noise Median: {np.nanmedian(diff_sig):.4f} MJy/sr")
print(f"Overall Significance Mean: {np.nanmean(sig):.5f}")
print(f"Overall Significance Std: {np.nanstd(sig):.4f}")

print(f"\nSource-Free Sky Pixels: {np.sum(source_free_mask):,} ({np.sum(source_free_mask)/np.sum(valid)*100:.1f}% of valid)")
diff_sf = diff[source_free_mask]
sig_sf = sig[source_free_mask]
diff_sig_sf = diff_sig[source_free_mask]

print(f"Source-Free Difference Std: {np.std(diff_sf):.4f} MJy/sr")
print(f"Source-Free Expected Noise Mean: {np.mean(diff_sig_sf):.4f} MJy/sr")
print(f"Source-Free Significance Mean: {np.mean(sig_sf):.5f}")
print(f"Source-Free Significance Std: {np.std(sig_sf):.4f}")

# Define 4 distinct source-free patches (e.g. 64x64 boxes)
boxes = [
    ("Region 1 (Top-Left)", 50, 114, 50, 114),
    ("Region 2 (Top-Right)", 50, 114, 398, 462),
    ("Region 3 (Bottom-Left)", 398, 462, 50, 114),
    ("Region 4 (Center-South)", 300, 364, 224, 288),
]

def calc_autocorr(patch):
    """Compute spatial autocorrelation at lag 1 in x and y."""
    valid_p = np.isfinite(patch)
    if np.sum(valid_p) < 20:
        return 0.0, 0.0
    p = patch - np.nanmean(patch)
    # lag 1 x
    p0 = p[:, :-1]
    p1 = p[:, 1:]
    v = valid_p[:, :-1] & valid_p[:, 1:]
    corr_x = np.sum(p0[v] * p1[v]) / (np.sqrt(np.sum(p0[v]**2) * np.sum(p1[v]**2)) + 1e-12)
    # lag 1 y
    p0_y = p[:-1, :]
    p1_y = p[1:, :]
    v_y = valid_p[:-1, :] & valid_p[1:, :]
    corr_y = np.sum(p0_y[v_y] * p1_y[v_y]) / (np.sqrt(np.sum(p0_y[v_y]**2) * np.sum(p1_y[v_y]**2)) + 1e-12)
    return float(corr_x), float(corr_y)

print("\n--- Detailed Source-Free Sky Sub-Regions ---")
for name, y0, y1, x0, x1 in boxes:
    sub_d = diff[y0:y1, x0:x1]
    sub_sig = sig[y0:y1, x0:x1]
    sub_dsig = diff_sig[y0:y1, x0:x1]
    sub_sf = source_free_mask[y0:y1, x0:x1]
    total_p = sub_sf.size
    n_valid = int(np.sum(sub_sf))
    masked_frac = float(1.0 - n_valid / total_p)

    if n_valid > 10:
        d_vals = sub_d[sub_sf]
        s_vals = sub_sig[sub_sf]
        pred_sigma = float(np.mean(sub_dsig[sub_sf]))
        obs_std = float(np.std(d_vals))
        mean_d = float(np.mean(d_vals))
        mean_s = float(np.mean(s_vals))
        std_s = float(np.std(s_vals))
        cx, cy = calc_autocorr(np.where(sub_sf, sub_d, np.nan))
    else:
        obs_std = pred_sigma = mean_d = mean_s = std_s = cx = cy = 0.0

    print(f"\n{name} [y={y0}:{y1}, x={x0}:{x1}]:")
    print(f"  Valid source-free pixels: {n_valid} / {total_p} (Masked fraction: {masked_frac*100:.1f}%)")
    print(f"  Mean difference: {mean_d:+.5f} MJy/sr")
    print(f"  Observed difference std: {obs_std:.5f} MJy/sr")
    print(f"  Predicted std from FITS VARIANCE: {pred_sigma:.5f} MJy/sr")
    print(f"  Std ratio (Observed / Predicted): {obs_std / (pred_sigma + 1e-12):.3f}")
    print(f"  Significance mean: {mean_s:+.5f}")
    print(f"  Significance std: {std_s:.4f}")
    print(f"  Spatial autocorrelation: lag-1 X = {cx:.3f}, lag-1 Y = {cy:.3f}")
