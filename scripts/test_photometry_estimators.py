import numpy as np

def test_photometry_estimators():
    # 7x7 native PSF from D1 zone 220
    # Let's create an authentic native PSF
    from astropy.io import fits
    with fits.open('data/spherex/calibrations/epsf_D1_spx_cal-epsf-v1-2026-191.fits') as h:
        k = np.array(h[1].data['EPSF'][220], dtype=np.float64)
    
    slices = [slice(0, 4), slice(4, 9), slice(9, 14), slice(14, 19), slice(19, 24), slice(24, 29), slice(29, 33)]
    P = np.zeros((7, 7), dtype=np.float64)
    for iy, sy in enumerate(slices):
        for ix, sx in enumerate(slices):
            P[iy, ix] = np.sum(k[sy, sx])
    P /= np.sum(P) # exactly 1.000000
    
    sigma_diff = 1.0 # unit noise
    V = np.ones((7, 7)) * (sigma_diff**2)
    
    mf_denom = np.sqrt(np.sum(P**2 / V))
    
    for snr in [3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 50.0]:
        F_true = snr / mf_denom
        # Simulate difference cutout with noise
        rng = np.random.default_rng(42)
        n_trials = 100
        biases_psf = []
        biases_aper = []
        biases_iso = []
        
        for _ in range(n_trials):
            noise = rng.normal(0, sigma_diff, (7, 7))
            D = F_true * P + noise
            S = D / sigma_diff
            
            # 1. Optimal PSF-fitting flux estimator
            # F_hat = sum(D * P / V) / sum(P^2 / V)
            F_psf = np.sum(D * P / V) / np.sum(P**2 / V)
            biases_psf.append((F_psf - F_true) / F_true)
            
            # 2. 7x7 box aperture flux
            F_aper = np.sum(D)
            biases_aper.append((F_aper - F_true) / F_true)
            
            # 3. Connected-component / isophotal flux (pixels with S >= 3.5)
            mask_35 = (S >= 3.5)
            F_iso = np.sum(D[mask_35]) if np.any(mask_35) else 0.0
            biases_iso.append((F_iso - F_true) / F_true)
            
        print(f"SNR={snr:4.1f} | F_true={F_true:6.2f} | "
              f"PSF-fit bias: {np.mean(biases_psf)*100:+5.2f}% (std {np.std(biases_psf)*100:4.1f}%) | "
              f"Aper bias: {np.mean(biases_aper)*100:+5.2f}% (std {np.std(biases_aper)*100:4.1f}%) | "
              f"Isophotal bias: {np.mean(biases_iso)*100:+5.2f}%")

test_photometry_estimators()
