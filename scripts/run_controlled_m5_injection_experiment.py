import os
import sys
import json
import numpy as np
from astropy.io import fits
from astropy.table import Table

sys.path.insert(0, 'backend')
from app.astronomy.spherex_psf import CALIB_DIR, select_spatially_varying_epsf, integrate_epsf_to_native
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

# Subregion 512x512 [700:1212, 700:1212] around detector center
y0, y1 = 700, 1212
x0, x1 = 700, 1212
base_img1 = np.array(real_img[y0:y1, x0:x1], dtype=np.float32)
base_var1 = np.array(real_var[y0:y1, x0:x1], dtype=np.float32)
base_flg1 = np.array(real_flg[y0:y1, x0:x1], dtype=np.int32)

# 2. Load authentic D1 ePSF calibration model at region center (956, 956)
d1_calib_path = os.path.join(CALIB_DIR, "epsf_D1_spx_cal-epsf-v1-2026-191.fits")
with fits.open(d1_calib_path) as hdul:
    epsf_tab = Table.read(hdul['EPSF'])
zone_info = select_spatially_varying_epsf(epsf_tab, parent_x=956.0, parent_y=956.0)

# Native 7x7 pixel-integrated PSF
kernel_native = zone_info['native_kernel'] # shape (7, 7)
k_h = kernel_native.shape[0] // 2
k_max = float(np.max(kernel_native))
sum_p2 = float(np.sum(kernel_native**2))
peak_snr_ratio = k_max / np.sqrt(sum_p2)

print(f"Native PSF shape: {kernel_native.shape}, peak: {k_max:.6f}, sum(P^2): {sum_p2:.6f}, Peak/MF ratio: {peak_snr_ratio:.4f}")

# Target SNR levels
snr_levels = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 50.0]
n_trials = 50
seed = 20261115
rng = np.random.default_rng(seed)

results = []

print("\nRunning Corrected M5 Controlled Injection/Recovery Experiment (N=50 per level)...")

