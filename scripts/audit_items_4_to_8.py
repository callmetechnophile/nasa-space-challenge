import os
import sys
import glob
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u

sys.path.insert(0, 'backend')

from app.astronomy.spherex_psf import (
    CALIB_DIR,
    select_spatially_varying_epsf,
    determine_parent_detector_pixel,
    load_psf_or_epsf_model,
)
from app.astronomy.spherex_spectral_wcs import (
    load_dual_wcs_from_hdulist,
    extract_spectral_properties,
    compute_spectral_properties_at_sky_coord,
)
from app.astronomy.gaia_astrometry import (
    propagate_gaia_source,
    cross_match_spherex_with_gaia,
    perform_gaia_astrometric_validation,
    BENCHMARK_GAIA_DR3_STARS,
)

print("==================================================")
print("ITEM 4: GAIA ASTROMETRIC VALIDATION AUDIT")
print("==================================================")
print(f"Total benchmark Gaia DR3 stars defined: {len(BENCHMARK_GAIA_DR3_STARS)}")
for i, s in enumerate(BENCHMARK_GAIA_DR3_STARS):
    p_ra, p_dec, disp = propagate_gaia_source(s, target_obstime_str="2025-10-31T19:02:05.151")
    print(f"  Star {i+1} [{s['source_id']}]: G={s.get('phot_g_mean_mag')} | Ref=({s['ra_deg']:.6f}, {s['dec_deg']:.6f}) | Prop=({p_ra:.6f}, {p_dec:.6f}) | PM disp={disp:.3f}\"")

# Perform cross-match test with small sample (3 stars) vs full sample (6 stars)
prop_3 = [propagate_gaia_source(s, target_epoch_year=2025.8) for s in BENCHMARK_GAIA_DR3_STARS[:3]]
measured_3 = [{"ra_deg": s["propagated_ra_deg"] + 0.05/3600.0, "dec_deg": s["propagated_dec_deg"]} for s in prop_3]
res_3 = cross_match_spherex_with_gaia(measured_3, prop_3)
print("\n3-star synthetic cross-match results:")
print(f"  Matched: {res_3['matched_count']}, RMS: {res_3['residual_rms_arcsec']:.4f}\", NMAD: {res_3['robust_scatter_nmad_arcsec']:.4f}\"")
print("  Note on NMAD with N=3 identical offset: MAD = median(|0.05 - 0.05|) = 0.0000\"!")

prop_6 = [propagate_gaia_source(s, target_epoch_year=2025.8) for s in BENCHMARK_GAIA_DR3_STARS]
# With realistic dispersion (sigma = 0.15 arcsec)
np.random.seed(42)
measured_6 = []
for s in prop_6:
    d_ra = np.random.normal(0, 0.15) / 3600.0 / np.cos(np.radians(s["propagated_dec_deg"]))
    d_dec = np.random.normal(0, 0.15) / 3600.0
    measured_6.append({"ra_deg": s["propagated_ra_deg"] + d_ra, "dec_deg": s["propagated_dec_deg"] + d_dec})
res_6 = cross_match_spherex_with_gaia(measured_6, prop_6)
print("\n6-star sample with realistic 0.15\" scatter:")
print(f"  Matched: {res_6['matched_count']}, RMS: {res_6['residual_rms_arcsec']:.4f}\", NMAD: {res_6['robust_scatter_nmad_arcsec']:.4f}\"")


print("\n==================================================")
print("ITEM 6: NULL-FIELD FALSE-POSITIVE AUDIT")
print("==================================================")
from scipy.stats import chi2
trials = 50
pix_per_trial = 256 * 256
total_pix = trials * pix_per_trial
pix_scale_asec = 6.2
omega_pix_deg2 = (pix_scale_asec / 3600.0)**2
omega_tot_deg2 = total_pix * omega_pix_deg2
full_frame_pix = 2040 * 2040
omega_full_deg2 = full_frame_pix * omega_pix_deg2

# 0 false positives observed at 4.0 sigma
k_obs = 0
# Poisson 1-sided 95% upper limit: lambda_95 = 0.5 * chi2.ppf(0.95, 2*(k+1))
lambda_95 = 0.5 * chi2.ppf(0.95, 2 * (k_obs + 1))
fp_density_deg2 = lambda_95 / omega_tot_deg2
fp_per_frame_95 = fp_density_deg2 * omega_full_deg2

