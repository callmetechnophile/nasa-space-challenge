"""Independent Audit Script for M5 Final Numerical Consistency Audit.
Audits all five areas:
1. Significance statistics across 4x4 blocks and benchmark regions
2. WCS and SIP verification (headers, analytical SIP, Astropy behavior)
3. EPSF sampling, binning, normalization, and 33x33 vs 7x7 resolution
4. Photometric recovery across SNR, polarity, positions, and backgrounds
5. False-positive confidence and Poisson upper bounds
"""

import sys
import os
import math
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.ndimage import label, center_of_mass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("backend"))

from app.astronomy.spherex_mef_reader import read_spherex_mef_product
from app.astronomy.image_registration import create_common_wcs, reproject_to_common_grid
from app.astronomy.quality_mask import create_quality_mask, FATAL_DEFECT_MASK, BIT_SOURCE
from app.astronomy.spectral_compatibility import LVFWavelengthModel, evaluate_spectral_compatibility
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates

f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
f2 = "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"

print("================================================================================")
print("INDEPENDENT AUDIT: M5 FINAL NUMERICAL CONSISTENCY AUDIT")
print("================================================================================")

# ------------------------------------------------------------------------------
# AUDIT 2 FIRST: WCS & SIP COEFFICIENTS INSPECTION
# ------------------------------------------------------------------------------
print("\n" + "="*80)
print("AUDIT 2: WCS AND SIP VERIFICATION")
print("="*80)

for label_name, fpath in [("Epoch 1", f1), ("Epoch 2", f2)]:
    print(f"\n--- Checking Header & SIP for {label_name}: {os.path.basename(fpath)} ---")
    with fits.open(fpath) as hdul:
        hdr = hdul["IMAGE"].header
        crpix1 = float(hdr["CRPIX1"])
        crpix2 = float(hdr["CRPIX2"])
        crval1 = float(hdr["CRVAL1"])
        crval2 = float(hdr["CRVAL2"])
        ctype1 = hdr.get("CTYPE1")
        ctype2 = hdr.get("CTYPE2")
        a_order = int(hdr.get("A_ORDER", 0))
        b_order = int(hdr.get("B_ORDER", 0))
        
        print(f"CRPIX: ({crpix1}, {crpix2}) | CRVAL: ({crval1:.8f}, {crval2:.8f})")
        print(f"CTYPE: {ctype1}, {ctype2} | A_ORDER: {a_order}, B_ORDER: {b_order}")
        
        # Check all SIP coefficients present in header
        sip_a = {}
        sip_b = {}
        sip_ap = {}
        sip_bp = {}
        for k, v in hdr.items():
            if k.startswith("A_") and k[2:].replace("_", "").isdigit():
                parts = k.split("_")
                if len(parts) == 3:
                    sip_a[(int(parts[1]), int(parts[2]))] = float(v)
            elif k.startswith("B_") and k[2:].replace("_", "").isdigit():
                parts = k.split("_")
                if len(parts) == 3:
                    sip_b[(int(parts[1]), int(parts[2]))] = float(v)
            elif k.startswith("AP_") and k[3:].replace("_", "").isdigit():
                parts = k.split("_")
                if len(parts) == 3:
                    sip_ap[(int(parts[1]), int(parts[2]))] = float(v)
            elif k.startswith("BP_") and k[3:].replace("_", "").isdigit():
                parts = k.split("_")
                if len(parts) == 3:
                    sip_bp[(int(parts[1]), int(parts[2]))] = float(v)
        
        print(f"Found {len(sip_a)} A_p_q terms, {len(sip_b)} B_p_q terms")
        print(f"Found {len(sip_ap)} AP_p_q terms, {len(sip_bp)} BP_p_q terms")
        print(f"Zeroth order terms: A_0_0 = {sip_a.get((0,0), 0.0)}, B_0_0 = {sip_b.get((0,0), 0.0)}")
        print(f"First order terms: A_1_0 = {sip_a.get((1,0), 0.0)}, A_0_1 = {sip_a.get((0,1), 0.0)}")
        print(f"                  B_1_0 = {sip_b.get((1,0), 0.0)}, B_0_1 = {sip_b.get((0,1), 0.0)}")
        
        w = WCS(hdr)
        print(f"Astropy WCS has sip: {w.sip is not None}")
        if w.sip is not None:
            print(f"  w.sip.a shape: {w.sip.a.shape}")
            print(f"  w.sip.a[0,0] = {w.sip.a[0,0]}")
            print(f"  w.sip.b[0,0] = {w.sip.b[0,0]}")
            print(f"  w.sip.a[1,0] = {w.sip.a[1,0]}, w.sip.a[0,1] = {w.sip.a[0,1]}")
            
        # Test Astropy all_pix2world vs wcs_pix2world at reference pixel (origin=1)
        w_lin = w.wcs_pix2world([[crpix1, crpix2]], 1)[0]
        w_sip = w.all_pix2world([[crpix1, crpix2]], 1)[0]
        diff_lin = np.hypot((w_lin[0]-crval1)*np.cos(np.radians(crval2))*3600.0, (w_lin[1]-crval2)*3600.0)
        diff_sip = np.hypot((w_sip[0]-crval1)*np.cos(np.radians(crval2))*3600.0, (w_sip[1]-crval2)*3600.0)
        print(f"Linear WCS at CRPIX offset from CRVAL: {diff_lin:.6e} arcsec")
        print(f"Full SIP WCS at CRPIX offset from CRVAL: {diff_sip:.6f} arcsec")
        
        # Now let's calculate analytical SIP distortion at (u=0, v=0)
        # u = crpix1 - crpix1 = 0, v = crpix2 - crpix2 = 0
        # f(u, v) = sum A_p_q u^p v^q = A_0_0
        # g(u, v) = sum B_p_q u^p v^q = B_0_0
        # Then pixel coordinate after distortion is (x + f, y + g)
        # What does linear WCS evaluate at (crpix1 + A_0_0, crpix2 + B_0_0)?
        w_analytic = w.wcs_pix2world([[crpix1 + sip_a.get((0,0), 0.0), crpix2 + sip_b.get((0,0), 0.0)]], 1)[0]
        diff_analytic_sip = np.hypot((w_analytic[0]-w_sip[0])*np.cos(np.radians(crval2))*3600.0, (w_analytic[1]-w_sip[1])*3600.0)
        print(f"Difference between Astropy all_pix2world and analytical SIP at CRPIX: {diff_analytic_sip:.6e} arcsec")
        
        # Test CD matrix and pixel scale
        cd = w.wcs.cd if hasattr(w.wcs, "cd") else None
        print(f"CD matrix:\n{cd}")
        pix_scale = np.sqrt(np.abs(np.linalg.det(cd))) * 3600.0 if cd is not None else np.nan
        print(f"Linear Pixel scale from CD: {pix_scale:.4f} arcsec/pixel")

