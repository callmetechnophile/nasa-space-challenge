import os
import sys
import json
import numpy as np
from scipy.stats import chi2

sys.path.insert(0, 'backend')
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates

def run_null_experiment(threshold_sigma, n_frames=50, frame_size=(256, 256), seed=42):
    rng = np.random.default_rng(seed)
    
    pix_scale_arcsec = 6.2
    omega_pix_deg2 = (pix_scale_arcsec / 3600.0) ** 2
    
    total_valid_pixels = 0
    total_detected_candidates = 0
    min_area_pixels = 3
    
    noise_sigma = 0.02
    noise_var = noise_sigma ** 2
    
    for i in range(n_frames):
        img1 = rng.normal(0.0, noise_sigma, frame_size).astype(np.float32)
        var1 = np.full(frame_size, noise_var, dtype=np.float32)
        img2 = rng.normal(0.0, noise_sigma, frame_size).astype(np.float32)
        var2 = np.full(frame_size, noise_var, dtype=np.float32)
        
        diff_res = compute_difference_and_significance(
            img1, var1, img2, var2,
            subtract_residual_background=False
        )
        
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
    obs_density_deg2 = total_detected_candidates / total_solid_angle_deg2
    
    k = total_detected_candidates
    lambda_95 = float(0.5 * chi2.ppf(0.95, 2 * (k + 1)))
    density_95_upper_deg2 = lambda_95 / total_solid_angle_deg2
    
    full_frame_pix = 2040 * 2040
    omega_full_frame_deg2 = full_frame_pix * omega_pix_deg2
    candidates_per_full_frame_95 = density_95_upper_deg2 * omega_full_frame_deg2
    
    return {
        "experiment_type": "SIMULATION_BASED_NULL_TEST",
        "noise_model": "Independent zero-mean Gaussian (white)",
        "generator": "numpy.random.default_rng",
        "random_seed": seed,
        "spatial_covariance_modeled": False,
        "threshold_sigma": float(threshold_sigma),
        "n_frames": int(n_frames),
        "frame_shape": list(frame_size),
        "total_valid_pixels": int(total_valid_pixels),
        "total_solid_angle_deg2": float(total_solid_angle_deg2),
        "min_area_pixels": int(min_area_pixels),
        "detected_candidates": int(total_detected_candidates),
        "observed_density_deg2": float(obs_density_deg2),
        "poisson_95_upper_bound_count": float(lambda_95),
        "poisson_95_upper_bound_density_deg2": float(density_95_upper_deg2),
        "full_frame_solid_angle_deg2": float(omega_full_frame_deg2),
        "poisson_95_upper_bound_per_full_frame": float(candidates_per_full_frame_95),
        "astrophysical_false_positives_constrained": False,
        "caveat": "White Gaussian noise underestimates real false-positive rate because real data contain spatial covariance from pixel resampling, flat-field residuals, and 1/f detector noise."
    }

print("=== RUNNING SEPARATE 4.0-SIGMA AND 5.0-SIGMA NULL EXPERIMENTS ===")
res_40 = run_null_experiment(threshold_sigma=4.0, n_frames=50, seed=12345)
res_50 = run_null_experiment(threshold_sigma=5.0, n_frames=50, seed=54321)

out = {
    "null_4_0_sigma": res_40,
    "null_5_0_sigma": res_50
}

with open("scripts/null_difference_audit.json", "w") as f:
    json.dump(out, f, indent=2)

for key, r in out.items():
    print(f"\n--- {r['experiment_type']}: {r['threshold_sigma']:.1f} Sigma Threshold ---")
    print(f"  Frames: {r['n_frames']} ({r['frame_shape'][0]}x{r['frame_shape'][1]}) | Seed: {r['random_seed']}")
    print(f"  Valid pixels: {r['total_valid_pixels']:,} | Solid angle: {r['total_solid_angle_deg2']:.5f} deg^2")
    print(f"  Detected candidates (min area {r['min_area_pixels']} px): {r['detected_candidates']}")
    print(f"  Poisson 95% upper bound count: {r['poisson_95_upper_bound_count']:.5f}")
    print(f"  Poisson 95% upper bound density: {r['poisson_95_upper_bound_density_deg2']:.5f} deg^-2")
    print(f"  Full frame (2040x2040, {r['full_frame_solid_angle_deg2']:.3f} deg^2) 95% UB: {r['poisson_95_upper_bound_per_full_frame']:.4f} candidates/frame")

print("\nResults written to scripts/null_difference_audit.json")
