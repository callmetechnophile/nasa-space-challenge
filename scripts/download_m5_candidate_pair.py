"""Download and inspect candidate multi-epoch FITS pair for M5 Phase 0 Feasibility Audit."""
import os
import sys
import json
import asyncio
import hashlib
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.abspath("backend"))

from app.models.spherex_observation import SpherexDownloadRequest
from app.services.spherex_download import download_spherex_fits

CANDIDATES = [
    {
        "obs_id": "2026W31_2A_0034_3",
        "access_url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W31_2A/l2b-v27-2026-224/1/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
        "target": "Equatorial Corridor (Epoch 1)",
    },
    {
        "obs_id": "2026W32_2A_0338_1",
        "access_url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W32_2A/l2b-v27-2026-223/1/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits",
        "target": "Equatorial Corridor (Epoch 2)",
    }
]

async def run_downloads():
    results = []
    print("=== Downloading Candidate SPHEREx Multi-Epoch Products ===")
    for cand in CANDIDATES:
        req = SpherexDownloadRequest(
            obs_id=cand["obs_id"],
            access_url=cand["access_url"],
            collection="spherex_qr3"
        )
        print(f"\nRequesting: {cand['obs_id']}")
        print(f"URL: {cand['access_url']}")
        res = await download_spherex_fits(req, timeout_sec=240.0)
        print(f"Downloaded: {res.filename} | Size: {res.file_size_bytes} B ({res.file_size_mb} MB) | Already Cached: {res.already_existed}")
        print(f"SHA-256: {res.sha256}")
        
        # Now inspect HDUs
        hdu_info = []
        with fits.open(res.file_path) as hdul:
            for idx, hdu in enumerate(hdul):
                hdu_info.append({
                    "index": idx,
                    "name": hdu.name,
                    "type": type(hdu).__name__,
                    "shape": list(hdu.data.shape) if hdu.data is not None else None,
                    "dtype": str(hdu.data.dtype) if hdu.data is not None else None,
                })
            
            pri_hdr = dict(hdul[0].header)
            img_hdr = dict(hdul["IMAGE"].header) if "IMAGE" in hdul else {}
            
            # WCS inspection
            wcs_params = {
                "crval1": float(img_hdr.get("CRVAL1", np.nan)),
                "crval2": float(img_hdr.get("CRVAL2", np.nan)),
                "crpix1": float(img_hdr.get("CRPIX1", np.nan)),
                "crpix2": float(img_hdr.get("CRPIX2", np.nan)),
                "cdelt1": float(img_hdr.get("CDELT1", np.nan)),
                "cdelt2": float(img_hdr.get("CDELT2", np.nan)),
                "ctype1": str(img_hdr.get("CTYPE1")),
                "ctype2": str(img_hdr.get("CTYPE2")),
            }
            
            time_params = {
                "date_obs": str(pri_hdr.get("DATE-OBS") or img_hdr.get("DATE-OBS")),
                "mjd_obs": float(pri_hdr.get("MJD-OBS") or img_hdr.get("MJD-OBS") or np.nan),
                "tel_time": float(pri_hdr.get("TEL_TIME") or img_hdr.get("TEL_TIME") or np.nan),
                "exptime": float(pri_hdr.get("EXPTIME") or img_hdr.get("EXPTIME") or np.nan),
                "date_file": str(pri_hdr.get("DATE")),
                "telescop": str(pri_hdr.get("TELESCOP")),
                "detector": str(pri_hdr.get("DETECTOR") or pri_hdr.get("DETNAME")),
                "version": str(pri_hdr.get("VERSION") or pri_hdr.get("PIPEVER")),
            }

        results.append({
            "target": cand["target"],
            "obs_id": cand["obs_id"],
            "filename": res.filename,
            "file_path": res.file_path,
            "file_size_bytes": res.file_size_bytes,
            "sha256": res.sha256,
            "hdus": hdu_info,
            "wcs": wcs_params,
            "time_metadata": time_params,
        })
        
    # Compute relative metrics between the pair
    p1 = results[0]
    p2 = results[1]
    dra = (p2["wcs"]["crval1"] - p1["wcs"]["crval1"]) * np.cos(np.radians(0.5 * (p1["wcs"]["crval2"] + p2["wcs"]["crval2"])))
    ddec = p2["wcs"]["crval2"] - p1["wcs"]["crval2"]
    sep_deg = float(np.hypot(dra, ddec))
    sep_arcsec = sep_deg * 3600.0
    dt_days = float(p2["time_metadata"]["mjd_obs"] - p1["time_metadata"]["mjd_obs"])
    
    pair_summary = {
        "pair_target": "Equatorial Corridor",
        "product_1": p1["filename"],
        "product_2": p2["filename"],
        "pointing_separation_arcsec": round(sep_arcsec, 3),
        "pointing_separation_pixels": round(sep_arcsec / 6.2, 3),
        "time_baseline_days": round(dt_days, 4),
        "time_baseline_hours": round(dt_days * 24.0, 2),
        "products": results
    }
    
    out_path = os.path.abspath("evidence/m5/download_verification.json")
    with open(out_path, "w") as f:
        json.dump(pair_summary, f, indent=2)
    print(f"\nSaved download verification to: {out_path}")
    print(f"\nPair Summary:")
    print(f"  Pointing separation: {sep_arcsec:.2f} arcsec ({sep_arcsec/6.2:.2f} pixels)")
    print(f"  Temporal baseline: {dt_days:.4f} days ({dt_days*24.0:.2f} hours)")
    print(f"  Product 1 SHA-256: {p1['sha256']}")
    print(f"  Product 2 SHA-256: {p2['sha256']}")

if __name__ == "__main__":
    asyncio.run(run_downloads())
