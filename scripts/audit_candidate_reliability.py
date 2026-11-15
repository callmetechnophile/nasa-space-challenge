import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("backend"))
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates, DISCLAIMER_LABEL

print("=== AUDIT 4: CANDIDATE EXTRACTION RELIABILITY & INJECTION RECOVERY ===")

np.random.seed(42)
grid_size = 256
noise_sigma = 0.02  # MJy/sr (typical SPHEREx background noise level)
noise_var = noise_sigma ** 2

# Generate realistic baseline background
img1 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
img2 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
var1 = np.full((grid_size, grid_size), noise_var, dtype=np.float32)
var2 = np.full((grid_size, grid_size), noise_var, dtype=np.float32)

# Synthetic PSF (Gaussian FWHM = 2.0 pixels -> sigma = 2.0 / 2.35482)
psf_sigma = 2.0 / 2.35482
def make_stamp(flux, radius=5):
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    r2 = x**2 + y**2
    stamp = np.exp(-r2 / (2 * psf_sigma**2))
    stamp = stamp / np.sum(stamp) * flux
    return stamp

# Test 1: Completeness versus Injected SNR (Positive and Negative)
snr_levels = [2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 20.0]
flux_levels = [s * noise_sigma * np.sqrt(2.0) * (2 * np.pi * psf_sigma**2) for s in snr_levels]
polarities = ["POSITIVE", "NEGATIVE"]

print("\n--- Test 1A: Completeness & Recovery vs Injected SNR ---")
for pol in polarities:
    print(f"\nPolarity: {pol}")
    for snr, flux in zip(snr_levels, flux_levels):
        n_trials = 20
        recovered = 0
        pos_errors = []
        flux_errors = []

        for trial in range(n_trials):
            i1 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
            i2 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
            
            # Place source away from edge
            xi = np.random.randint(40, grid_size - 40)
            yi = np.random.randint(40, grid_size - 40)

            sign = +1.0 if pol == "POSITIVE" else -1.0
            stamp = make_stamp(flux * sign)
            rad = 5
            i2[yi-rad:yi+rad+1, xi-rad:xi+rad+1] += stamp

            d_res = compute_difference_and_significance(i1, var1, i2, var2, subtract_residual_background=False)
            c_res = extract_change_candidates(d_res["significance_map"], d_res["difference_image"], significance_threshold=3.5)

            # Match candidate within 3 pixels of true location
            matched = False
            for c in c_res["candidates"]:
                if c["polarity"] == pol:
                    dist = np.hypot(c["pixel_x"] - xi, c["pixel_y"] - yi)
                    if dist <= 3.0:
                        matched = True
                        pos_errors.append(dist)
                        rec_flux = c["integrated_flux_mjy_sr"]
                        flux_errors.append((abs(rec_flux) - flux) / flux)
                        break
            if matched:
                recovered += 1

        comp = (recovered / n_trials) * 100
        mean_pos_err = np.mean(pos_errors) if pos_errors else np.nan
        mean_flux_bias = np.mean(flux_errors) * 100 if flux_errors else np.nan
        print(f"  Injected SNR={snr:4.1f} sigma | Comp={comp:5.1f}% | PosErr={mean_pos_err:.2f} px | FluxBias={mean_flux_bias:+.1f}%")

# Test 2: False Positive Rate on Pure Noise
print("\n--- Test 2: False Positive Rate on Null Sky (Pure Noise) ---")
n_null_runs = 10
total_null_pixels = n_null_runs * (grid_size ** 2)
total_false_cands_35 = 0
total_false_cands_50 = 0

for _ in range(n_null_runs):
    i1 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
    i2 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
    d_res = compute_difference_and_significance(i1, var1, i2, var2, subtract_residual_background=False)
    c35 = extract_change_candidates(d_res["significance_map"], d_res["difference_image"], significance_threshold=3.5)
    c50 = extract_change_candidates(d_res["significance_map"], d_res["difference_image"], significance_threshold=5.0)
    total_false_cands_35 += c35["candidate_count"]
    total_false_cands_50 += c50["candidate_count"]

fpr_35 = total_false_cands_35 / (n_null_runs * (grid_size**2))
fpr_50 = total_false_cands_50 / (n_null_runs * (grid_size**2))
print(f"  Null Sky Trials: {n_null_runs} frames ({total_null_pixels:,} pixels)")
print(f"  False candidates at 3.5 sigma: {total_false_cands_35} ({total_false_cands_35/n_null_runs:.1f}/frame, rate={fpr_35:.3e}/px)")
print(f"  False candidates at 5.0 sigma: {total_false_cands_50} ({total_false_cands_50/n_null_runs:.1f}/frame, rate={fpr_50:.3e}/px)")

# Test 3: Edge Proximity Rejection & Warning Flag
print("\n--- Test 3: Edge Proximity Warning Flag ---")
i1 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
i2 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
# Inject source at edge (x=8, y=8)
i2[3:14, 3:14] += make_stamp(flux_levels[-1])
d_res = compute_difference_and_significance(i1, var1, i2, var2, subtract_residual_background=False)
c_res = extract_change_candidates(d_res["significance_map"], d_res["difference_image"], significance_threshold=3.5)
edge_cand = [c for c in c_res["candidates"] if "NEAR_IMAGE_BOUNDARY" in c["warnings"]]
print(f"  Edge source at (8, 8) detected: {len(edge_cand) > 0}")
if edge_cand:
    print(f"  Candidate Warning Flags: {edge_cand[0]['warnings']}")
    print(f"  Candidate Status Label: {edge_cand[0]['scientific_status']}")
    assert edge_cand[0]['scientific_status'] == DISCLAIMER_LABEL

# Test 4: Crowded Field (near bright star residual)
print("\n--- Test 4: Crowded Field / Bright Star Residual Residual Artifacts ---")
i1 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
i2 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
# Add bright star in Epoch 1 and Epoch 2 with 0.1 pixel astrometric shift (simulating pointing jitter)
ys, xs = np.ogrid[-15:16, -15:16]
star_stamp1 = np.exp(-(xs**2 + ys**2)/(2*psf_sigma**2)) * 50.0  # Bright star 50 MJy/sr
star_stamp2 = np.exp(-((xs - 0.1)**2 + ys**2)/(2*psf_sigma**2)) * 50.0
i1[128-15:128+16, 128-15:128+16] += star_stamp1
i2[128-15:128+16, 128-15:128+16] += star_stamp2

d_res = compute_difference_and_significance(i1, var1, i2, var2, subtract_residual_background=False)
c_res = extract_change_candidates(d_res["significance_map"], d_res["difference_image"], significance_threshold=3.5)
print(f"  Bright star dipole residual: candidates detected near star = {c_res['candidate_count']}")
for c in c_res["candidates"][:3]:
    dist_star = np.hypot(c["pixel_x"] - 128, c["pixel_y"] - 128)
    print(f"    Dipole Artifact: {c['candidate_id']} | Dist from star={dist_star:.1f} px | Polarity={c['polarity']} | SNR={c['significance_peak']:.1f} sigma")
