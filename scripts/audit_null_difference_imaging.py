import os
import sys
import numpy as np
from astropy.io import fits
from scipy.stats import chi2

sys.path.insert(0, 'backend')
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates

def run_null_experiment(threshold_sigma, n_frames=50, frame_size=(256, 256), seed=42):
    rng = np.random.default_rng(seed)
    
    # SPHEREx pixel scale
    pix_scale_arcsec = 6.2
    omega_pix_deg2 = (pix_scale_arcsec / 3600.0) ** 2
    
    total_valid_pixels = 0
    total_detected_candidates = 0
    min_area_pixels = 3
    
    # Typical SPHEREx background noise sigma in MJy/sr
    noise_sigma = 0.02
    noise_var = noise_sigma ** 2
    
    for i in range(n_frames):
        # Generate two independent realization epochs of null sky (background noise only)
        img1 = rng.normal(0.0, noise_sigma, frame_size).astype(np.float32)
        var1 = np.full(frame_size, noise_var, dtype=np.float32)
        img2 = rng.normal(0.0, noise_sigma, frame_size).astype(np.float32)
        var2 = np.full(frame_size, noise_var, dtype=np.float32)
        
        # Run production difference engine
        diff_res = compute_difference_and_significance(
            img1, var1, img2, var2,
            subtract_residual_background=False
        )
        
        # Run production candidate extractor
        c_res = extract_change_candidates(
            significance_map=diff_res["significance_map"],
            difference_image=diff_res["difference_image"],
            significance_threshold=threshold_sigma,
            min_area_pixels=min_area_pixels,
        )
        
        valid_pixels = int(np.sum(np.isfinite(diff_res["significance_map"])))
        total_valid_pixels += valid_pixels
        total_detected_candidates += c_res["candidate_count"]
        
    total_solid_angle_deg2 = total_valid_pixels * omega_pix_deg2
    
    # Observed candidate density
    obs_density_deg2 = total_detected_candidates / total_solid_angle_deg2
    
    # 1-sided 95% Poisson upper confidence bound on counts:
    # lambda_95 = 0.5 * chi2.ppf(0.95, 2 * (k + 1))
    k = total_detected_candidates
    lambda_95 = 0.5 * chi2.ppf(0.95, 2 * (k + 1))
    density_95_upper_deg2 = lambda_95 / total_solid_angle_deg2
    
    # Full SPHEREx 2040x2040 frame solid angle
    full_frame_pix = 2040 * 2040
    omega_full_frame_deg2 = full_frame_pix * omega_pix_deg2
    candidates_per_full_frame_95 = density_95_upper_deg2 * omega_full_frame_deg2
    
    return {
        "threshold_sigma": threshold_sigma,
        "n_frames": n_frames,
        "frame_shape": frame_size,
        "total_valid_pixels": total_valid_pixels,
        "total_solid_angle_deg2": total_solid_angle_deg2,
        "min_area_pixels": min_area_pixels,
        "detected_candidates": total_detected_candidates,
        "observed_density_deg2": obs_density_deg2,
        "poisson_95_upper_bound_count": lambda_95,
        "poisson_95_upper_bound_density_deg2": density_95_upper_deg2,
        "full_frame_solid_angle_deg2": omega_full_frame_deg2,
        "poisson_95_upper_bound_per_full_frame": candidates_per_full_frame_95,
    }

print("=== RUNNING SEPARATE 4.0-SIGMA AND 5.0-SIGMA NULL EXPERIMENTS ===")
res_40 = run_null_experiment(threshold_sigma=4.0, n_frames=50, seed=12345)
res_50 = run_null_experiment(threshold_sigma=5.0, n_frames=50, seed=54321)

for r in [res_40, res_50]:
    print(f"\n--- Null Experiment: {r['threshold_sigma']:.1f} Sigma Threshold ---")
    print(f"  Number of independent frames: {r['n_frames']}")
    print(f"  Valid pixels evaluated: {r['total_valid_pixels']:,}")
    print(f"  Total solid angle surveyed: {r['total_solid_angle_deg2']:.5f} deg^2")
    print(f"  Detection threshold: {r['threshold_sigma']:.1f} sigma")
    print(f"  Minimum candidate area: {r['min_area_pixels']} connected pixels")
    print(f"  Number of detected candidates: {r['detected_candidates']}")
    print(f"  Observed candidate density: {r['observed_density_deg2']:.5f} deg^-2")
    print(f"  1-sided 95% Poisson upper bound count: {r['poisson_95_upper_bound_count']:.5f}")
    print(f"  1-sided 95% Poisson upper bound density: {r['poisson_95_upper_bound_density_deg2']:.5f} deg^-2")
    print(f"  Full 2040x2040 frame solid angle: {r['full_frame_solid_angle_deg2']:.5f} deg^2")
    print(f"  95% Upper bound candidates per full frame: {r['poisson_95_upper_bound_per_full_frame']:.5f}")
