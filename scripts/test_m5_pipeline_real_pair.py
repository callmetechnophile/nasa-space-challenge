import os
import sys

sys.path.insert(0, os.path.abspath("backend"))
from app.services.temporal_service import TemporalService

f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
f2 = "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"

service = TemporalService()
print("Executing Temporal Difference Pipeline...")
result = service.run_difference_pipeline(
    fits_path_1=f1,
    fits_path_2=f2,
    significance_threshold=3.5,
    spectral_tolerance=0.02,
    grid_size=512,
    subtract_background=True,
)

print("\n=== Temporal Pipeline Result Summary ===")
print("Epoch 1:", result["epoch_1"]["file"], "| MJD:", result["epoch_1"]["mjd_obs"], "| Band:", result["epoch_1"]["band"])
print("Epoch 2:", result["epoch_2"]["file"], "| MJD:", result["epoch_2"]["mjd_obs"], "| Band:", result["epoch_2"]["band"])
print(f"Temporal Baseline: {result['temporal_baseline']['delta_days']:.4f} days ({result['temporal_baseline']['delta_hours']:.2f} hours)")
print(f"Registration Displacement: dx={result['registration']['displacement']['dx_pixels']:.3f} pix, dy={result['registration']['displacement']['dy_pixels']:.3f} pix, sep={result['registration']['displacement']['angular_separation_arcsec']:.2f} arcsec")
print(f"Spectral Compatibility Fraction: {result['spectral_compatibility']['compatibility_fraction']*100:.2f}%, mean relative diff: {result['spectral_compatibility']['mean_rel_diff']*100:.4f}%")
print(f"PSF Target FWHM: {result['psf_matching']['target_fwhm']:.3f} pixels, convolved epoch: {result['psf_matching']['convolved_epoch']}")
print("Difference Metrics:")
for k, v in result["difference_metrics"].items():
    print(f"  {k}: {v}")
print(f"\nCandidates Found: {result['candidate_count']}")
for c in result["candidates"][:5]:
    print(f"  {c['candidate_id']}: ({c['ra_deg']}, {c['dec_deg']}) | Polarity: {c['polarity']} | Peak SNR: {c['significance_peak']} | Status: {c['scientific_status']}")
print("Scientific Disclaimer:", result["scientific_disclaimer"])