# ------------------------------------------------------------------------------
# AUDIT 3: EPSF SAMPLING AND NORMALIZATION
# ------------------------------------------------------------------------------
print("\n" + "="*80)
print("AUDIT 3: EPSF SAMPLING AND NORMALIZATION")
print("="*80)
with fits.open(f1) as hdul:
    epsf_hdu = hdul["EPSF"]
    epsf_hdr = epsf_hdu.header
    print("EPSF Header Keywords:")
    for k in ["TFIELDS", "NAXIS1", "NAXIS2", "EXTNAME", "BUNIT", "OVSMPX", "OVSMPY", "OVERSAMP", "PIXSCALE", "KEEPNAT"]:
        if k in epsf_hdr:
            print(f"  {k} = {epsf_hdr[k]}")
    
    epsf_data = epsf_hdu.data
    print(f"Table columns: {epsf_data.names}")
    center_row = epsf_data[220]
    epsf_subpix = center_row["EPSF"]
    print(f"Center bin row 220 array shape: {epsf_subpix.shape}")
    print(f"Center bin array dtype: {epsf_subpix.dtype}")
    print(f"Center bin min: {np.min(epsf_subpix):.6e}, max: {np.max(epsf_subpix):.6e}, sum: {np.sum(epsf_subpix):.6f}")
    
    # Check centroid of 33x33
    ny, nx = epsf_subpix.shape
    yc, xc = (ny - 1) / 2.0, (nx - 1) / 2.0
    y_idx, x_idx = np.indices((ny, nx))
    tot = np.sum(epsf_subpix)
    cx_sub = np.sum(x_idx * epsf_subpix) / tot
    cy_sub = np.sum(y_idx * epsf_subpix) / tot
    var_x = np.sum(((x_idx - cx_sub) ** 2) * epsf_subpix) / tot
    var_y = np.sum(((y_idx - cy_sub) ** 2) * epsf_subpix) / tot
    fwhm_x_sub = np.sqrt(max(var_x, 0.01)) * 2.35482
    fwhm_y_sub = np.sqrt(max(var_y, 0.01)) * 2.35482
    print(f"Subpixel centroid: ({cx_sub:.4f}, {cy_sub:.4f}) relative to center ({xc}, {yc}): dx={cx_sub-xc:.4f}, dy={cy_sub-yc:.4f}")
    print(f"Subpixel second-moment FWHM: X={fwhm_x_sub:.3f}, Y={fwhm_y_sub:.3f} sub-pixels")
    
    # Conversion to native pixels:
    # 33x33 with 5x oversampling.
    # If padded by 1 pixel on each side -> 35x35
    # Then block-summed 5x5 -> 7x7 native pixels.
    pad_epsf = np.pad(epsf_subpix, ((1, 1), (1, 1)), mode="constant", constant_values=0.0)
    native_7x7 = pad_epsf.reshape(7, 5, 7, 5).sum(axis=(1, 3))
    print(f"\nBlock-summed 7x7 native kernel:")
    print(f"  Shape: {native_7x7.shape}")
    print(f"  Sum before renormalization: {np.sum(native_7x7):.6f}")
    print(f"  Fraction of flux lost in 33x33 cutoff vs pad: {1.0 - np.sum(epsf_subpix):.6e}")
    print(f"  Peak pixel value: {np.max(native_7x7):.6f}")
    
    # 7x7 centroid & FWHM
    ny7, nx7 = native_7x7.shape
    yc7, xc7 = (ny7 - 1) / 2.0, (nx7 - 1) / 2.0
    y7_idx, x7_idx = np.indices((ny7, nx7))
    tot7 = np.sum(native_7x7)
    cx7 = np.sum(x7_idx * native_7x7) / tot7
    cy7 = np.sum(y7_idx * native_7x7) / tot7
    var_x7 = np.sum(((x7_idx - cx7) ** 2) * native_7x7) / tot7
    var_y7 = np.sum(((y7_idx - cy7) ** 2) * native_7x7) / tot7
    fwhm_x7 = np.sqrt(max(var_x7, 0.01)) * 2.35482
    fwhm_y7 = np.sqrt(max(var_y7, 0.01)) * 2.35482
    print(f"  Centroid relative to array center ({xc7}, {yc7}): dx={cx7-xc7:.4f}, dy={cy7-yc7:.4f} native px")
    print(f"  Second-moment FWHM: X={fwhm_x7:.3f}, Y={fwhm_y7:.3f} native pixels")
    print(f"  Ratio of subpixel FWHM / 5.0: X={fwhm_x_sub/5.0:.3f}, Y={fwhm_y_sub/5.0:.3f}")

