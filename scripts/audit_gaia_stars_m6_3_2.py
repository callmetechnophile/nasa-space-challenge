import os
import sys
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.ndimage import label, center_of_mass

sys.path.insert(0, 'backend')
from app.astronomy.gaia_astrometry import BENCHMARK_GAIA_DR3_STARS, propagate_gaia_source

fp = 'data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits'
with fits.open(fp) as hdul:
    img = hdul['IMAGE'].data
    var = hdul['VARIANCE'].data
    flg = hdul['FLAGS'].data
    im_hdr = hdul['IMAGE'].header
    w = WCS(im_hdr)
    date_obs = im_hdr['DATE-OBS']
    
    # Estimate local background in the central 200x200 region around stars
    # Central pixel coordinates are near (1020, 1020)
    bg_sub = img[900:1150, 900:1150]
    bg_val = float(np.nanmedian(bg_sub))
    bg_rms = float(np.nanstd(bg_sub))
    print(f"Background in central region: median={bg_val:.4f}, rms={bg_rms:.4f}")

    results = []
    
    for s in BENCHMARK_GAIA_DR3_STARS:
        sid = s['source_id']
        p_ra, p_dec, disp = propagate_gaia_source(s, target_obstime_str=date_obs)
        
        # Predicted detector coordinates (0-based for numpy indexing, 1-based for FITS)
        px1_pred, py1_pred = w.all_world2pix(p_ra, p_dec, 1)
        px0_pred, py0_pred = px1_pred - 1.0, py1_pred - 1.0
        
        # Search radius = 3 pixels (~18.6 arcsec) around predicted position
        r = 3
        ix = int(round(px0_pred))
        iy = int(round(py0_pred))
        
        y0, y1 = max(0, iy - r), min(2040, iy + r + 1)
        x0, x1 = max(0, ix - r), min(2040, ix + r + 1)
        
        cutout = img[y0:y1, x0:x1] - bg_val
        cutout_var = var[y0:y1, x0:x1]
        cutout_flg = flg[y0:y1, x0:x1]
        
        # Local peak
        local_max = np.max(cutout)
        local_max_idx = np.unravel_index(np.argmax(cutout), cutout.shape)
        peak_y0 = y0 + local_max_idx[0]
        peak_x0 = x0 + local_max_idx[1]
        local_sigma = np.sqrt(cutout_var[local_max_idx]) if cutout_var[local_max_idx] > 0 else bg_rms
        peak_snr = local_max / local_sigma
        
        # Production flux-weighted centroiding in 3x3 around peak
        cy0, cy1 = max(0, peak_y0 - 1), min(2040, peak_y0 + 2)
        cx0, cx1 = max(0, peak_x0 - 1), min(2040, peak_x0 + 2)
        c_patch = np.maximum(0.0, img[cy0:cy1, cx0:cx1] - bg_val)
        
        if np.sum(c_patch) > 0:
            y_coords, x_coords = np.mgrid[cy0:cy1, cx0:cx1]
            meas_y0 = float(np.sum(y_coords * c_patch) / np.sum(c_patch))
            meas_x0 = float(np.sum(x_coords * c_patch) / np.sum(c_patch))
        else:
            meas_y0 = float(peak_y0)
            meas_x0 = float(peak_x0)
            
        meas_x1 = meas_x0 + 1.0
        meas_y1 = meas_y0 + 1.0
        
        # Convert measured pixel to celestial sky coordinate via production WCS
        meas_sky = w.all_pix2world([[meas_x1, meas_y1]], 1)[0]
        meas_ra = float(meas_sky[0])
        meas_dec = float(meas_sky[1])
        
        # Compute astrometric residuals
        c_gaia = SkyCoord(ra=p_ra * u.deg, dec=p_dec * u.deg, frame="icrs")
        c_spx = SkyCoord(ra=meas_ra * u.deg, dec=meas_dec * u.deg, frame="icrs")
        
        sep_arcsec = float(c_gaia.separation(c_spx).arcsec)
        cos_dec = np.cos(np.radians(p_dec))
        dra_cosdec_arcsec = (meas_ra - p_ra) * 3600.0 * cos_dec
        ddec_arcsec = (meas_dec - p_dec) * 3600.0
        
        # Check match quality
        # SPHEREx pixel is 6.2 arcsec. If separation > 3 pixels (~18.6 arcsec), likely confused/blended/unmatched
        pixel_dist = np.hypot(meas_x1 - px1_pred, meas_y1 - py1_pred)
        if peak_snr < 3.5:
            match_quality = "NON_DETECTION"
        elif pixel_dist > 2.5:
            match_quality = "CONFUSED_OR_BLENDED"
        else:
            match_quality = "RELIABLE_MATCH"
            
        results.append({
            "source_id": sid,
            "ref_ra": s['ra_deg'],
            "ref_dec": s['dec_deg'],
            "ref_epoch": "J2016.0",
            "pmra": s.get('pmra_mas_yr'),
            "pmdec": s.get('pmdec_mas_yr'),
            "parallax": s.get('parallax_mas'),
            "radial_velocity": s.get('radial_velocity_km_s'),
            "g_mag": s.get('phot_g_mean_mag'),
            "prop_ra": p_ra,
            "prop_dec": p_dec,
            "pred_pix": (px1_pred, py1_pred),
            "meas_pix": (meas_x1, meas_y1),
            "pixel_dist": pixel_dist,
            "meas_ra": meas_ra,
            "meas_dec": meas_dec,
            "dra_cosdec": dra_cosdec_arcsec,
            "ddec": ddec_arcsec,
            "separation": sep_arcsec,
            "peak_snr": peak_snr,
            "match_quality": match_quality,
        })

