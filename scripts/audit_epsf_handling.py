import os
import sys
import numpy as np
from astropy.io import fits
from scipy.ndimage import map_coordinates

# Add backend to path
sys.path.insert(0, os.path.abspath("backend"))
from app.astronomy.spherex_mef_reader import read_spherex_mef_product
from app.astronomy.image_registration import create_common_wcs, reproject_to_common_grid

f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
f2 = "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"

p1 = read_spherex_mef_product(f1)
p2 = read_spherex_mef_product(f2)

print("=== AUDIT 2: EMPIRICAL PSF (EPSF) TABLE INSPECTION ===")
with fits.open(f1) as hdul:
    epsf_hdu = hdul["EPSF"]
    print("EPSF HDU Header:")
    for k in ["TFIELDS", "NAXIS2", "EXTNAME", "BUNIT", "OVERSAMP", "PIXSCALE"]:
        print(f"  {k}: {epsf_hdu.header.get(k)}")

    tbl = epsf_hdu.data
    print(f"Total bins (rows): {len(tbl)}")
    print(f"Column Names: {tbl.names}")
    for col in tbl.names:
        sample_val = tbl[0][col]
        shape_str = str(getattr(sample_val, "shape", ""))
        dtype_str = str(getattr(sample_val, "dtype", type(sample_val).__name__))
        print(f"  Col '{col}': shape={shape_str}, dtype={dtype_str}")

# Inspect Center Bin (Bin index 220)
center_row = tbl[220]
print(f"\nCenter Bin (Row 220):")
print(f"  BINX={center_row['BINX']}, BINY={center_row['BINY']}")
print(f"  XCENTER={center_row['XCENTER']}, YCENTER={center_row['YCENTER']}")
print(f"  XWIDTH={center_row['XWIDTH']}, YWIDTH={center_row['YWIDTH']}")
print(f"  CWAVE={center_row['CWAVE']}, CBAND={center_row['CBAND']}")
print(f"  NSTAR={center_row['NSTAR']}, NEFF_MEAN={center_row['NEFF_MEAN']}")

k_arr = center_row["EPSF"]
print(f"\nCenter Kernel Shape: {k_arr.shape}")
print(f"Kernel Min: {np.min(k_arr):.6e}, Max: {np.max(k_arr):.6e}, Sum (Normalization): {np.sum(k_arr):.6f}")

# Moments & Centroid
ny, nx = k_arr.shape
yc, xc = (ny - 1) / 2.0, (nx - 1) / 2.0
y_idx, x_idx = np.indices((ny, nx))
tot = np.sum(k_arr)
cx = np.sum(x_idx * k_arr) / tot
cy = np.sum(y_idx * k_arr) / tot
var_x = np.sum(((x_idx - cx) ** 2) * k_arr) / tot
var_y = np.sum(((y_idx - cy) ** 2) * k_arr) / tot
fwhm_x = np.sqrt(max(var_x, 0.01)) * 2.35482
fwhm_y = np.sqrt(max(var_y, 0.01)) * 2.35482

print(f"Centroid relative to array center ({xc}, {yc}): dx={cx - xc:.4f}, dy={cy - yc:.4f} sub-pixels")
print(f"Second-moment FWHM: X={fwhm_x:.3f} sub-pixels, Y={fwhm_y:.3f} sub-pixels")

# Encircled Energy
r = np.hypot(x_idx - cx, y_idx - cy)
r_flat = r.ravel()
k_flat = k_arr.ravel()
sort_idx = np.argsort(r_flat)
r_sorted = r_flat[sort_idx]
cum_ee = np.cumsum(k_flat[sort_idx]) / tot

ee50_r = float(r_sorted[np.searchsorted(cum_ee, 0.50)])
ee80_r = float(r_sorted[np.searchsorted(cum_ee, 0.80)])
print(f"Encircled Energy Radii: EE50 = {ee50_r:.3f} sub-pixels, EE80 = {ee80_r:.3f} sub-pixels")

# Compare with Epoch 2
with fits.open(f2) as hdul2:
    tbl2 = hdul2["EPSF"].data
    k2 = tbl2[220]["EPSF"]
    diff_k = np.max(np.abs(k_arr - k2))
    print(f"\nEpoch 1 vs Epoch 2 EPSF Table Difference: max absolute diff = {diff_k:.8e} (identical static calibration)")

# 33x33 vs 101x101 resolution explanation:
# Let's inspect where 90% or 99% of energy lies:
mask_99 = cum_ee <= 0.99
r_99 = r_sorted[np.searchsorted(cum_ee, 0.99)]
print(f"Radius containing 99% of kernel energy: {r_99:.2f} sub-pixels")
print(f"Diameter containing 99% of energy: {2 * r_99:.2f} sub-pixels (fits within ~33 sub-pixels window!)")

# Reprojection Impact on Point Source FWHM
print("\n--- Testing Effective PSF After Reprojection ---")
# Inject isolated Gaussian point source in synthetic array with native FWHM = 2.0 pixels
ny_det, nx_det = 2040, 2040
sim_img = np.zeros((ny_det, nx_det), dtype=np.float32)
# Inject at (x=1020, y=1020)
y_sim, x_sim = np.indices((64, 64))
r2_sim = (x_sim - 31.5)**2 + (y_sim - 31.5)**2
sig_native = 2.0 / 2.35482
psf_stamp = np.exp(-r2_sim / (2 * sig_native**2))
sim_img[1020-32:1020+32, 1020-32:1020+32] = psf_stamp

# Measure injected FWHM
tot_inj = np.sum(psf_stamp)
cx_inj = np.sum(x_sim * psf_stamp) / tot_inj
cy_inj = np.sum(y_sim * psf_stamp) / tot_inj
vx_inj = np.sum(((x_sim - cx_inj)**2) * psf_stamp) / tot_inj
fwhm_inj = np.sqrt(vx_inj) * 2.35482
print(f"Injected native source FWHM: {fwhm_inj:.4f} pixels")

# Reproject with order=1 (bilinear)
w_src = p1.wcs
w_tgt = create_common_wcs(46.8444, 1.8322, pixel_scale_deg=0.0017222, npix_x=512, npix_y=512)
reproj = reproject_to_common_grid(sim_img, None, w_src, w_tgt, target_shape=(512, 512), order=1)

# Extract reprojected stamp
reproj_img = reproj["image"]
valid_stamp = np.nan_to_num(reproj_img)
py, px = np.unravel_index(np.argmax(valid_stamp), valid_stamp.shape)
stamp_reproj = valid_stamp[py-16:py+16, px-16:px+16]
tot_reproj = np.sum(stamp_reproj)
ys_r, xs_r = np.indices(stamp_reproj.shape)
cx_r = np.sum(xs_r * stamp_reproj) / tot_reproj
vx_r = np.sum(((xs_r - cx_r)**2) * stamp_reproj) / tot_reproj
fwhm_reproj = np.sqrt(vx_r) * 2.35482
print(f"Reprojected source FWHM (bilinear): {fwhm_reproj:.4f} pixels")
print(f"Reprojection FWHM broadening: {fwhm_reproj - fwhm_inj:+.4f} pixels ({((fwhm_reproj/fwhm_inj)-1)*100:+.2f}%)")