# ------------------------------------------------------------------------------
# AUDIT 1: SIGNIFICANCE STATISTICS ACROSS 4x4 BLOCKS AND BENCHMARKS
# ------------------------------------------------------------------------------
print("\n" + "="*80)
print("AUDIT 1: SIGNIFICANCE STATISTICS ACROSS 4x4 BLOCKS AND BENCHMARK REGIONS")
print("="*80)

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

diff = diff_res["difference_image"]
diff_sig = diff_res["diff_sigma"]
sig = diff_res["significance_map"]
valid = diff_res["valid_mask"]

is_source_1 = (flags1_rep.astype(np.int64) & BIT_SOURCE) != 0
is_source_2 = (flags2_rep.astype(np.int64) & BIT_SOURCE) != 0
source_mask = is_source_1 | is_source_2
source_free_mask = valid & (~source_mask)

def robust_mad(data):
    med = np.median(data)
    return float(1.4826 * np.median(np.abs(data - med)))

def compute_detailed_stats(d_vals, sig_vals, sigma_vals, block_valid, block_sig):
    n_pix = len(d_vals)
    mean_d = float(np.mean(d_vals))
    std_d = float(np.std(d_vals))
    med_d = float(np.median(d_vals))
    mad_d = robust_mad(d_vals)
    
    mean_sigma = float(np.mean(sigma_vals))
    std_sigma = float(np.std(sigma_vals))
    
    mean_s = float(np.mean(sig_vals))
    std_s = float(np.std(sig_vals))
    med_s = float(np.median(sig_vals))
    mad_s = robust_mad(sig_vals)
    
    p1, p5, p16, p50, p84, p95, p99 = [float(x) for x in np.percentile(sig_vals, [1, 5, 16, 50, 84, 95, 99])]
    
    # Calculate ratio of std(d) / mean(sigma)
    ratio_std = std_d / mean_sigma if mean_sigma > 0 else np.nan
    ratio_mad = mad_d / mean_sigma if mean_sigma > 0 else np.nan
    
    # Autocorrelation of significance map
    p = block_sig - np.nanmean(block_sig)
    num_x = np.nanmean(p[:, :-1] * p[:, 1:])
    denom_x = np.nanvar(block_sig)
    rx = float(num_x / denom_x) if denom_x > 0 else np.nan
    
    num_y = np.nanmean(p[:-1, :] * p[1:, :])
    denom_y = np.nanvar(block_sig)
    ry = float(num_y / denom_y) if denom_y > 0 else np.nan
    
    return {
        "n_pix": n_pix,
        "mean_d": mean_d, "std_d": std_d, "med_d": med_d, "mad_d": mad_d,
        "mean_sigma": mean_sigma, "std_sigma": std_sigma,
        "mean_s": mean_s, "std_s": std_s, "med_s": med_s, "mad_s": mad_s,
        "p1": p1, "p5": p5, "p16": p16, "p50": p50, "p84": p84, "p95": p95, "p99": p99,
        "ratio_std": ratio_std, "ratio_mad": ratio_mad,
        "rx": rx, "ry": ry
    }

