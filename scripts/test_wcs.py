from astropy.io import fits
from astropy.wcs import WCS

with fits.open('data/spherex/fixtures_m5/m5_synthetic_epoch1.fits') as hdul:
    h = hdul[1].header.copy()
    for k in list(h.keys()):
        if k.endswith('W') and len(k) > 1 and k[:-1] in ['CTYPE1', 'CTYPE2', 'CRVAL1', 'CRVAL2', 'CRPIX1', 'CRPIX2']:
            del h[k]
    w = WCS(h, naxis=2)
    print('Clean WCS success:', w)
