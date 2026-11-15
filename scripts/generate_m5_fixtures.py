"""Generates deterministic controlled multi-epoch SPHEREx FITS fixtures for Milestone 5 validation.
Creates Epoch 1 and Epoch 2 with known astrophysical transients, static stars,
WCS dither, calibrated variance, bad pixels, and WCS-WAVE extensions.
"""

import os
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/spherex/fixtures_m5"))


def create_spherical_wcs(ra_center=45.0, dec_center=0.0, npix=512, pixel_scale_deg=0.0017222):
    w = WCS(naxis=2)
    w.wcs.crpix = [npix / 2.0 + 0.5, npix / 2.0 + 0.5]
    w.wcs.cdelt = [-pixel_scale_deg, pixel_scale_deg]
    w.wcs.crval = [ra_center, dec_center]
    w.wcs.ctype = ["RA---TAN-SIP", "DEC--TAN-SIP"]
    return w


def build_wcs_wave_hdu():
    x_grid = np.linspace(1, 512, 9, dtype=np.int32)
    y_grid = np.linspace(1, 512, 9, dtype=np.int32)
    # Detector 1: 0.75 - 1.12 microns
    values = np.zeros((9, 9, 2), dtype=np.float32)
    for i, y in enumerate(y_grid):
        lam = 0.75 + (512.0 - y) / 511.0 * (1.12 - 0.75)
        dlam = lam / 40.0
        for j in range(9):
            values[i, j, 0] = lam
            values[i, j, 1] = dlam

    col1 = fits.Column(name="X", format="9J", array=np.array([x_grid]))
    col2 = fits.Column(name="Y", format="9J", array=np.array([y_grid]))
    col3 = fits.Column(name="VALUES", format="162E", dim="(9,9,2)", array=np.array([values]))
    return fits.BinTableHDU.from_columns([col1, col2, col3], name="WCS-WAVE")