print("\n--- DETAILED 4x4 BLOCK STATISTICS ---")
print(f"{'Block':<7} | {'Valid N':<7} | {'Mean D':<8} | {'Std D':<8} | {'MAD D':<8} | {'Pred Sig':<8} | {'Mean S':<8} | {'Std S':<8} | {'MAD S':<8} | {'P16':<7} | {'P84':<7} | {'StdD/Pred':<9} | {'MAD D/Pred':<10} | {'rho_x':<6} | {'rho_y':<6}")
print("-" * 155)

blocks_16 = []
for gy in range(4):
    for gx in range(4):
        y0, y1 = gy * 128, (gy + 1) * 128
        x0, x1 = gx * 128, (gx + 1) * 128
        b_val = valid[y0:y1, x0:x1]
        b_diff = diff[y0:y1, x0:x1]
        b_sig = sig[y0:y1, x0:x1]
        b_sigma = diff_sig[y0:y1, x0:x1]
        
        n_val = int(np.sum(b_val))
        if n_val > 100:
            st = compute_detailed_stats(b_diff[b_val], b_sig[b_val], b_sigma[b_val], b_val, b_sig)
            bname = f"B[{gy},{gx}]"
            blocks_16.append((bname, st))
            print(f"{bname:<7} | {st['n_pix']:<7d} | {st['mean_d']:+8.4f} | {st['std_d']:8.4f} | {st['mad_d']:8.4f} | {st['mean_sigma']:8.4f} | {st['mean_s']:+8.4f} | {st['std_s']:8.4f} | {st['mad_s']:8.4f} | {st['p16']:+7.2f} | {st['p84']:+7.2f} | {st['ratio_std']:9.4f} | {st['ratio_mad']:10.4f} | {st['rx']:+6.3f} | {st['ry']:+6.3f}")

print("\n--- DETAILED BENCHMARK REGIONS STATISTICS ---")
benchmark_boxes = [
    ("Region 1 (Quiet)", 50, 114, 50, 114),
    ("Region 2 (Quiet)", 50, 114, 398, 462),
    ("Region 3 (Quiet)", 398, 462, 50, 114),
    ("Region 4 (Quiet)", 300, 364, 224, 288),
]

print(f"{'Region':<20} | {'Valid N':<7} | {'Mean D':<8} | {'Std D':<8} | {'MAD D':<8} | {'Pred Sig':<8} | {'Mean S':<8} | {'Std S':<8} | {'MAD S':<8} | {'P16':<7} | {'P84':<7} | {'StdD/Pred':<9} | {'MAD D/Pred':<10} | {'rho_x':<6} | {'rho_y':<6}")
print("-" * 170)

for rname, y0, y1, x0, x1 in benchmark_boxes:
    sub_val = valid[y0:y1, x0:x1]
    sub_diff = diff[y0:y1, x0:x1]
    sub_sig = sig[y0:y1, x0:x1]
    sub_sigma = diff_sig[y0:y1, x0:x1]
    n_val = int(np.sum(sub_val))
    if n_val > 100:
        st = compute_detailed_stats(sub_diff[sub_val], sub_sig[sub_val], sub_sigma[sub_val], sub_val, sub_sig)
        print(f"{rname:<20} | {st['n_pix']:<7d} | {st['mean_d']:+8.4f} | {st['std_d']:8.4f} | {st['mad_d']:8.4f} | {st['mean_sigma']:8.4f} | {st['mean_s']:+8.4f} | {st['std_s']:8.4f} | {st['mad_s']:8.4f} | {st['p16']:+7.2f} | {st['p84']:+7.2f} | {st['ratio_std']:9.4f} | {st['ratio_mad']:10.4f} | {st['rx']:+6.3f} | {st['ry']:+6.3f}")

# Full Source-Free & Global
print("-" * 170)
sf_val = source_free_mask
st_sf = compute_detailed_stats(diff[sf_val], sig[sf_val], diff_sig[sf_val], sf_val, np.where(sf_val, sig, np.nan))
print(f"{'Full Source-Free':<20} | {st_sf['n_pix']:<7d} | {st_sf['mean_d']:+8.4f} | {st_sf['std_d']:8.4f} | {st_sf['mad_d']:8.4f} | {st_sf['mean_sigma']:8.4f} | {st_sf['mean_s']:+8.4f} | {st_sf['std_s']:8.4f} | {st_sf['mad_s']:8.4f} | {st_sf['p16']:+7.2f} | {st_sf['p84']:+7.2f} | {st_sf['ratio_std']:9.4f} | {st_sf['ratio_mad']:10.4f} | {st_sf['rx']:+6.3f} | {st_sf['ry']:+6.3f}")

