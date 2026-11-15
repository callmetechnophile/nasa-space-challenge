import os
import sys
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u

sys.path.insert(0, 'backend')
from app.astronomy.spherex_spectral_wcs import (
    load_dual_wcs_from_hdulist,
    compute_spectral_properties_at_sky_coord,
)

pair_files = [
    'data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits',
    'data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits'
]

# Common celestial coordinate: center of overlap
test_ra = 46.8441306695
test_dec = 1.8317631143
c_test = SkyCoord(ra=test_ra * u.deg, dec=test_dec * u.deg, frame="icrs")

print("=== REQUIREMENT 5: FULL-PRECISION SPECTRAL WCS COMPARISON ===")
print(f"Target Celestial Coordinate: RA = {test_ra:.10f} deg, Dec = {test_dec:.10f} deg")

records = []

for idx, fp in enumerate(pair_files):
    fname = os.path.basename(fp)
    with fits.open(fp) as hdul:
        wcs_spatial, wcs_spectral = load_dual_wcs_from_hdulist(hdul)
        props = compute_spectral_properties_at_sky_coord(hdul, sky_coord=c_test)
        
        # Primary & extension headers
        p_hdr = hdul[0].header
        im_hdr = hdul['IMAGE'].header
        
        rec = {
            "epoch": f"Epoch {idx + 1}",
            "filename": fname,
            "detector": props['detector'],
            "pipeline_version": props['pipeline_version'],
            "cal_version": p_hdr.get('CAL_VER', im_hdr.get('CAL_VER', 'cal-v27')),
            "date_obs": props['date_obs'],
            "provenance": props['wcs_provenance'],
            "pixel_x": props['pixel_x'],
            "pixel_y": props['pixel_y'],
            "wavelength_um": props['wavelength_um'],
            "bandwidth_um": props['bandwidth_um'],
            "spatial_wcs_type": props['spatial_wcs_type'],
            "spatial_has_sip": props['spatial_has_sip'],
            "spectral_wcs_type": props['spectral_wcs_type'],
            "spectral_has_sip": props['spectral_has_sip'],
        }
        records.append(rec)

for r in records:
    print(f"\n--- {r['epoch']}: {r['filename']} ---")
    print(f"  Detector: {r['detector']} | Pipeline Version: {r['pipeline_version']} | Calibration: {r['cal_version']}")
    print(f"  Observation Timestamp (DATE-OBS): {r['date_obs']}")
    print(f"  Spectral Provenance: {r['provenance']}")
    print(f"  Spatial WCS: {r['spatial_wcs_type']} (SIP={r['spatial_has_sip']})")
    print(f"  Spectral WCS: {r['spectral_wcs_type']} (SIP={r['spectral_has_sip']})")
    print(f"  Unrounded Pixel Coordinates: X = {r['pixel_x']:.16f}, Y = {r['pixel_y']:.16f}")
    print(f"  Unrounded Wavelength:       lambda = {r['wavelength_um']:.16f} um")
    print(f"  Unrounded Bandwidth:        dlambda = {r['bandwidth_um']:.16f} um")

# Full precision relative difference
lam1 = records[0]['wavelength_um']
lam2 = records[1]['wavelength_um']
dlam1 = records[0]['bandwidth_um']
dlam2 = records[1]['bandwidth_um']

delta_lambda = abs(lam1 - lam2)
mean_lambda = (lam1 + lam2) / 2.0
rel_mismatch_pct = (delta_lambda / mean_lambda) * 100.0

delta_dlambda = abs(dlam1 - dlam2)
mean_dlambda = (dlam1 + dlam2) / 2.0
rel_dlam_mismatch_pct = (delta_dlambda / mean_dlambda) * 100.0

pix_dx = abs(records[0]['pixel_x'] - records[1]['pixel_x'])
pix_dy = abs(records[0]['pixel_y'] - records[1]['pixel_y'])
pix_dist = np.hypot(pix_dx, pix_dy)

print("\n=== FULL-PRECISION METRICS ===")
print(f"  Spatial Pixel Shift: delta_X = {pix_dx:.16f} px, delta_Y = {pix_dy:.16f} px (total = {pix_dist:.16f} px)")
print(f"  Absolute Wavelength Difference: |lambda1 - lambda2| = {delta_lambda:.16e} um")
print(f"  Relative Wavelength Mismatch:   {rel_mismatch_pct:.16f} %")
print(f"  Absolute Bandwidth Difference:  |dlam1 - dlam2| = {delta_dlambda:.16e} um")
print(f"  Relative Bandwidth Mismatch:    {rel_dlam_mismatch_pct:.16f} %")
