from astropy.io import fits
import numpy as np

def analyze_epsf_integration(d=1, zone=0):
    fn = f'data/spherex/calibrations/epsf_D{d}_spx_cal-epsf-v1-2026-191.fits' if d != 3 else 'data/spherex/calibrations/epsf_D3_spx_cal-epsf-v2-2026-191.fits'
    with fits.open(fn) as h:
        k = np.array(h[1].data['EPSF'][zone], dtype=np.float64)
    
    # 1. Oversampled stats
    sum_os = np.sum(k)
    max_os = np.max(k)
    sum_p2_os = np.sum(k**2)
    
    # Subpixel coordinates relative to center (16, 16)
    y_os, x_os = np.indices((33, 33))
    cy_os = np.sum(y_os * k) / sum_os
    cx_os = np.sum(x_os * k) / sum_os
    
    # 2. Integration into 7x7 native pixels
    # Method A: Box summation where bins are:
    # 0: [0:4] (4 subpix), 1: [4:9] (5), 2: [9:14] (5), 3: [14:19] (5), 4: [19:24] (5), 5: [24:29] (5), 6: [29:33] (4)
    slices = [slice(0, 4), slice(4, 9), slice(9, 14), slice(14, 19), slice(19, 24), slice(24, 29), slice(29, 33)]
    native_A = np.zeros((7, 7), dtype=np.float64)
    for iy, sy in enumerate(slices):
        for ix, sx in enumerate(slices):
            native_A[iy, ix] = np.sum(k[sy, sx])
            
    # Method B: Area-weighted integration or padding 1 subpixel with edge value/0 to make 35x35 then block sum 5x5
    # If we pad with zeros to 35x35 (pad 1 pixel on each side):
    k_pad = np.pad(k, 1, mode='constant', constant_values=0.0) # shape (35, 35)
    native_B = k_pad.reshape(7, 5, 7, 5).sum(axis=(1, 3))
    
    # Method C: Subpixel-weighted integration:
    # Subpixel width = 0.2 native pixels.
    # A full native pixel has width 1.0 (5 subpixels of width 0.2).
    # Since sum(k) was normalized to 1.0 over all 33x33 subpixels,
    # summing the subpixels directly inside each native pixel bin preserves the total flux exactly:
    # sum(native_A) == sum(k) == 1.000000!
    
    sum_nat = np.sum(native_A)
    max_nat = np.max(native_A)
    sum_p2_nat = np.sum(native_A**2)
    
    y_nat, x_nat = np.indices((7, 7))
    cy_nat = np.sum(y_nat * native_A) / sum_nat
    cx_nat = np.sum(x_nat * native_A) / sum_nat
    
    # Map native centroid back to subpixel scale for comparison:
    # Native index 3 corresponds to center 16.
    # Native index j corresponds to subpixel:
    # j=0: 1.5, j=1: 6.5, j=2: 11.5, j=3: 16.0, j=4: 20.5, j=5: 25.5, j=6: 30.5
    # Let's check centroid displacement:
    # Native center is index 3.0.
    cx_nat_offset = cx_nat - 3.0
    cy_nat_offset = cy_nat - 3.0
    cx_os_offset = (cx_os - 16.0) / 5.0
    cy_os_offset = (cy_os - 16.0) / 5.0
    disp = np.hypot(cx_nat_offset - cx_os_offset, cy_nat_offset - cy_os_offset)
    
    print(f"=== Detector D{d} Zone {zone} ===")
    print(f"Oversampled: sum={sum_os:.6f}, max={max_os:.6f}, sum(P^2)={sum_p2_os:.6f}, centroid=({cx_os:.4f}, {cy_os:.4f})")
    print(f"Native 7x7:  sum={sum_nat:.6f}, max={max_nat:.6f}, sum(P^2)={sum_p2_nat:.6f}, centroid=({cx_nat:.4f}, {cy_nat:.4f})")
    print(f"Flux error:  {abs(sum_nat - sum_os):.2e}")
    print(f"Centroid displacement (native px): {disp:.6f}")
    print(f"Peak-to-total SNR ratio: max(P)/sqrt(sum(P^2)) = {max_nat / np.sqrt(sum_p2_nat):.4f}")
    print(f"Native central 3x3:\n{np.round(native_A[2:5, 2:5], 4)}")

analyze_epsf_integration(1, 0)
analyze_epsf_integration(1, 220)
analyze_epsf_integration(3, 225)