g_val = valid
st_g = compute_detailed_stats(diff[g_val], sig[g_val], diff_sig[g_val], g_val, sig)
print(f"{'Global Field (Valid)':<20} | {st_g['n_pix']:<7d} | {st_g['mean_d']:+8.4f} | {st_g['std_d']:8.4f} | {st_g['mad_d']:8.4f} | {st_g['mean_sigma']:8.4f} | {st_g['mean_s']:+8.4f} | {st_g['std_s']:8.4f} | {st_g['mad_s']:8.4f} | {st_g['p16']:+7.2f} | {st_g['p84']:+7.2f} | {st_g['ratio_std']:9.4f} | {st_g['ratio_mad']:10.4f} | {st_g['rx']:+6.3f} | {st_g['ry']:+6.3f}")


# ------------------------------------------------------------------------------
# AUDIT 4: PHOTOMETRIC RECOVERY & COMPLETENESS AUDIT
# ------------------------------------------------------------------------------
print("\n" + "="*80)
print("AUDIT 4: PHOTOMETRIC RECOVERY AND COMPLETENESS AUDIT")
print("="*80)

# Native EPSF (7x7) from HDU 5 bin 220
with fits.open(f1) as hdul:
    sub_k = hdul["EPSF"].data[220]["EPSF"].astype(np.float64)
pad_epsf = np.pad(sub_k, ((1, 1), (1, 1)), mode="constant", constant_values=0.0)
native_epsf = pad_epsf.reshape(7, 5, 7, 5).sum(axis=(1, 3))
native_epsf /= np.sum(native_epsf)

# Gaussian PSF (FWHM = 2.0 native pixels)
psf_sigma = 2.0 / 2.35482
y_g, x_g = np.ogrid[-4:5, -4:5]
gauss_psf = np.exp(-(x_g**2 + y_g**2) / (2 * psf_sigma**2))
gauss_psf /= np.sum(gauss_psf)

noise_sigma = 0.021 # MJy/sr per single epoch
noise_var = noise_sigma ** 2
sigma_diff = math.sqrt(2.0) * noise_sigma # ~0.0297 MJy/sr

def measure_aperture(diff_img, xc, yc, radius=3.5):
    ny, nx = diff_img.shape
    y, x = np.ogrid[:ny, :nx]
    r = np.hypot(x - xc, y - yc)
    return float(np.sum(diff_img[r <= radius]))

def measure_psf_fit(diff_img, xc, yc, kernel):
    rad = kernel.shape[0] // 2
    ix, iy = int(round(xc)), int(round(yc))
    ny, nx = diff_img.shape
    if ix - rad < 0 or ix + rad >= nx or iy - rad < 0 or iy + rad >= ny:
        return np.nan
    stamp = diff_img[iy-rad:iy+rad+1, ix-rad:ix+rad+1]
    return float(np.sum(stamp * kernel) / np.sum(kernel**2))

snr_levels = [5.0, 7.0, 10.0, 15.0, 20.0, 50.0]
profiles = [("Authentic Level-2 EPSF (7x7)", native_epsf), ("Gaussian (FWHM=2.0px)", gauss_psf)]

grid_size = 256
n_trials = 30
np.random.seed(42)

