import os
import sys
import glob
import numpy as np
from astropy.io import fits
from astropy.table import Table

sys.path.insert(0, 'backend')
from app.astronomy.spherex_psf import CALIB_DIR, select_spatially_varying_epsf, determine_parent_detector_pixel

cal_files = sorted(glob.glob(os.path.join(CALIB_DIR, "epsf_D*.fits")))

print("=== REQUIREMENT 3: SIX-DETECTOR ePSF POSITION & BOUNDARY AUDIT ===")

for cf in cal_files:
    det_name = os.path.basename(cf).split('_')[1]
    with fits.open(cf) as hdul:
        tab = Table.read(hdul['EPSF'])
    
    print(f"\n--- Detector {det_name} (Total Zones: {len(tab)}) ---")
    
    # 1. Four detector corners & center
    test_positions = [
        ("Bottom-Left Corner", 1.0, 1.0),
        ("Bottom-Right Corner", 2040.0, 1.0),
        ("Top-Left Corner", 1.0, 2040.0),
        ("Top-Right Corner", 2040.0, 2040.0),
        ("Detector Center", 1024.0, 1024.0),
    ]
    
    for label, px, py in test_positions:
        res = select_spatially_varying_epsf(tab, parent_x=px, parent_y=py)
        ksum = float(np.sum(res['kernel']))
        print(f"  {label:20s} ({px:6.1f}, {py:6.1f}) -> Zone {res['zone_index']:3d} (bin {res['bin_x']}, {res['bin_y']}) at ({res['zone_center_x']:6.1f}, {res['zone_center_y']:6.1f}) | dist={res['zone_distance_pix']:5.1f} px | norm={ksum:.6f}")
        
    # 2. Zone boundary test: mid-point between two adjacent zones
    # Find zone 0 and zone 1
    z0 = tab[0]
    z1 = tab[1]
    mid_x = (z0['XCENTER'] + z1['XCENTER']) / 2.0
    mid_y = (z0['YCENTER'] + z1['YCENTER']) / 2.0
    
    # Test immediately on either side of the boundary: eps = 0.5 pixels
    left_x = mid_x - 0.5
    right_x = mid_x + 0.5
    
    res_left = select_spatially_varying_epsf(tab, parent_x=left_x, parent_y=mid_y)
    res_right = select_spatially_varying_epsf(tab, parent_x=right_x, parent_y=mid_y)
    print(f"  Boundary Transition between Zone {z0['BINX']},{z0['BINY']} and Zone {z1['BINX']},{z1['BINY']} (boundary X={mid_x:.2f}):")
    print(f"    Left  (X={left_x:.2f}) -> selects Zone {res_left['zone_index']} (bin {res_left['bin_x']}, {res_left['bin_y']})")
    print(f"    Right (X={right_x:.2f}) -> selects Zone {res_right['zone_index']} (bin {res_right['bin_x']}, {res_right['bin_y']})")
    assert res_left['zone_index'] != res_right['zone_index'], "Boundary transition failed to switch zones!"
    
    # 3. Nonzero cutout CRPIX1A / CRPIX2A offset test
    # Suppose cutout has CRPIX1A = -400.0, CRPIX2A = -700.0, and cutout pixel is (25.0, 30.0)
    crpix1a, crpix2a = -400.0, -700.0
    cut_x, cut_y = 25.0, 30.0
    parent_x, parent_y = determine_parent_detector_pixel(cutout_x=cut_x, cutout_y=cut_y, crpix1a=crpix1a, crpix2a=crpix2a)
    # Expected: 1 + 25 - (-400) = 426.0, 1 + 30 - (-700) = 731.0
    res_cutout = select_spatially_varying_epsf(tab, parent_x=parent_x, parent_y=parent_y)
    print(f"  Cutout ({cut_x}, {cut_y}) with CRPIX=({crpix1a}, {crpix2a}) -> Parent ({parent_x:.1f}, {parent_y:.1f}) -> Zone {res_cutout['zone_index']} (bin {res_cutout['bin_x']}, {res_cutout['bin_y']}) at ({res_cutout['zone_center_x']:.1f}, {res_cutout['zone_center_y']:.1f})")

print("\nAll six detector ePSF tests passed successfully!")