print("\n================== GAIA BENCHMARK DETAILED AUDIT RESULTS ==================")
for r in results:
    print(f"\nGaia Source: {r['source_id']} (G = {r['g_mag']} mag)")
    print(f"  Gaia Ref (J2016.0): ({r['ref_ra']:.6f}, {r['ref_dec']:.6f})")
    print(f"  Astrometry: PM=({r['pmra']}, {r['pmdec']}) mas/yr, Plx={r['parallax']} mas, RV={r['radial_velocity']}")
    print(f"  Propagated at DATE-OBS: ({r['prop_ra']:.6f}, {r['prop_dec']:.6f})")
    print(f"  Predicted Pixel (1-based): ({r['pred_pix'][0]:.2f}, {r['pred_pix'][1]:.2f})")
    print(f"  Measured Pixel (1-based):  ({r['meas_pix'][0]:.2f}, {r['meas_pix'][1]:.2f}) -> delta_pix = {r['pixel_dist']:.2f} px")
    print(f"  Measured WCS Sky Position: ({r['meas_ra']:.6f}, {r['meas_dec']:.6f})")
    print(f"  Residuals: dra*cos(dec) = {r['dra_cosdec']:+.3f}\", ddec = {r['ddec']:+.3f}\", separation = {r['separation']:.3f}\"")
    print(f"  Peak SNR: {r['peak_snr']:.2f} sigma | Quality: {r['match_quality']}")

# Overall statistics
reliable = [r for r in results if r['match_quality'] == 'RELIABLE_MATCH']
print(f"\nReliable matches: {len(reliable)} / {len(results)}")
if len(reliable) >= 3:
    seps = [r['separation'] for r in reliable]
    rms = np.sqrt(np.mean(np.array(seps)**2))
    med = np.median(seps)
    mad = np.median(np.abs(seps - med))
    nmad = 1.4826 * mad
    print(f"Statistics on reliable matches: Median={med:.3f}\", RMS={rms:.3f}\", NMAD={nmad:.3f}\"")
else:
    print("Insufficient reliable matches for statistical modeling.")