for pname, kernel in profiles:
    rad = kernel.shape[0] // 2
    peak_frac = float(np.max(kernel))
    print(f"\nProfile: {pname} | Peak fraction: {peak_frac:.4f}")
    
    for pol in ["POSITIVE", "NEGATIVE"]:
        sign = +1.0 if pol == "POSITIVE" else -1.0
        print(f"\n--- Polarity: {pol} ---")
        print(f"{'Target SNR':<10} | {'Input Flux':<10} | {'Comp %':<8} | {'N_det/N_tot':<11} | {'Centroid Err':<12} | {'F_iso Bias %':<14} | {'F_aper Bias %':<15} | {'F_psf Bias %':<14}")
        print("-" * 105)
        
        for snr in snr_levels:
            # target_flux is set such that peak pixel has SNR = snr in diff map
            target_flux = (snr * sigma_diff) / peak_frac
            
            n_det = 0
            pos_errs = []
            f_iso_biases = []
            f_aper_biases = []
            f_psf_biases = []
            
            for _ in range(n_trials):
                # Background images
                img1 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
                img2 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
                v1 = np.full((grid_size, grid_size), noise_var, dtype=np.float32)
                v2 = np.full((grid_size, grid_size), noise_var, dtype=np.float32)
                
                # Injection position with random subpixel jitter
                xi = np.random.randint(60, grid_size - 60)
                yi = np.random.randint(60, grid_size - 60)
                
                img2[yi-rad:yi+rad+1, xi-rad:xi+rad+1] += (sign * target_flux * kernel).astype(np.float32)
                
                dres = compute_difference_and_significance(img1, v1, img2, v2, subtract_residual_background=False)
                diff_m = dres["difference_image"]
                sig_m = dres["significance_map"]
                
                cands = extract_change_candidates(sig_m, diff_m, significance_threshold=3.5, min_area_pixels=3)
                
                # Match candidate
                matched = False
                for c in cands["candidates"]:
                    if c["polarity"] == pol:
                        dist = np.hypot(c["pixel_x"] - xi, c["pixel_y"] - yi)
                        if dist <= 2.5:
                            matched = True
                            n_det += 1
                            pos_errs.append(dist)
                            
                            # Measured fluxes
                            f_iso = abs(c["integrated_flux_mjy_sr"])
                            f_iso_biases.append((f_iso - target_flux) / target_flux * 100.0)
                            
                            f_aper = abs(measure_aperture(diff_m, c["pixel_x"], c["pixel_y"], radius=3.5))
                            f_aper_biases.append((f_aper - target_flux) / target_flux * 100.0)
                            
                            f_psf = abs(measure_psf_fit(diff_m, c["pixel_x"], c["pixel_y"], kernel))
                            f_psf_biases.append((f_psf - target_flux) / target_flux * 100.0)
                            break
                            
            comp_pct = (n_det / n_trials) * 100.0
            det_str = f"{n_det}/{n_trials}"
            
            if n_det > 0:
                c_err_str = f"{np.mean(pos_errs):.2f} +/- {np.std(pos_errs):.2f} px"
                b_iso_str = f"{np.mean(f_iso_biases):+6.1f} +/- {np.std(f_iso_biases):.1f}%"
                b_aper_str = f"{np.mean(f_aper_biases):+6.1f} +/- {np.std(f_aper_biases):.1f}%"
                b_psf_str = f"{np.mean(f_psf_biases):+6.1f} +/- {np.std(f_psf_biases):.1f}%"
            else:
                c_err_str = "nan"
                b_iso_str = "nan"
                b_aper_str = "nan"
                b_psf_str = "nan"
                
            print(f"{snr:<10.1f} | {target_flux:<10.4f} | {comp_pct:<7.1f}% | {det_str:<11} | {c_err_str:<12} | {b_iso_str:<14} | {b_aper_str:<15} | {b_psf_str:<14}")

# Test multiple detector locations and image boundaries
print("\n--- TEST: DETECTOR LOCATIONS AND BOUNDARY EFFECTS ---")
loc_tests = [
    ("Detector Center (128, 128)", 128, 128),
    ("Intermediate (70, 70)", 70, 70),
    ("Corner (25, 25)", 25, 25),
    ("Boundary Near Edge (10, 10)", 10, 10),
    ("Extreme Edge (4, 4)", 4, 4),
]
print(f"{'Location Description':<28} | {'(X, Y)':<10} | {'Detected':<8} | {'Warnings':<25} | {'F_iso Bias%':<12} | {'F_aper Bias%':<12} | {'F_psf Bias%':<12}")
print("-" * 115)

kernel = gauss_psf
rad = kernel.shape[0] // 2
snr = 20.0
target_flux = (snr * sigma_diff) / float(np.max(kernel))

for desc, xi, yi in loc_tests:
    img1 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
    img2 = np.random.normal(0.0, noise_sigma, (grid_size, grid_size)).astype(np.float32)
    v1 = np.full((grid_size, grid_size), noise_var, dtype=np.float32)
    v2 = np.full((grid_size, grid_size), noise_var, dtype=np.float32)
    
    # Clip stamp injection to avoid out of bounds
    x0, x1 = max(0, xi - rad), min(grid_size, xi + rad + 1)
    y0, y1 = max(0, yi - rad), min(grid_size, yi + rad + 1)
    kx0, kx1 = x0 - (xi - rad), x1 - (xi - rad)
    ky0, ky1 = y0 - (yi - rad), y1 - (yi - rad)
    img2[y0:y1, x0:x1] += (target_flux * kernel[ky0:ky1, kx0:kx1]).astype(np.float32)
    
    dres = compute_difference_and_significance(img1, v1, img2, v2, subtract_residual_background=False)
    diff_m = dres["difference_image"]
    sig_m = dres["significance_map"]
    
    cands = extract_change_candidates(sig_m, diff_m, significance_threshold=3.5, min_area_pixels=3)
    
    matched = False
    for c in cands["candidates"]:
        if np.hypot(c["pixel_x"] - xi, c["pixel_y"] - yi) <= 3.0:
            matched = True
            f_iso = abs(c["integrated_flux_mjy_sr"])
            b_iso = (f_iso - target_flux) / target_flux * 100.0
            f_aper = abs(measure_aperture(diff_m, c["pixel_x"], c["pixel_y"], radius=3.5))
            b_aper = (f_aper - target_flux) / target_flux * 100.0
            f_psf = abs(measure_psf_fit(diff_m, c["pixel_x"], c["pixel_y"], kernel))
            b_psf = (f_psf - target_flux) / target_flux * 100.0
            w_str = str(c["warnings"]) if c["warnings"] else "None"
            print(f"{desc:<28} | ({xi:3d}, {yi:3d}) | {str(matched):<8} | {w_str:<25} | {b_iso:+11.1f}% | {b_aper:+11.1f}% | {b_psf:+11.1f}%")
            break
    if not matched:
        print(f"{desc:<28} | ({xi:3d}, {yi:3d}) | False    | N/A                       | nan         | nan         | nan")

