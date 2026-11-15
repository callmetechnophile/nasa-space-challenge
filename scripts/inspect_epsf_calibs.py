from astropy.io import fits
import numpy as np

for d in range(1, 7):
    fn = f'data/spherex/calibrations/epsf_D{d}_spx_cal-epsf-v1-2026-191.fits' if d != 3 else 'data/spherex/calibrations/epsf_D3_spx_cal-epsf-v2-2026-191.fits'
    with fits.open(fn) as h:
        hdr1 = h[1].header
        k = h[1].data['EPSF'][0]
        ovx = hdr1.get("OVSMPX")
        ovy = hdr1.get("OVSMPY")
        knat = hdr1.get("KEEPNAT")
        kpos = hdr1.get("KEEPOS")
        print(f"D{d}: shape={k.shape}, OVSMPX={ovx}, OVSMPY={ovy}, KEEPNAT={knat}, KEEPOS={kpos}, sum={np.sum(k):.6f}, max={np.max(k):.6f}, argmax={np.unravel_index(np.argmax(k), k.shape)}")
