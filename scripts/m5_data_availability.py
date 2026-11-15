"""Phase 0 Data Availability and Feasibility Assessment for SPHEREx Milestone 5.
Inspects IRSA SIA2 metadata, multi-epoch observations, time baselines,
detector IDs, spectral wavelength coverage, and feasibility for difference imaging.
"""

import os
import json
import numpy as np
from astropy.io.votable import parse_single_table
from astropy.io import fits

def inspect_votable(xml_path: str):
    print(f"=== Inspecting VOTable: {xml_path} ===")
    t = parse_single_table(xml_path)
    arr = t.array
    print(f"Total records: {len(arr)}")
    
    records = []
    for r in arr:
        records.append({
            "obs_id": str(r["obs_id"]),
            "t_min": float(r["t_min"]),
            "t_max": float(r["t_max"]),
            "t_exptime": float(r["t_exptime"]) if "t_exptime" in r.dtype.names else None,
            "ra": float(r["s_ra"]),
            "dec": float(r["s_dec"]),
            "band": str(r["energy_bandpassname"]),
            "em_min": float(r["em_min"]) if "em_min" in r.dtype.names else None,
            "em_max": float(r["em_max"]) if "em_max" in r.dtype.names else None,
            "url": str(r["access_url"]),
            "s_region": str(r["s_region"]) if "s_region" in r.dtype.names else "",
        })
    return records

def analyze_multi_epoch_pairs(records):
    # Group by band/detector
    by_band = {}
    for r in records:
        by_band.setdefault(r["band"], []).append(r)
    
    print("\n--- Summary by Detector / Bandpass ---")
    pair_candidates = []
    for band, obs_list in sorted(by_band.items()):
        obs_list.sort(key=lambda x: x["t_min"])
        n_obs = len(obs_list)
        time_span = obs_list[-1]["t_min"] - obs_list[0]["t_min"]
        print(f"Detector {band}: {n_obs} observations, Time baseline = {time_span:.3f} days ({time_span*24:.1f} hours)")
        
        # Look for pairs with high spatial overlap
        for i in range(n_obs):
            for j in range(i + 1, n_obs):
                o1 = obs_list[i]
                o2 = obs_list[j]
                dt_days = o2["t_min"] - o1["t_min"]
                # Great circle distance between centers
                d_ra = np.radians(o2["ra"] - o1["ra"]) * np.cos(np.radians(0.5 * (o1["dec"] + o2["dec"])))
                d_dec = np.radians(o2["dec"] - o1["dec"])
                dist_deg = np.degrees(np.hypot(d_ra, d_dec))
                
                # If centers are within 0.5 degrees (SPHEREx FOV is ~3.5 x 11 deg total, each detector ~3.5 x 3.5 deg)
                if dist_deg < 0.8:
                    pair_candidates.append({
                        "band": band,
                        "dt_days": dt_days,
                        "dist_deg": dist_deg,
                        "obs1": o1["obs_id"],
                        "obs2": o2["obs_id"],
                        "t1_mjd": o1["t_min"],
                        "t2_mjd": o2["t_min"],
                        "ra1": o1["ra"],
                        "dec1": o1["dec"],
                        "ra2": o2["ra"],
                        "dec2": o2["dec"],
                        "url1": o1["url"],
                        "url2": o2["url"],
                    })

    print(f"\nTotal overlapping multi-epoch candidate pairs found: {len(pair_candidates)}")
    # Sort pairs by separation distance and time difference
    pair_candidates.sort(key=lambda x: (x["dist_deg"], -x["dt_days"]))
    print("\nTop candidate multi-epoch observation pairs for difference imaging:")
    for idx, p in enumerate(pair_candidates[:10]):
        print(f"Pair {idx+1}: Band={p['band']}, Sep={p['dist_deg']:.4f} deg, Delta_t={p['dt_days']:.3f} days ({p['dt_days']*24:.1f} h)")
        print(f"   Obs1: {p['obs1']} (MJD {p['t1_mjd']:.4f}, RA={p['ra1']:.3f}, Dec={p['dec1']:.3f})")
        print(f"   Obs2: {p['obs2']} (MJD {p['t2_mjd']:.4f}, RA={p['ra2']:.3f}, Dec={p['dec2']:.3f})")
        print(f"   URL1: {p['url1']}")
        print(f"   URL2: {p['url2']}")
    
    return pair_candidates

def inspect_downloaded_fits():
    fits_path = "data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits"
    if not os.path.exists(fits_path):
        print("Downloaded FITS does not exist:", fits_path)
        return
    print("\n=== Inspecting Downloaded Real FITS Product ===")
    print("Path:", fits_path)
    with fits.open(fits_path) as hdul:
        print("HDU list:")
        for idx, h in enumerate(hdul):
            name = h.name
            shape = getattr(h, "shape", None)
            dtype = getattr(h, "data", None)
            dt_str = str(dtype.dtype) if dtype is not None else "None"
            print(f"  HDU {idx}: {name} (shape={shape}, dtype={dt_str})")
        
        # Check WCS-WAVE
        if "WCS-WAVE" in hdul:
            wave_hdu = hdul["WCS-WAVE"]
            print("WCS-WAVE header keys:", [k for k in wave_hdu.header.keys() if "CRPIX" in k or "CRVAL" in k or "CDELT" in k or "CTYPE" in k])
            if hasattr(wave_hdu, "columns"):
                print("WCS-WAVE columns:", wave_hdu.columns.names)
                data = wave_hdu.data
                print(f"WCS-WAVE rows: {len(data)}, sample values: {data['VALUES'][:5]}")
        
        # Check PRIMARY header
        p_hdr = hdul[0].header
        print("Target/Survey metadata:")
        print("  TELESCOP:", p_hdr.get("TELESCOP"))
        print("  INSTRUME:", p_hdr.get("INSTRUME"))
        print("  DETECTOR:", p_hdr.get("DETECTOR"))
        print("  OBS_ID:", p_hdr.get("OBS_ID"))
        print("  DATE-OBS:", p_hdr.get("DATE-OBS"))
        print("  MJD-OBS:", p_hdr.get("MJD-OBS"))
        print("  WAVELMIN:", p_hdr.get("WAVELMIN"), "WAVELMAX:", p_hdr.get("WAVELMAX"))

if __name__ == "__main__":
    records = inspect_votable("evidence/m4/empty_region_equatorial_void_spherex_qr3.xml")
    pairs = analyze_multi_epoch_pairs(records)
    inspect_downloaded_fits()