def generate_m5_fixtures():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    npix = 512
    rng = np.random.RandomState(42)

    # Common background (zodiacal light + thermal background ~ 2.5 MJy/sr)
    zodi = np.full((npix, npix), 2.5, dtype=np.float32)
    variance_nominal = np.full((npix, npix), 0.25, dtype=np.float32)  # sigma ~ 0.5 MJy/sr

    # Generate 20 static stars
    star_x = rng.uniform(40, npix - 40, size=20)
    star_y = rng.uniform(40, npix - 40, size=20)
    star_flux = rng.uniform(5.0, 30.0, size=20)

    y_grid, x_grid = np.mgrid[0:npix, 0:npix]
    stars_layer = np.zeros((npix, npix), dtype=np.float32)
    sigma_psf = 1.8  # FWHM ~ 4.2 pixels
    for sx, sy, sf in zip(star_x, star_y, star_flux):
        r2 = (x_grid - sx) ** 2 + (y_grid - sy) ** 2
        stars_layer += (sf / (2 * np.pi * sigma_psf ** 2)) * np.exp(-0.5 * r2 / sigma_psf ** 2)

    # --- EPOCH 1 ---
    # Epoch 1 image = zodi + static stars + noise
    noise1 = rng.normal(0, np.sqrt(variance_nominal)).astype(np.float32)
    img1 = zodi + stars_layer + noise1
    var1 = np.copy(variance_nominal)
    flags1 = np.zeros((npix, npix), dtype=np.int32)

    # Injected transient in Epoch 1 (which fades in Epoch 2): Star at (150, 150)
    fade_x, fade_y = 150.0, 150.0
    r2_fade = (x_grid - fade_x) ** 2 + (y_grid - fade_y) ** 2
    fading_star = 12.0 * np.exp(-0.5 * r2_fade / sigma_psf ** 2)
    img1 += fading_star

    # Add 1 cosmic ray hit in Epoch 1 at (300, 300) with bit 4 (16) flagged
    cr_x, cr_y = 300, 300
    img1[cr_y, cr_x] += 100.0
    flags1[cr_y, cr_x] |= 16  # FLAG_COSMIC_RAY

    wcs1 = create_spherical_wcs(ra_center=45.0, dec_center=0.0, npix=npix)

    # Build Epoch 1 MEF
    h0_1 = fits.PrimaryHDU()
    h1_1 = fits.ImageHDU(data=img1, header=wcs1.to_header(), name="IMAGE")
    h1_1.header["BUNIT"] = "MJy/sr"
    h1_1.header["DETECTOR"] = 1
    h1_1.header["OBSID"] = "M5_SYNTH_EPOCH1"
    h1_1.header["MJD-OBS"] = 61250.0
    h1_1.header["DATE-OBS"] = "2026-07-20T00:00:00"
    h1_1.header["CTYPE1W"] = "WAVE-TAB"
    h1_1.header["CTYPE2W"] = "WAVE-TAB"

    h2_1 = fits.ImageHDU(data=flags1, name="FLAGS")
    h3_1 = fits.ImageHDU(data=var1, name="VARIANCE")
    h4_1 = fits.ImageHDU(data=zodi, name="ZODI")
    h5_1 = fits.ImageHDU(data=np.ones((5, 21, 21), dtype=np.float32), name="PSF")
    h6_1 = build_wcs_wave_hdu()

    hdul1 = fits.HDUList([h0_1, h1_1, h2_1, h3_1, h4_1, h5_1, h6_1])
    epoch1_path = os.path.join(OUTPUT_DIR, "m5_synthetic_epoch1.fits")
    hdul1.writeto(epoch1_path, overwrite=True)

    # --- EPOCH 2 ---
    # Epoch 2 has slight pointing dither (+0.0003 deg ~ 1 arcsec)
    wcs2 = create_spherical_wcs(ra_center=45.0003, dec_center=0.0002, npix=npix)
    noise2 = rng.normal(0, np.sqrt(variance_nominal)).astype(np.float32)
    img2 = zodi + stars_layer + noise2
    var2 = np.copy(variance_nominal)
    flags2 = np.zeros((npix, npix), dtype=np.int32)

    # Injected new brightening transient: Star at (350, 350)
    bright_x, bright_y = 350.0, 350.0
    r2_bright = (x_grid - bright_x) ** 2 + (y_grid - bright_y) ** 2
    brightening_star = 15.0 * np.exp(-0.5 * r2_bright / sigma_psf ** 2)
    img2 += brightening_star

    # Notice fading star is absent in Epoch 2 (it faded!)
    # And add 1 dead pixel in Epoch 2 at (100, 100) flagged bit 2 (4)
    flags2[100, 100] |= 4
    img2[100, 100] = 0.0

    h0_2 = fits.PrimaryHDU()
    h1_2 = fits.ImageHDU(data=img2, header=wcs2.to_header(), name="IMAGE")
    h1_2.header["BUNIT"] = "MJy/sr"
    h1_2.header["DETECTOR"] = 1
    h1_2.header["OBSID"] = "M5_SYNTH_EPOCH2"
    h1_2.header["MJD-OBS"] = 61280.0  # 30 days later
    h1_2.header["DATE-OBS"] = "2026-08-19T00:00:00"
    h1_2.header["CTYPE1W"] = "WAVE-TAB"
    h1_2.header["CTYPE2W"] = "WAVE-TAB"

    h2_2 = fits.ImageHDU(data=flags2, name="FLAGS")
    h3_2 = fits.ImageHDU(data=var2, name="VARIANCE")
    h4_2 = fits.ImageHDU(data=zodi, name="ZODI")
    h5_2 = fits.ImageHDU(data=np.ones((5, 21, 21), dtype=np.float32), name="PSF")
    h6_2 = build_wcs_wave_hdu()

    hdul2 = fits.HDUList([h0_2, h1_2, h2_2, h3_2, h4_2, h5_2, h6_2])
    epoch2_path = os.path.join(OUTPUT_DIR, "m5_synthetic_epoch2.fits")
    hdul2.writeto(epoch2_path, overwrite=True)

    print("Generated M5 synthetic test fixtures:")
    print("  Epoch 1:", epoch1_path, f"({os.path.getsize(epoch1_path)} bytes)")
    print("  Epoch 2:", epoch2_path, f"({os.path.getsize(epoch2_path)} bytes)")


if __name__ == "__main__":
    generate_m5_fixtures()
