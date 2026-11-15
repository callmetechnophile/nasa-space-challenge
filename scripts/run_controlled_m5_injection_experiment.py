import os
import sys
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS

sys.path.insert(0, 'backend')
from app.astronomy.spherex_psf import CALIB_DIR, select_spatially_varying_epsf
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates

def wilson_score_interval(k, n, z=1.95996):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    half = (z * np.sqrt((p * (1.0 - p)) / n + (z**2) / (4 * (n**2)))) / denom
    lower = max(0.0, center - half)
    upper = min(1.0, center + half)
    return p, lower, upper

# 1. Load authentic calibrated FITS background and variance
fits_path = 'data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits'
with fits.open(fits_path) as hdul:
    real_img = hdul['IMAGE'].data
    real_var = hdul['VARIANCE'].data
    real_flg = hdul['FLAGS'].data
    w = WCS(hdul['IMAGE'].header)

# Select a clean 512x512 subregion away from borders
# Region [700:1212, 700:1212] around detector center
y0, y1 = 700, 1212
x0, x1 = 700, 1212
base_img1 = np.array(real_img[y0:y1, x0:x1], dtype=np.float32)
base_var1 = np.array(real_var[y0:y1, x0:x1], dtype=np.float32)
base_flg1 = np.array(real_flg[y0:y1, x0:x1], dtype=np.int32)

# Load authentic D1 ePSF calibration model at region center (956, 956)
d1_calib_path = os.path.join(CALIB_DIR, "epsf_D1_spx_cal-epsf-v1-2026-191.fits")
with fits.open(d1_calib_path) as hdul:
    epsf_tab = Table.read(hdul['EPSF'])
zone_info = select_spatially_varying_epsf(epsf_tab, parent_x=956.0, parent_y=956.0)
kernel = np.array(zone_info['kernel'], dtype=np.float64)
# Downsample or normalize kernel to pixel grid (33x33 subpixel kernel -> 9x9 pixel kernel or central sum=1)
# Note: SPHEREx ePSF tables are 33x33. Let's inspect peak and sum
kernel_norm = kernel / np.sum(kernel)
k_h = kernel_norm.shape[0] // 2
k_max = float(np.max(kernel_norm))
sum_p2 = float(np.sum(kernel_norm**2))

print(f"ePSF Kernel shape: {kernel_norm.shape}, peak: {k_max:.6f}, sum(P_i^2): {sum_p2:.6f}")

# Target SNR levels
snr_levels = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 50.0]
n_trials = 30
seed = 20261115
rng = np.random.default_rng(seed)

results = []

