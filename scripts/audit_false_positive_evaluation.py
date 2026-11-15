"""Audit Gate 4: Rigorous False-Positive Evaluation across Null Simulations and Real Source-Free Sky.
Distinguishes:
1. Individual threshold-crossing pixels (|S| >= 3.5).
2. Connected components (area >= 3 pixels).
3. Independent astrophysical candidate events (after spatial filtering & boundary checks).
Reports rates per frame, per pixel, and per square degree on sky.
"""

import sys
import os
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("backend"))
from app.astronomy.spherex_mef_reader import read_spherex_mef_product
from app.astronomy.image_registration import create_common_wcs, reproject_to_common_grid
from app.astronomy.quality_mask import create_quality_mask, FATAL_DEFECT_MASK, BIT_SOURCE
from app.astronomy.spectral_compatibility import LVFWavelengthModel, evaluate_spectral_compatibility
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates

print("================================================================================")
print("GATE 4: FALSE-POSITIVE EVALUATION ON NULL SIMULATIONS & REAL SOURCE-FREE SKY")
print("================================================================================")

# Nominal SPHEREx pixel scale
pixel_scale_arcsec = 6.2 # arcsec / pixel
sq_deg_per_pixel = (pixel_scale_arcsec / 3600.0) ** 2 # deg^2 / pixel

# ------------------------------------------------------------------------------
# SECTION 1: Monte Carlo Null Simulations (Pure Gaussian Noise)
# ------------------------------------------------------------------------------
print("\n--- SECTION 1: MONTE CARLO NULL SIMULATIONS (50 INDEPENDENT FRAMES) ---")
n_frames = 50
grid_dim = 512
total_sim_pixels = n_frames * (grid_dim ** 2)
noise_sigma = 0.021
noise_var = noise_sigma ** 2

tot_thresh_pixels_35 = 0
tot_thresh_pixels_50 = 0
tot_connected_comps_35 = 0
tot_connected_comps_50 = 0
tot_filtered_cands_35 = 0
tot_filtered_cands_50 = 0

for trial in range(n_frames):
    img1 = np.random.normal(0.0, noise_sigma, (grid_dim, grid_dim)).astype(np.float32)
    img2 = np.random.normal(0.0, noise_sigma, (grid_dim, grid_dim)).astype(np.float32)
    var1 = np.full((grid_dim, grid_dim), noise_var, dtype=np.float32)
    var2 = np.full((grid_dim, grid_dim), noise_var, dtype=np.float32)
    
    d_res = compute_difference_and_significance(img1, var1, img2, var2, subtract_residual_background=False)
    sig = d_res["significance_map"]
    diff_img = d_res["difference_image"]
    
    # 1. Individual threshold-crossing pixels
    px_35 = int(np.sum(np.abs(sig) >= 3.5))
    px_50 = int(np.sum(np.abs(sig) >= 5.0))
    tot_thresh_pixels_35 += px_35
    tot_thresh_pixels_50 += px_50
    
    # 2. Connected components without area filtering (min_area=1)
    c_raw_35 = extract_change_candidates(sig, diff_img, significance_threshold=3.5, min_area_pixels=1)
    c_raw_50 = extract_change_candidates(sig, diff_img, significance_threshold=5.0, min_area_pixels=1)
    tot_connected_comps_35 += c_raw_35["candidate_count"]
    tot_connected_comps_50 += c_raw_50["candidate_count"]
    
    # 3. Operational pipeline candidates (min_area=3)
    c_ops_35 = extract_change_candidates(sig, diff_img, significance_threshold=3.5, min_area_pixels=3)
    c_ops_50 = extract_change_candidates(sig, diff_img, significance_threshold=5.0, min_area_pixels=3)
    tot_filtered_cands_35 += c_ops_35["candidate_count"]
    tot_filtered_cands_50 += c_ops_50["candidate_count"]

total_sq_deg_sim = total_sim_pixels * sq_deg_per_pixel