for case in ["ISOLATED", "CROWDED"]:
    for polarity in ["POSITIVE", "NEGATIVE"]:
        for snr_target in snr_levels:
            recovered_count = 0
            psf_flux_biases = []
            iso_flux_biases = []
            pos_errors = []
            false_detections_count = 0
            peak_snrs = []
            
            for trial in range(n_trials):
                img1 = base_img1.copy()
                var1 = base_var1.copy()
                img2 = base_img1.copy()
                var2 = base_var1.copy()
                
                diff_var = var1 + var2
                
                # Pick injection coordinate
                if case == "ISOLATED":
                    ix = rng.integers(k_h + 20, 512 - k_h - 20)
                    iy = rng.integers(k_h + 20, 512 - k_h - 20)
                else: # CROWDED
                    ix = rng.integers(k_h + 20, 512 - k_h - 20)
                    iy = rng.integers(k_h + 20, 512 - k_h - 20)
                    # Add an un-subtracted companion star at 3 pixels separation
                    comp_flux = 5.0 * np.sqrt(diff_var[iy, ix])
                    img1[iy-2:iy+3, ix-2:ix+3] += comp_flux * 0.2
                    img2[iy-2:iy+3, ix-2:ix+3] += comp_flux * 0.2
                
                # Local noise variance for matched-filter calculation
                v_patch = diff_var[iy - k_h : iy - k_h + kernel_native.shape[0], ix - k_h : ix - k_h + kernel_native.shape[1]]
                if v_patch.shape != kernel_native.shape or np.any(v_patch <= 0):
                    v_local = float(np.median(diff_var))
                    inv_v_sum = np.sum(kernel_native**2) / v_local
                else:
                    inv_v_sum = np.sum((kernel_native**2) / v_patch)
                    
                mf_denominator = np.sqrt(inv_v_sum)
                F_inj = snr_target / mf_denominator
                
                v_center = diff_var[iy, ix]
                snr_peak = (F_inj * k_max) / np.sqrt(v_center)
                peak_snrs.append(snr_peak)
                
                # Inject native PSF into img2
                sign = +1.0 if polarity == "POSITIVE" else -1.0
                stamp = sign * F_inj * kernel_native
                img2[iy - k_h : iy - k_h + kernel_native.shape[0], ix - k_h : ix - k_h + kernel_native.shape[1]] += stamp
                
                # Run production difference engine and candidate extractor
                diff_res = compute_difference_and_significance(img1, var1, img2, var2, subtract_residual_background=False)
                c_res = extract_change_candidates(
                    significance_map=diff_res["significance_map"],
                    difference_image=diff_res["difference_image"],
                    significance_threshold=3.5,
                    min_area_pixels=3,
                    psf_kernel=kernel_native,
                    variance_map=diff_var,
                )
                
                # Match candidate within 3.0 pixels with correct polarity
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
                    
                    # PSF flux
                    if matched_cand.get("psf_flux_mjy_sr") is not None:
                        f_psf = abs(matched_cand["psf_flux_mjy_sr"])
                        psf_flux_biases.append((f_psf - F_inj) / F_inj)
                    
                    # Isophotal flux
                    f_iso = abs(matched_cand.get("isophotal_flux_mjy_sr", matched_cand["integrated_flux_mjy_sr"]))
                    iso_flux_biases.append((f_iso - F_inj) / F_inj)
                
                # False detections: candidates > 10 pixels away from injection
                false_cands = [c for c in c_res["candidates"] if np.hypot(c["pixel_x"] - ix, c["pixel_y"] - iy) > 10.0]
                false_detections_count += len(false_cands)
                
            p_comp, ci_low, ci_high = wilson_score_interval(recovered_count, n_trials)
            mean_psf_bias = float(np.mean(psf_flux_biases)) if psf_flux_biases else 0.0
            median_psf_bias = float(np.median(psf_flux_biases)) if psf_flux_biases else 0.0
            std_psf_flux = float(np.std(psf_flux_biases)) if psf_flux_biases else 0.0
            mean_iso_bias = float(np.mean(iso_flux_biases)) if iso_flux_biases else 0.0
            mean_pos_err = float(np.mean(pos_errors)) if pos_errors else 0.0
            mean_snr_peak = float(np.mean(peak_snrs))
            
            rec = {
                "case": case,
                "polarity": polarity,
                "snr_mf": snr_target,
                "snr_peak": round(mean_snr_peak, 2),
                "trials": n_trials,
                "recovered": recovered_count,
                "completeness": round(p_comp, 4),
                "ci_low": round(ci_low, 4),
                "ci_high": round(ci_high, 4),
                "psf_flux_bias_mean": round(mean_psf_bias, 4),
                "psf_flux_bias_median": round(median_psf_bias, 4),
                "psf_flux_scatter": round(std_psf_flux, 4),
                "isophotal_flux_bias_mean": round(mean_iso_bias, 4),
                "pos_err_px": round(mean_pos_err, 3),
                "false_cands_total": false_detections_count,
                "false_rate_per_trial": round(false_detections_count / n_trials, 4),
            }
            results.append(rec)
            print(f"[{case:8s}] {polarity:8s} | SNR_MF={snr_target:4.1f} (Peak={mean_snr_peak:4.1f}) | Comp={p_comp*100:5.1f}% [{ci_low*100:4.1f}%, {ci_high*100:4.1f}%] | PSF-Bias={mean_psf_bias*100:+5.2f}% (med {median_psf_bias*100:+5.2f}%, sct {std_psf_flux*100:4.1f}%) | Iso-Bias={mean_iso_bias*100:+5.1f}% | PosErr={mean_pos_err:.2f}px | False={false_detections_count}")

with open('scripts/m5_injection_results_corrected.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nSaved corrected results to scripts/m5_injection_results_corrected.json")