for case in ["ISOLATED", "CROWDED"]:
    for polarity in ["POSITIVE", "NEGATIVE"]:
        for snr_target in snr_levels:
            recovered_count = 0
            flux_biases = []
            flux_scatters = []
            pos_errors = []
            false_detections_count = 0
            peak_snrs = []
            
            for trial in range(n_trials):
                img1 = base_img1.copy()
                var1 = base_var1.copy()
                img2 = base_img1.copy()
                var2 = base_var1.copy()
                
                # In difference imaging: Var(diff) = var1 + var2
                diff_var = var1 + var2
                
                # Pick injection coordinate
                if case == "ISOLATED":
                    # Find a quiet pixel with low local flux
                    # Pick randomly in safe interior
                    ix = rng.integers(k_h + 20, 512 - k_h - 20)
                    iy = rng.integers(k_h + 20, 512 - k_h - 20)
                else: # CROWDED
                    # Place near an existing star or structure
                    ix = rng.integers(k_h + 20, 512 - k_h - 20)
                    iy = rng.integers(k_h + 20, 512 - k_h - 20)
                    # Add an un-subtracted companion star at 3 pixels separation
                    comp_flux = 5.0 * np.sqrt(diff_var[iy, ix])
                    img1[iy-2:iy+3, ix-2:ix+3] += comp_flux * 0.2
                    img2[iy-2:iy+3, ix-2:ix+3] += comp_flux * 0.2
                
                # Local noise variance for matched-filter calculation
                v_patch = diff_var[iy - k_h : iy - k_h + kernel_norm.shape[0], ix - k_h : ix - k_h + kernel_norm.shape[1]]
                if v_patch.shape != kernel_norm.shape or np.any(v_patch <= 0):
                    v_local = float(np.median(diff_var))
                    inv_v_sum = np.sum(kernel_norm**2) / v_local
                else:
                    inv_v_sum = np.sum((kernel_norm**2) / v_patch)
                    
                mf_denominator = np.sqrt(inv_v_sum)
                # Injected total flux F for desired Matched-Filter SNR:
                F_inj = snr_target / mf_denominator
                
                # Calculate corresponding Peak-Pixel SNR:
                # Peak pixel flux is F_inj * max(P_i)
                # Local pixel sigma is sqrt(diff_var at center)
                v_center = diff_var[iy, ix]
                snr_peak = (F_inj * k_max) / np.sqrt(v_center)
                peak_snrs.append(snr_peak)
                
                # Inject into img2
                sign = +1.0 if polarity == "POSITIVE" else -1.0
                stamp = sign * F_inj * kernel_norm
                
                img2[iy - k_h : iy - k_h + kernel_norm.shape[0], ix - k_h : ix - k_h + kernel_norm.shape[1]] += stamp
                
                # Run production difference engine and change detection
                diff_res = compute_difference_and_significance(img1, var1, img2, var2, subtract_residual_background=False)
                c_res = extract_change_candidates(
                    significance_map=diff_res["significance_map"],
                    difference_image=diff_res["difference_image"],
                    significance_threshold=3.5,
                    min_area_pixels=3,
                )
                
                # Check recovery: match candidate within 3.0 pixels of (ix, iy) with correct polarity
                matched = False
                matched_cand = None
                for c in c_res["candidates"]:
                    dist = np.hypot(c["pixel_x"] - ix, c["pixel_y"] - iy)
                    if dist <= 3.0 and c["polarity"] == polarity:
                        matched = True
                        matched_cand = c
                        break
                        
                if matched:
                    recovered_count += 1
                    dist = np.hypot(matched_cand["pixel_x"] - ix, matched_cand["pixel_y"] - iy)
                    pos_errors.append(dist)
                    meas_flux = abs(matched_cand["integrated_flux_mjy_sr"])
                    flux_biases.append((meas_flux - F_inj) / F_inj)
                
                # False detections: candidates > 10 pixels away from injection
                false_cands = [c for c in c_res["candidates"] if np.hypot(c["pixel_x"] - ix, c["pixel_y"] - iy) > 10.0]
                false_detections_count += len(false_cands)
                
            p_comp, ci_low, ci_high = wilson_score_interval(recovered_count, n_trials)
            mean_bias = float(np.mean(flux_biases)) if flux_biases else 0.0
            std_flux = float(np.std(flux_biases)) if flux_biases else 0.0
            mean_pos_err = float(np.mean(pos_errors)) if pos_errors else 0.0
            mean_snr_peak = float(np.mean(peak_snrs))
            
            results.append({
                "case": case,
                "polarity": polarity,
                "snr_mf": snr_target,
                "snr_peak": mean_snr_peak,
                "trials": n_trials,
                "recovered": recovered_count,
                "completeness": p_comp,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "flux_bias": mean_bias,
                "flux_scatter": std_flux,
                "pos_err_px": mean_pos_err,
                "false_cands_total": false_detections_count,
                "false_rate_per_trial": false_detections_count / n_trials,
            })
            print(f"[{case:8s}] {polarity:8s} | SNR_MF={snr_target:4.1f} (SNR_peak={mean_snr_peak:4.1f}) | Comp={p_comp*100:5.1f}% [{ci_low*100:4.1f}%, {ci_high*100:4.1f}%] | FluxBias={mean_bias*100:+5.1f}% | Scatter={std_flux*100:4.1f}% | PosErr={mean_pos_err:.2f}px | False={false_detections_count}")

import json
with open('scripts/m5_injection_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nSaved results to scripts/m5_injection_results.json")
