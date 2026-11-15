import os
import astropy.io.fits as fits
from astropy.wcs import WCS

files = [
    './data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits',
    './data/fits/wise-0855.fits'
]

for p in files:
    if not os.path.exists(p):
        print("Not found:", p)
        continue
    print("=" * 60)
    print("FITS FILE:", p)
    print("=" * 60)
    with fits.open(p) as hdul:
        hdul.info()
        for idx, hdu in enumerate(hdul):
            hdr = hdu.header
            data_shape = hdu.data.shape if hdu.data is not None else None
            print(f"\n--- HDU {idx}: {hdu.name} ---")
            print(f"Data shape: {data_shape}")
            print(f"BITPIX: {hdr.get('BITPIX')}")
            print(f"NAXIS: {hdr.get('NAXIS')}, NAXIS1: {hdr.get('NAXIS1')}, NAXIS2: {hdr.get('NAXIS2')}")
            for key in ['CTYPE1', 'CTYPE2', 'CRVAL1', 'CRVAL2', 'CRPIX1', 'CRPIX2', 'CDELT1', 'CDELT2', 'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2', 'CUNIT1', 'CUNIT2']:
                if key in hdr:
                    print(f"  {key}: {hdr[key]}")

            # Test WCS projection for WISE 0855
            # Catalog: RA 133.795129, Dec -7.245147
            # Propagated: RA 133.759213, Dec -7.242009
            try:
                w = WCS(hdr)
                if w.is_celestial:
                    cat_ra, cat_dec = 133.795129, -7.245147
                    prop_ra, prop_dec = 133.759213, -7.242009
                    cat_px = w.world_to_pixel_values(cat_ra, cat_dec)
                    prop_px = w.world_to_pixel_values(prop_ra, prop_dec)
                    print(f"  [WCS Test] Catalog (RA {cat_ra}, Dec {cat_dec}) -> Pixel: ({cat_px[0]:.2f}, {cat_px[1]:.2f})")
                    print(f"  [WCS Test] Propagated (RA {prop_ra}, Dec {prop_dec}) -> Pixel: ({prop_px[0]:.2f}, {prop_px[1]:.2f})")
                    naxis1 = hdr.get('NAXIS1', 0)
                    naxis2 = hdr.get('NAXIS2', 0)
                    in_cat = 0 <= cat_px[0] < naxis1 and 0 <= cat_px[1] < naxis2
                    in_prop = 0 <= prop_px[0] < naxis1 and 0 <= prop_px[1] < naxis2
                    print(f"  Inside boundaries? Catalog: {in_cat}, Propagated: {in_prop}")
            except Exception as e:
                print(f"  WCS parsing exception: {e}")