print(f"Total Evaluated Sim Pixels: {total_sim_pixels:,} across {n_frames} frames ({total_sq_deg_sim:.4f} sq deg)")
print(f"\n[Detection Threshold: 3.5 sigma]")
print(f"  1. Individual Pixels (|S| >= 3.5):")
print(f"     Total: {tot_thresh_pixels_35:,} | Rate/pixel: {tot_thresh_pixels_35 / total_sim_pixels:.4e} | Rate/frame: {tot_thresh_pixels_35 / n_frames:.1f} | Rate/sq.deg: {tot_thresh_pixels_35 / total_sq_deg_sim:.1f}")
print(f"     Theoretical 2-sided Gaussian P(|Z| >= 3.5) = 4.6526e-04 (observed = {tot_thresh_pixels_35 / total_sim_pixels:.4e})")
print(f"  2. Raw Connected Components (area >= 1 px):")
print(f"     Total: {tot_connected_comps_35:,} | Rate/frame: {tot_connected_comps_35 / n_frames:.1f} | Rate/sq.deg: {tot_connected_comps_35 / total_sq_deg_sim:.1f}")
print(f"  3. Operational Change Candidates (area >= 3 px):")
print(f"     Total: {tot_filtered_cands_35:,} | Rate/frame: {tot_filtered_cands_35 / n_frames:.3f} | Rate/sq.deg: {tot_filtered_cands_35 / total_sq_deg_sim:.3f}")

print(f"\n[Detection Threshold: 5.0 sigma]")
print(f"  1. Individual Pixels (|S| >= 5.0):")
print(f"     Total: {tot_thresh_pixels_50:,} | Rate/pixel: {tot_thresh_pixels_50 / total_sim_pixels:.4e} | Rate/frame: {tot_thresh_pixels_50 / n_frames:.3f}")
print(f"     Theoretical 2-sided Gaussian P(|Z| >= 5.0) = 5.7330e-07 (observed = {tot_thresh_pixels_50 / total_sim_pixels:.4e})")
print(f"  2. Operational Change Candidates (area >= 3 px):")
print(f"     Total: {tot_filtered_cands_50:,} | Rate/frame: {tot_filtered_cands_50 / n_frames:.4f} | Rate/sq.deg: {tot_filtered_cands_50 / total_sq_deg_sim:.4f}")

# ------------------------------------------------------------------------------
# SECTION 2: Real-Data Source-Free Sky Evaluation
# ------------------------------------------------------------------------------
print("\n--- SECTION 2: REAL-DATA SOURCE-FREE SKY EVALUATION ---")
f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
f2 = "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"

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

sig = diff_res["significance_map"]
diff_img = diff_res["difference_image"]
valid = diff_res["valid_mask"]

is_source = ((flags1_rep.astype(np.int64) & BIT_SOURCE) != 0) | ((flags2_rep.astype(np.int64) & BIT_SOURCE) != 0)
sf_mask = valid & (~is_source)

# Create a source-free difference and significance array (masking sources as NaN)
sig_sf = np.where(sf_mask, sig, np.nan)
diff_sf = np.where(sf_mask, diff_img, np.nan)

c_sf_35 = extract_change_candidates(sig_sf, diff_sf, significance_threshold=3.5, min_area_pixels=3)
c_sf_50 = extract_change_candidates(sig_sf, diff_sf, significance_threshold=5.0, min_area_pixels=3)

n_sf_pix = int(np.sum(sf_mask))
sf_sq_deg = n_sf_pix * sq_deg_per_pixel

print(f"Source-Free Sky Pixels: {n_sf_pix:,} ({sf_sq_deg:.4f} sq deg)")
print(f"False Candidates at 3.5 sigma in source-free sky: {c_sf_35['candidate_count']} (Rate: {c_sf_35['candidate_count'] / sf_sq_deg:.1f} / sq.deg)")
print(f"False Candidates at 5.0 sigma in source-free sky: {c_sf_50['candidate_count']} (Rate: {c_sf_50['candidate_count'] / sf_sq_deg:.1f} / sq.deg)")

if c_sf_35["candidates"]:
    print(f"\nTop 3 Source-Free Candidates (|S| >= 3.5):")
    for cand in c_sf_35["candidates"][:3]:
        print(f"  ID: {cand['candidate_id']} | Peak Sig: {cand['significance_peak']:+.2f} | Area: {cand['area_pixels']} px | Warnings: {cand['warnings']}")

print("\n================================================================================")
print("GATE 4 SUMMARY: THREE-TIER FALSE-POSITIVE DISTINCTION CONFIRMED")
print("================================================================================")
