import sys
sys.path.insert(0, "backend")
from app.services.temporal_service import TemporalService

service = TemporalService()
f1 = "data/spherex/fixtures_m5/m5_synthetic_epoch1.fits"
f2 = "data/spherex/fixtures_m5/m5_synthetic_epoch2.fits"

res = service.run_difference_pipeline(f1, f2, significance_threshold=3.5, grid_size=512)
print("Comparison Results:")
print("  Epoch 1:", res["epoch_1"]["file"], "MJD:", res["epoch_1"]["mjd_obs"])
print("  Epoch 2:", res["epoch_2"]["file"], "MJD:", res["epoch_2"]["mjd_obs"])
print("  Temporal Baseline:", res["temporal_baseline"]["delta_days"], "days")
print("  Registration displacement:", res["registration"]["displacement"])
print("  Spectral Compatibility:", res["spectral_compatibility"])
print("  Difference Metrics:", res["difference_metrics"])
print("  Candidate count:", res["candidate_count"])
for c in res["candidates"]:
    print(f"   Candidate {c['candidate_id']}: {c['polarity']} peak_SNR={c['significance_peak']:.2f} centroid=({c['pixel_x']}, {c['pixel_y']}) RA={c['ra_deg']}, Dec={c['dec_deg']}")