# Test multiple background levels
print("\n--- TEST: MULTIPLE BACKGROUND LEVELS ---")
bg_levels = [0.0, 5.0, 20.0, 50.0, 100.0]
print(f"{'Background Level (MJy/sr)':<26} | {'Residual Sky Diff (MJy/sr)':<28} | {'F_aper Bias %':<15} | {'F_psf Bias %':<15}")
print("-" * 90)

for bg in bg_levels:
    img1 = np.random.normal(bg, noise_sigma, (grid_size, grid_size)).astype(np.float32)
    img2 = np.random.normal(bg, noise_sigma, (grid_size, grid_size)).astype(np.float32)
    v1 = np.full((grid_size, grid_size), noise_var, dtype=np.float32)
    v2 = np.full((grid_size, grid_size), noise_var, dtype=np.float32)
    
    xi, yi = 128, 128
    img2[yi-rad:yi+rad+1, xi-rad:xi+rad+1] += (target_flux * kernel).astype(np.float32)
    
    dres = compute_difference_and_significance(img1, v1, img2, v2, subtract_residual_background=True)
    diff_m = dres["difference_image"]
    sig_m = dres["significance_map"]
    
    res_sky = float(np.nanmedian(diff_m))
    f_aper = abs(measure_aperture(diff_m, xi, yi, radius=3.5))
    b_aper = (f_aper - target_flux) / target_flux * 100.0
    f_psf = abs(measure_psf_fit(diff_m, xi, yi, kernel))
    b_psf = (f_psf - target_flux) / target_flux * 100.0
    
    print(f"{bg:<26.1f} | {res_sky:+28.6e} | {b_aper:+14.1f}% | {b_psf:+14.1f}%")

# ------------------------------------------------------------------------------
# AUDIT 5: FALSE-POSITIVE CONFIDENCE AND POISSON LIMITS
# ------------------------------------------------------------------------------
print("\n" + "="*80)
print("AUDIT 5: FALSE-POSITIVE CONFIDENCE AND POISSON LIMITS")
print("="*80)

n_null_frames = 50
grid_dim = 512
total_pixels = n_null_frames * (grid_dim ** 2)
pix_scale_deg = 0.0017222 # ~6.2 arcsec / 3600 deg
sq_deg_per_frame = (grid_dim * pix_scale_deg) ** 2
total_sq_deg = n_null_frames * sq_deg_per_frame

px_cross_35 = 0
px_cross_50 = 0
cc_comps_35 = 0
cc_comps_50 = 0
ops_cands_35 = 0
ops_cands_50 = 0

for _ in range(n_null_frames):
    i1 = np.random.normal(0.0, noise_sigma, (grid_dim, grid_dim)).astype(np.float32)
    i2 = np.random.normal(0.0, noise_sigma, (grid_dim, grid_dim)).astype(np.float32)
    v1 = np.full((grid_dim, grid_dim), noise_var, dtype=np.float32)
    v2 = np.full((grid_dim, grid_dim), noise_var, dtype=np.float32)
    
    dres = compute_difference_and_significance(i1, v1, i2, v2, subtract_residual_background=False)
    s = dres["significance_map"]
    d = dres["difference_image"]
    
    px_cross_35 += int(np.sum(np.abs(s) >= 3.5))
    px_cross_50 += int(np.sum(np.abs(s) >= 5.0))
    
    c_raw35 = extract_change_candidates(s, d, significance_threshold=3.5, min_area_pixels=1)
    c_raw50 = extract_change_candidates(s, d, significance_threshold=5.0, min_area_pixels=1)
    cc_comps_35 += c_raw35["candidate_count"]
    cc_comps_50 += c_raw50["candidate_count"]
    
    c_ops35 = extract_change_candidates(s, d, significance_threshold=3.5, min_area_pixels=3)
    c_ops50 = extract_change_candidates(s, d, significance_threshold=5.0, min_area_pixels=3)
    ops_cands_35 += c_ops35["candidate_count"]
    ops_cands_50 += c_ops50["candidate_count"]

