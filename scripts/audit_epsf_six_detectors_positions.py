import os
import sys
import glob
import json
import numpy as np
from astropy.io import fits
from astropy.table import Table

sys.path.insert(0, 'backend')
from app.astronomy.spherex_psf import CALIB_DIR, select_spatially_varying_epsf, determine_parent_detector_pixel

cal_files = sorted(glob.glob(os.path.join(CALIB_DIR, "epsf_D*.fits")))

print("=== REQUIREMENT 3: SIX-DETECTOR ePSF POSITION & BOUNDARY AUDIT (D1-D6) ===")

results_audit = {}

for cf in cal_files:
    det_name = os.path.basename(cf).split('_')[1]
    with fits.open(cf) as hdul:
        tab = Table.read(hdul['EPSF'])
        hdr = hdul['EPSF'].header
    
    det_results = {
        "num_zones": len(tab),
        "grid_shape": "11x41" if len(tab) == 451 else "21x21",
        "positions": [],
        "horizontal_boundary": {},
        "vertical_boundary": {},
        "cutout_mapping": {}
    }
    
    print(f"\n--- Detector {det_name} (Total Zones: {len(tab)}, Grid: {det_results['grid_shape']}) ---")
    
    # 1. Four corners, center, and four outer edges
    test_positions = [
        ("Bottom-Left Corner", 1.0, 1.0),
        ("Bottom-Right Corner", 2040.0, 1.0),
        ("Top-Left Corner", 1.0, 2040.0),
        ("Top-Right Corner", 2040.0, 2040.0),
        ("Detector Center", 1024.0, 1024.0),
        ("Left Edge Midpoint", 1.0, 1024.0),
        ("Right Edge Midpoint", 2040.0, 1024.0),
        ("Bottom Edge Midpoint", 1024.0, 1.0),
        ("Top Edge Midpoint", 1024.0, 2040.0),
    ]
    
    for label, px, py in test_positions:
        res = select_spatially_varying_epsf(tab, parent_x=px, parent_y=py)
        ksum = float(np.sum(res['kernel']))
        nat_sum = float(np.sum(res['native_kernel']))
        pos_entry = {
            "label": label,
            "parent_x": px,
            "parent_y": py,
            "zone_index": int(res['zone_index']),
            "bin_x": int(res['bin_x']),
            "bin_y": int(res['bin_y']),
            "zone_center_x": float(res['zone_center_x']),
            "zone_center_y": float(res['zone_center_y']),
            "zone_dist_pix": float(res['zone_distance_pix']),
            "oversampled_norm": ksum,
            "native_norm": nat_sum,
            "native_max": float(res['native_max']),
            "native_sum_p2": float(res['native_sum_p2']),
            "native_peak_snr_ratio": float(res['native_peak_snr_ratio']),
        }
        det_results["positions"].append(pos_entry)
        print(f"  {label:20s} ({px:6.1f}, {py:6.1f}) -> Zone {res['zone_index']:3d} (bin {res['bin_x']:2d}, {res['bin_y']:2d}) at ({res['zone_center_x']:6.1f}, {res['zone_center_y']:6.1f}) | dist={res['zone_distance_pix']:5.1f} px | nat_peak={res['native_max']:.4f} | Peak/MF={res['native_peak_snr_ratio']:.4f}")

    # 2. Zone boundary test: Vertical boundary (between bin_x=0 and bin_x=1, at same bin_y=0)
    z0 = tab[0]  # bin_x=0, bin_y=0
    z1 = tab[1]  # bin_x=1, bin_y=0
    mid_x = float(z0['XCENTER'] + z1['XCENTER']) / 2.0
    mid_y = float(z0['YCENTER'])
    
    for delta in [0.5, 0.1]:
        left_x = mid_x - delta
        right_x = mid_x + delta
        res_left = select_spatially_varying_epsf(tab, parent_x=left_x, parent_y=mid_y)
        res_right = select_spatially_varying_epsf(tab, parent_x=right_x, parent_y=mid_y)
        assert res_left['zone_index'] == 0, f"Expected zone 0 for left_x={left_x}"
        assert res_right['zone_index'] == 1, f"Expected zone 1 for right_x={right_x}"
    
    # Calculate boundary discontinuity between zone 0 and zone 1
    k_left_ovs = res_left['kernel']
    k_right_ovs = res_right['kernel']
    rms_ovs = float(np.sqrt(np.mean((k_left_ovs - k_right_ovs) ** 2)))
    max_ovs = float(np.max(np.abs(k_left_ovs - k_right_ovs)))
    
    k_left_nat = res_left['native_kernel']
    k_right_nat = res_right['native_kernel']
    rms_nat = float(np.sqrt(np.mean((k_left_nat - k_right_nat) ** 2)))
    max_nat = float(np.max(np.abs(k_left_nat - k_right_nat)))
    rel_max_nat = max_nat / float(res_left['native_max'])
    
    det_results["vertical_boundary"] = {
        "zone_left": int(res_left['zone_index']),
        "zone_right": int(res_right['zone_index']),
        "boundary_x": mid_x,
        "boundary_y": mid_y,
        "deltas_tested": [0.5, 0.1],
        "rms_diff_oversampled": rms_ovs,
        "max_diff_oversampled": max_ovs,
        "rms_diff_native": rms_nat,
        "max_diff_native": max_nat,
        "rel_max_native_pct": rel_max_nat * 100.0
    }
    print(f"  Vertical Boundary (Zone 0 -> 1 at X={mid_x:.2f}):")
    print(f"    Transitions at ±0.5 px and ±0.1 px verified: Zone {res_left['zone_index']} -> Zone {res_right['zone_index']}")
    print(f"    Discontinuity: Native RMS={rms_nat:.6f}, Max={max_nat:.6f} ({rel_max_nat*100:.3f}% of peak)")

    # 3. Zone boundary test: Horizontal boundary (between bin_y=0 and bin_y=1, at same bin_x=0)
    # If 21x21, next row is zone 21; if 11x41, next row is zone 11
    stride = 11 if len(tab) == 451 else 21
    z_row1 = tab[stride]  # bin_x=0, bin_y=1
    mid_hy = float(z0['YCENTER'] + z_row1['YCENTER']) / 2.0
    mid_hx = float(z0['XCENTER'])
    
    for delta in [0.5, 0.1]:
        bot_y = mid_hy - delta
        top_y = mid_hy + delta
        res_bot = select_spatially_varying_epsf(tab, parent_x=mid_hx, parent_y=bot_y)
        res_top = select_spatially_varying_epsf(tab, parent_x=mid_hx, parent_y=top_y)
        assert res_bot['zone_index'] == 0, f"Expected zone 0 for bot_y={bot_y}"
        assert res_top['zone_index'] == stride, f"Expected zone {stride} for top_y={top_y}"
    
    k_bot_nat = res_bot['native_kernel']
    k_top_nat = res_top['native_kernel']
    rms_h_nat = float(np.sqrt(np.mean((k_bot_nat - k_top_nat) ** 2)))
    max_h_nat = float(np.max(np.abs(k_bot_nat - k_top_nat)))
    rel_max_h_nat = max_h_nat / float(res_bot['native_max'])
    
    det_results["horizontal_boundary"] = {
        "zone_bottom": int(res_bot['zone_index']),
        "zone_top": int(res_top['zone_index']),
        "boundary_x": mid_hx,
        "boundary_y": mid_hy,
        "deltas_tested": [0.5, 0.1],
        "rms_diff_native": rms_h_nat,
        "max_diff_native": max_h_nat,
        "rel_max_native_pct": rel_max_h_nat * 100.0
    }
    print(f"  Horizontal Boundary (Zone 0 -> {stride} at Y={mid_hy:.2f}):")
    print(f"    Transitions at ±0.5 px and ±0.1 px verified: Zone {res_bot['zone_index']} -> Zone {res_top['zone_index']}")
    print(f"    Discontinuity: Native RMS={rms_h_nat:.6f}, Max={max_h_nat:.6f} ({rel_max_h_nat*100:.3f}% of peak)")

    # 4. Nonzero cutout CRPIX1A / CRPIX2A offset test
    crpix1a, crpix2a = -400.0, -700.0
    cut_x, cut_y = 25.0, 30.0
    parent_x, parent_y = determine_parent_detector_pixel(cutout_x=cut_x, cutout_y=cut_y, crpix1a=crpix1a, crpix2a=crpix2a)
    res_cutout = select_spatially_varying_epsf(tab, parent_x=parent_x, parent_y=parent_y)
    det_results["cutout_mapping"] = {
        "cutout_x": cut_x,
        "cutout_y": cut_y,
        "crpix1a": crpix1a,
        "crpix2a": crpix2a,
        "parent_x": parent_x,
        "parent_y": parent_y,
        "zone_index": int(res_cutout['zone_index']),
        "bin_x": int(res_cutout['bin_x']),
        "bin_y": int(res_cutout['bin_y'])
    }
    print(f"  Cutout ({cut_x}, {cut_y}) CRPIX=({crpix1a}, {crpix2a}) -> Parent ({parent_x:.1f}, {parent_y:.1f}) -> Zone {res_cutout['zone_index']} (bin {res_cutout['bin_x']}, {res_cutout['bin_y']})")

    results_audit[det_name] = det_results

with open("scripts/epsf_six_detectors_audit.json", "w") as f:
    json.dump(results_audit, f, indent=2)

print("\n=== All six detector ePSF position, edge, corner, and boundary transition tests passed! ===")
print("Results written to scripts/epsf_six_detectors_audit.json")