print(f"Trials: {trials} cutouts of 256x256 ({total_pix:,} total pixels)")
print(f"Total solid angle surveyed: {omega_tot_deg2:.5f} deg^2")
print(f"Observed false positives at 4.0 sigma: {k_obs}")
print(f"Poisson 1-sided 95% upper confidence bound on counts: {lambda_95:.4f}")
print(f"False-positive density 95% upper bound: {fp_density_deg2:.4f} candidates/deg^2")
print(f"Full SPHEREx frame solid angle (2040x2040): {omega_full_deg2:.4f} deg^2")
print(f"False-positive rate 95% upper bound per full frame: {fp_per_frame_95:.4f} candidates/frame")


print("\n==================================================")
print("ITEM 7: ePSF ZONE SELECTION VALIDATION (ALL DETECTORS)")
print("==================================================")
cal_files = sorted(glob.glob(os.path.join(CALIB_DIR, "epsf_D*.fits")))
print(f"Found {len(cal_files)} calibration files in {CALIB_DIR}")

test_pixels = [(50.0, 50.0), (512.0, 512.0), (1024.0, 1024.0), (1500.0, 1500.0), (2000.0, 2000.0)]

for cf in cal_files:
    fname = os.path.basename(cf)
    with fits.open(cf) as hdul:
        tab = Table.read(hdul["EPSF"])
        print(f"\nFile: {fname} (HDU 'EPSF' rows: {len(tab)})")
        # Check coordinates and bounds
        x_min, x_max = np.min(tab["XCENTER"]), np.max(tab["XCENTER"])
        y_min, y_max = np.min(tab["YCENTER"]), np.max(tab["YCENTER"])
        print(f"  Zone centers X range: [{x_min:.1f}, {x_max:.1f}], Y range: [{y_min:.1f}, {y_max:.1f}]")
        
        for px, py in test_pixels:
            zinfo = select_spatially_varying_epsf(tab, parent_x=px, parent_y=py)
            kern = zinfo["kernel"]
            ksum = float(np.sum(kern))
            print(f"  Parent ({px:6.1f}, {py:6.1f}) -> Zone ({zinfo['bin_x']:2d}, {zinfo['bin_y']:2d}) at ({zinfo['zone_center_x']:6.1f}, {zinfo['zone_center_y']:6.1f}) | dist={zinfo['zone_distance_pix']:5.1f} px | shape={kern.shape} | sum={ksum:.6f}")


print("\n==================================================")
print("ITEM 8: SPECTRAL WCS END-TO-END VALIDATION")
print("==================================================")
pair_files = [
    'data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits',
    'data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits'
]

# Common sky coordinate for comparison: center of the field
with fits.open(pair_files[0]) as hdul1, fits.open(pair_files[1]) as hdul2:
    wcs1_spatial, wcs1_spectral = load_dual_wcs_from_hdulist(hdul1)
    wcs2_spatial, wcs2_spectral = load_dual_wcs_from_hdulist(hdul2)
    
    print(f"Epoch 1 (D3): Spatial SIP={wcs1_spatial.sip is not None}, Spectral SIP={wcs1_spectral.sip is not None}")
    print(f"Epoch 2 (D1): Spatial SIP={wcs2_spatial.sip is not None}, Spectral SIP={wcs2_spectral.sip is not None}")
    
    test_ra = 46.844
    test_dec = 1.832
    print(f"\nEvaluating at common celestial coordinate: RA={test_ra:.3f} deg, Dec={test_dec:.3f} deg")
    
    c_test = SkyCoord(ra=test_ra * u.deg, dec=test_dec * u.deg, frame="icrs")
    prop1 = compute_spectral_properties_at_sky_coord(hdul1, sky_coord=c_test)
    prop2 = compute_spectral_properties_at_sky_coord(hdul2, sky_coord=c_test)
    print(f"Epoch 1 (D3): lambda={prop1['wavelength_um']:.4f} um, detector={prop1['detector']}, dlambda={prop1['bandwidth_um']:.4f} um, pixel=({prop1['pixel_x']:.2f}, {prop1['pixel_y']:.2f})")
    print(f"Epoch 2 (D1): lambda={prop2['wavelength_um']:.4f} um, detector={prop2['detector']}, dlambda={prop2['bandwidth_um']:.4f} um, pixel=({prop2['pixel_x']:.2f}, {prop2['pixel_y']:.2f})")
    delta_lam = abs(prop1['wavelength_um'] - prop2['wavelength_um'])
    rel_diff = delta_lam / ((prop1['wavelength_um'] + prop2['wavelength_um']) / 2.0) * 100.0
    print(f"Delta lambda: {delta_lam:.4f} um ({rel_diff:.2f}% spectral difference across detectors)")