print(f"Total Evaluated Null Frames: {n_null_frames}")
print(f"Total Evaluated Null Pixels: {total_pixels:,}")
print(f"Surveyed Sky Area: {total_sq_deg:.4f} sq deg")

# Theoretical 2-sided normal tail
import scipy.stats as st
p_tail_35 = 2.0 * (1.0 - st.norm.cdf(3.5)) # ~4.6526e-4
p_tail_50 = 2.0 * (1.0 - st.norm.cdf(5.0)) # ~5.7330e-7

print(f"\n[Threshold 3.5 sigma]:")
print(f"  Pixel Crossings: {px_cross_35:,} (rate = {px_cross_35/total_pixels:.4e} vs theoretical {p_tail_35:.4e})")
print(f"  Connected Components (area >= 1): {cc_comps_35:,} (rate = {cc_comps_35/n_null_frames:.1f}/frame)")
print(f"  Operational Candidates (area >= 3): {ops_cands_35} (rate = {ops_cands_35/n_null_frames:.4f}/frame)")

print(f"\n[Threshold 5.0 sigma]:")
print(f"  Pixel Crossings: {px_cross_50:,} (rate = {px_cross_50/total_pixels:.4e} vs theoretical {p_tail_50:.4e})")
print(f"  Connected Components (area >= 1): {cc_comps_50:,} (rate = {cc_comps_50/n_null_frames:.1f}/frame)")
print(f"  Operational Candidates (area >= 3): {ops_cands_50} (rate = {ops_cands_50/n_null_frames:.4f}/frame)")

# 95% Poisson confidence upper bound when zero events observed:
# P(k=0 | lambda) = exp(-lambda) = 0.05 => lambda_95 = -ln(0.05) = 2.995732
lambda_95 = -math.log(0.05)
print(f"\n95% Poisson Upper Bound for Zero Observed Candidates:")
print(f"  Total Survey: < {lambda_95:.4f} false events across {n_null_frames} frames ({total_sq_deg:.4f} sq deg)")
print(f"  Upper bound rate per frame: < {lambda_95 / n_null_frames:.6f} candidates/frame")
print(f"  Upper bound rate per sq deg: < {lambda_95 / total_sq_deg:.6f} candidates/sq deg")
print(f"  Upper bound rate per pixel: < {lambda_95 / total_pixels:.6e} candidates/pixel")

# Real-data residual assessment without assuming astrophysical sources
print("\n--- REAL DATA SOURCE-FREE RESIDUAL CANDIDATES ASSESSMENT ---")
sf_sig_map = np.where(source_free_mask, sig, np.nan)
sf_diff_map = np.where(source_free_mask, diff, np.nan)

c_real_35 = extract_change_candidates(sf_sig_map, sf_diff_map, significance_threshold=3.5, min_area_pixels=3)
c_real_50 = extract_change_candidates(sf_sig_map, sf_diff_map, significance_threshold=5.0, min_area_pixels=3)

n_sf_pix = int(np.sum(source_free_mask))
sf_sq_deg = n_sf_pix * (pix_scale_deg ** 2)

print(f"Real Data Source-Free Sky Pixels: {n_sf_pix:,} ({sf_sq_deg:.4f} sq deg)")
print(f"Candidates at 3.5 sigma: {c_real_35['candidate_count']} (Observed density: {c_real_35['candidate_count']/sf_sq_deg:.1f}/sq deg)")
print(f"Candidates at 5.0 sigma: {c_real_50['candidate_count']} (Observed density: {c_real_50['candidate_count']/sf_sq_deg:.1f}/sq deg)")

# Analyze whether these candidates can be definitively classified as astrophysical:
print("\nScientific Integrity Assessment of Real-Data 'Source-Free' Candidates:")
print("  Rule: Do NOT classify catalog-masked residuals as astrophysical sources without independent evidence.")
print(f"  Observed candidates in catalog source-free mask: {c_real_35['candidate_count']}")
for i, cand in enumerate(c_real_35["candidates"][:5]):
    print(f"    Cand #{i+1}: ID={cand['candidate_id']} | Peak S={cand['significance_peak']:+.2f} | Area={cand['area_pixels']} px | IntFlux={cand['integrated_flux_mjy_sr']:+.4f} | Warnings={cand['warnings']}")

print("\n================================================================================")
print("AUDIT EXECUTION COMPLETE")
print("================================================================================")
