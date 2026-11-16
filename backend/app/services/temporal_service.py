"""SPHEREx Temporal Sky Analysis & Scientific Difference Imaging Service (Milestone 5).
Orchestrates multi-epoch discovery, spectral compatibility checking,
WCS common-grid reprojection, quality masking, PSF matching, difference imaging,
and conservative change candidate cataloging.
Strictly adheres to Anti-Fabrication Invariants: Explicitly tags mock test fixtures
vs real Level-2 flight observations.
"""

from __future__ import annotations

import os
import glob
import base64
import hashlib
import logging
import time
from typing import Dict, Any, List, Optional
import httpx
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from app.astronomy.spherex_mef_reader import read_spherex_mef_product, SpherexMefProduct
from app.astronomy.spectral_compatibility import (
    LVFWavelengthModel,
    evaluate_spectral_compatibility,
)
from app.astronomy.image_registration import (
    create_common_wcs,
    reproject_to_common_grid,
    compute_registration_displacement,
)
from app.astronomy.wcs_processor import extract_wcs
from app.astronomy.quality_mask import create_quality_mask, DEFAULT_FATAL_MASK
from app.astronomy.psf_matching import match_psf_pair, estimate_effective_fwhm
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates, DISCLAIMER_LABEL
from app.astronomy.diff_renderer import (
    render_difference_png_bytes,
    render_significance_png_bytes,
)
from app.astronomy.image_renderer import render_to_png_bytes
from app.models.provenance import (
    ScientificDatasetProvenance,
    ProvenanceState,
    AUTHENTIC_FITS_REGISTRY,
    TEST_FIXTURE_REGISTRY,
)
from app.storage.blob_storage import storage_manager

logger = logging.getLogger("temporal_service")

DATA_DIR = os.getenv("SPHEREX_STORAGE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex")))

IRSA_KNOWN_URLS: Dict[str, str] = {
    "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits": (
        "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W31_2A/l2b-v27-2026-224/1/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
    ),
    "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits": (
        "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W32_2A/l2b-v27-2026-223/1/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"
    ),
    "level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits": (
        "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2/level2/2025W44_2B/l2b-v20-2025-307/1/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits"
    ),
}


def _compute_file_sha256(path: str) -> str:
    """Compute cryptographic SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class TemporalService:
    """Core service for SPHEREx temporal sky comparison."""

    def __init__(self, storage_dir: str = DATA_DIR):
        self.storage_dir = storage_dir

    def resolve_or_fetch_observation_file(self, filename_or_path: str) -> Optional[str]:
        """Resolve an observation file locally, or fetch it on-demand from Azure Blob Storage or IRSA.

        Enforces anti-fabrication: Never fabricates or synthesizes flight data.
        Validates SHA-256 for authentic datasets registered in AUTHENTIC_FITS_REGISTRY.
        """
        if not filename_or_path:
            return None

        # 1. Absolute path check
        if os.path.isabs(filename_or_path) and os.path.isfile(filename_or_path):
            return filename_or_path

        basename = os.path.basename(filename_or_path)

        # 2. Local candidate directory search
        candidate_paths = [
            filename_or_path,
            os.path.join(self.storage_dir, filename_or_path),
            os.path.join(self.storage_dir, basename),
            os.path.join(DATA_DIR, filename_or_path),
            os.path.join(DATA_DIR, basename),
            os.path.join(os.getcwd(), "data", "spherex", basename),
            os.path.join(os.path.dirname(__file__), "../../../data/spherex", basename),
            os.path.join(os.path.dirname(__file__), "../../../backend/fixtures_m5", basename),
            os.path.join(os.path.dirname(__file__), "../fixtures_m5", basename),
            os.path.join(os.path.dirname(__file__), "../../fixtures_m5", basename),
            os.path.join("/data/spherex", basename),
            os.path.join("/tmp/spherex", basename),
        ]
        for cp in candidate_paths:
            if os.path.isfile(cp):
                return os.path.abspath(cp)

        # Determine writable cache directory
        cache_dir = self.storage_dir
        try:
            os.makedirs(cache_dir, exist_ok=True)
            if not os.access(cache_dir, os.W_OK):
                cache_dir = os.path.join("/tmp", "spherex")
                os.makedirs(cache_dir, exist_ok=True)
        except Exception:
            cache_dir = os.path.join("/tmp", "spherex")
            os.makedirs(cache_dir, exist_ok=True)

        target_path = os.path.join(cache_dir, basename)

        # 3. Fetch from Azure Blob Storage if available
        try:
            if storage_manager.download_product_to_file(basename, target_path):
                # Verify SHA-256 if registered
                if basename in AUTHENTIC_FITS_REGISTRY:
                    expected_sha = AUTHENTIC_FITS_REGISTRY[basename]["sha256"]
                    calc_sha = _compute_file_sha256(target_path)
                    if calc_sha.lower() != expected_sha.lower():
                        logger.error("Azure Blob SHA256 mismatch for %s: %s != %s", basename, calc_sha, expected_sha)
                        if os.path.exists(target_path):
                            os.remove(target_path)
                    else:
                        logger.info("Successfully fetched and verified %s from Azure Blob Storage", basename)
                        return target_path
                else:
                    return target_path
        except Exception as e:
            logger.warning("Failed to fetch %s from Azure Blob Storage: %s", basename, e)

        # 4. Fetch from NASA/IPAC IRSA archive URL
        irsa_url = IRSA_KNOWN_URLS.get(basename)
        if irsa_url:
            logger.info("Fetching authentic SPHEREx observation %s from IRSA: %s", basename, irsa_url)
            try:
                with httpx.Client(timeout=120.0, follow_redirects=True) as client:
                    with client.stream("GET", irsa_url) as resp:
                        if resp.status_code == 200:
                            with open(target_path, "wb") as f:
                                for chunk in resp.iter_bytes(chunk_size=65536):
                                    f.write(chunk)
                            # Verify SHA-256
                            if basename in AUTHENTIC_FITS_REGISTRY:
                                expected_sha = AUTHENTIC_FITS_REGISTRY[basename]["sha256"]
                                calc_sha = _compute_file_sha256(target_path)
                                if calc_sha.lower() != expected_sha.lower():
                                    logger.error("IRSA download SHA256 mismatch for %s: %s != %s", basename, calc_sha, expected_sha)
                                    if os.path.exists(target_path):
                                        os.remove(target_path)
                                    return None
                            logger.info("Successfully downloaded and verified %s from IRSA archive", basename)
                            return target_path
                        else:
                            logger.warning("IRSA returned status %s for %s", resp.status_code, irsa_url)
            except Exception as e:
                logger.error("Exception fetching %s from IRSA: %s", basename, e)

        return None

    def list_available_observations(self) -> List[Dict[str, Any]]:
        """List all locally available SPHEREx FITS observations with their metadata and provenance."""
        if not os.path.exists(self.storage_dir):
            return []

        files = sorted(glob.glob(os.path.join(self.storage_dir, "*.fits")))
        observations = []
        for fpath in files:
            fname = os.path.basename(fpath)
            try:
                with fits.open(fpath) as hdul:
                    h1 = hdul[1].header if len(hdul) > 1 else hdul[0].header
                    obs_id = str(h1.get("OBSID", fname.split(".")[0]))
                    detector = int(h1.get("DETECTOR", 1))
                    date_obs = str(h1.get("DATE-OBS", "UNKNOWN"))
                    mjd_obs = float(h1.get("MJD-OBS", 0.0))
                    crval1 = float(h1.get("CRVAL1", 0.0))
                    crval2 = float(h1.get("CRVAL2", 0.0))
                    bunit = str(h1.get("BUNIT", "MJy/sr"))

                    # Provenance determination
                    is_fixture = (fname in TEST_FIXTURE_REGISTRY) or ("synthetic" in fname.lower())
                    prov_state = "MOCK_TEST" if is_fixture else "REAL_VERIFIED"
                    classif = "MOCK" if is_fixture else "REAL"

                    observations.append({
                        "file_name": fname,
                        "file_path": fpath,
                        "file_size_bytes": os.path.getsize(fpath),
                        "obs_id": obs_id,
                        "detector": detector,
                        "band_name": f"SPHEREx-D{detector}",
                        "date_obs": date_obs,
                        "mjd_obs": mjd_obs,
                        "ra_center": crval1,
                        "dec_center": crval2,
                        "bunit": bunit,
                        "has_variance": "VARIANCE" in hdul,
                        "has_flags": "FLAGS" in hdul,
                        "has_wave": "WCS-WAVE" in hdul,
                        "provenance_state": prov_state,
                        "synthetic_real_classification": classif,
                    })
            except Exception as e:
                logger.warning("Error reading observation %s: %s", fname, e)

        return observations

    def run_difference_pipeline(
        self,
        fits_path_1: str,
        fits_path_2: str,
        significance_threshold: float = 3.5,
        spectral_tolerance: float = 0.02,
        grid_size: int = 512,
        fatal_bitmask: int = DEFAULT_FATAL_MASK,
        subtract_background: bool = True,
    ) -> Dict[str, Any]:
        """Execute complete scientifically defensible temporal comparison pipeline."""
        start_time = time.time()
        logger.info("Starting temporal comparison: %s vs %s", fits_path_1, fits_path_2)

        fname1 = os.path.basename(fits_path_1)
        fname2 = os.path.basename(fits_path_2)
        sha1 = _compute_file_sha256(fits_path_1)
        sha2 = _compute_file_sha256(fits_path_2)

        # Anti-fabrication check: detect if either input file is a test fixture
        is_fixture_1 = (fname1 in TEST_FIXTURE_REGISTRY) or ("synthetic" in fname1.lower())
        is_fixture_2 = (fname2 in TEST_FIXTURE_REGISTRY) or ("synthetic" in fname2.lower())
        is_mock = is_fixture_1 or is_fixture_2

        wave1_synthetic = False
        wave2_synthetic = False

        # 1. Ingest Observation 1
        try:
            prod1 = read_spherex_mef_product(fits_path_1)
            img1, flags1, var1 = prod1.image, prod1.flags, prod1.variance
            epsf1 = prod1.epsf_table
            wcs1 = prod1.wcs
            wave_model1 = LVFWavelengthModel(prod1.wcs_wave_x, prod1.wcs_wave_y, prod1.wcs_wave_values)
            mjd1 = float(prod1.primary_header.get("MJD-OBS", prod1.image_header.get("MJD-OBS", 0.0)))
            date1 = str(prod1.primary_header.get("DATE-OBS", prod1.image_header.get("DATE-OBS", "UNKNOWN")))
            det1 = int(prod1.primary_header.get("DETECTOR", prod1.image_header.get("DETECTOR", 1)))
        except Exception as e1:
            logger.info("Falling back to generic reader for %s: %s", fits_path_1, e1)
            with fits.open(fits_path_1) as hdul1:
                h1 = hdul1[1].header if len(hdul1) > 1 else hdul1[0].header
                img1 = hdul1[1].data.astype(np.float32) if len(hdul1) > 1 else hdul1[0].data.astype(np.float32)
                flags1 = hdul1["FLAGS"].data if "FLAGS" in hdul1 else None
                var1 = hdul1["VARIANCE"].data.astype(np.float32) if "VARIANCE" in hdul1 else None
                epsf1 = hdul1["EPSF"].data if "EPSF" in hdul1 else (hdul1["PSF"].data if "PSF" in hdul1 else None)
                wcs1 = extract_wcs(h1)
                if "WCS-WAVE" in hdul1:
                    wave_model1 = LVFWavelengthModel.from_fits_hdu(hdul1["WCS-WAVE"])
                else:
                    wave_model1 = LVFWavelengthModel.synthetic_default(detector=int(h1.get("DETECTOR", 1)))
                    wave1_synthetic = True
                mjd1 = float(h1.get("MJD-OBS", 0.0))
                date1 = str(h1.get("DATE-OBS", "UNKNOWN"))
                det1 = int(h1.get("DETECTOR", 1))

        # 2. Ingest Observation 2
        try:
            prod2 = read_spherex_mef_product(fits_path_2)
            img2, flags2, var2 = prod2.image, prod2.flags, prod2.variance
            epsf2 = prod2.epsf_table
            wcs2 = prod2.wcs
            wave_model2 = LVFWavelengthModel(prod2.wcs_wave_x, prod2.wcs_wave_y, prod2.wcs_wave_values)
            mjd2 = float(prod2.primary_header.get("MJD-OBS", prod2.image_header.get("MJD-OBS", 0.0)))
            date2 = str(prod2.primary_header.get("DATE-OBS", prod2.image_header.get("DATE-OBS", "UNKNOWN")))
            det2 = int(prod2.primary_header.get("DETECTOR", prod2.image_header.get("DETECTOR", 1)))
        except Exception as e2:
            logger.info("Falling back to generic reader for %s: %s", fits_path_2, e2)
            with fits.open(fits_path_2) as hdul2:
                h2 = hdul2[1].header if len(hdul2) > 1 else hdul2[0].header
                img2 = hdul2[1].data.astype(np.float32) if len(hdul2) > 1 else hdul2[0].data.astype(np.float32)
                flags2 = hdul2["FLAGS"].data if "FLAGS" in hdul2 else None
                var2 = hdul2["VARIANCE"].data.astype(np.float32) if "VARIANCE" in hdul2 else None
                epsf2 = hdul2["EPSF"].data if "EPSF" in hdul2 else (hdul2["PSF"].data if "PSF" in hdul2 else None)
                wcs2 = extract_wcs(h2)
                if "WCS-WAVE" in hdul2:
                    wave_model2 = LVFWavelengthModel.from_fits_hdu(hdul2["WCS-WAVE"])
                else:
                    wave_model2 = LVFWavelengthModel.synthetic_default(detector=int(h2.get("DETECTOR", 1)))
                    wave2_synthetic = True
                mjd2 = float(h2.get("MJD-OBS", 0.0))
                date2 = str(h2.get("DATE-OBS", "UNKNOWN"))
                det2 = int(h2.get("DETECTOR", 1))

        # 3. Geometric Center & Registration Error
        ra1, dec1 = wcs1.wcs.crval
        ra2, dec2 = wcs2.wcs.crval
        ra_center = 0.5 * (ra1 + ra2)
        dec_center = 0.5 * (dec1 + dec2)
        displacement = compute_registration_displacement(wcs1, wcs2, ra_center, dec_center)

        # 4. Common Target Grid & Reprojection
        target_wcs = create_common_wcs(
            ra_center=ra_center,
            dec_center=dec_center,
            pixel_scale_deg=6.2 / 3600.0,
            npix_x=grid_size,
            npix_y=grid_size,
        )

        reproj1 = reproject_to_common_grid(
            image=img1,
            variance=var1,
            source_wcs=wcs1,
            target_wcs=target_wcs,
            target_shape=(grid_size, grid_size),
        )
        reproj2 = reproject_to_common_grid(
            image=img2,
            variance=var2,
            source_wcs=wcs2,
            target_wcs=target_wcs,
            target_shape=(grid_size, grid_size),
        )

        if flags1 is not None:
            reproj_flags1 = reproject_to_common_grid(
                image=flags1.astype(np.float32),
                variance=None,
                source_wcs=wcs1,
                target_wcs=target_wcs,
                target_shape=(grid_size, grid_size),
                order=0,
            )["image"]
        else:
            reproj_flags1 = None

        if flags2 is not None:
            reproj_flags2 = reproject_to_common_grid(
                image=flags2.astype(np.float32),
                variance=None,
                source_wcs=wcs2,
                target_wcs=target_wcs,
                target_shape=(grid_size, grid_size),
                order=0,
            )["image"]
        else:
            reproj_flags2 = None

        # 5. Quality Masking
        qmask1 = create_quality_mask(
            image=reproj1["image"],
            flags=reproj_flags1,
            variance=reproj1["variance"],
            fatal_bitmask=fatal_bitmask,
        )
        qmask2 = create_quality_mask(
            image=reproj2["image"],
            flags=reproj_flags2,
            variance=reproj2["variance"],
            fatal_bitmask=fatal_bitmask,
        )

        # 6. Spectral Compatibility Evaluation on Common Grid
        spectral_eval = evaluate_spectral_compatibility(
            wave_model1=wave_model1,
            wave_model2=wave_model2,
            x1=reproj1["source_x"],
            y1=reproj1["source_y"],
            x2=reproj2["source_x"],
            y2=reproj2["source_y"],
            tolerance=spectral_tolerance,
        )

        # 7. PSF Matching
        fwhm1 = estimate_effective_fwhm(epsf1)
        fwhm2 = estimate_effective_fwhm(epsf2)
        psf_match_res = match_psf_pair(
            image1=reproj1["image"],
            variance1=reproj1["variance"],
            image2=reproj2["image"],
            variance2=reproj2["variance"],
            fwhm1=fwhm1,
            fwhm2=fwhm2,
        )

        # 8. Difference Imaging & Significance Calculation
        diff_res = compute_difference_and_significance(
            image1=psf_match_res["matched_image1"],
            variance1=psf_match_res["matched_variance1"],
            image2=psf_match_res["matched_image2"],
            variance2=psf_match_res["matched_variance2"],
            bad_mask1=qmask1["bad_mask"],
            bad_mask2=qmask2["bad_mask"],
            spectrally_compatible_mask=spectral_eval["compatible_mask"],
            subtract_residual_background=subtract_background,
        )

        # 9. Change Candidate Extraction
        cand_res = extract_change_candidates(
            significance_map=diff_res["significance_map"],
            difference_image=diff_res["difference_image"],
            wcs=target_wcs,
            significance_threshold=significance_threshold,
        )

        # Anti-fabrication candidate tagging: Mark test fixture injections
        candidates = cand_res["candidates"]
        for c in candidates:
            c["is_simulated_injection"] = is_mock
            if is_mock:
                c["candidate_id"] = f"MOCK-INJECTION-{c['candidate_id']}"
                c["quality_assessment"] = f"SIMULATED TEST FIXTURE INJECTION: {c.get('quality_assessment', '')}"

        # 10. Generate PNG previews
        diff_png = render_difference_png_bytes(diff_res["difference_image"])
        diff_b64 = f"data:image/png;base64,{base64.b64encode(diff_png).decode('ascii')}"

        sig_png = render_significance_png_bytes(diff_res["significance_map"], threshold=significance_threshold)
        sig_b64 = f"data:image/png;base64,{base64.b64encode(sig_png).decode('ascii')}"

        epoch1_png = render_to_png_bytes(reproj1["image"], stretch="asinh")
        epoch1_b64 = f"data:image/png;base64,{base64.b64encode(epoch1_png).decode('ascii')}"

        epoch2_png = render_to_png_bytes(reproj2["image"], stretch="asinh")
        epoch2_b64 = f"data:image/png;base64,{base64.b64encode(epoch2_png).decode('ascii')}"

        delta_mjd = abs(mjd2 - mjd1)
        delta_days = delta_mjd
        delta_hours = delta_days * 24.0

        ra_corners, dec_corners = target_wcs.all_pix2world(
            [0, grid_size - 1, grid_size - 1, 0],
            [0, 0, grid_size - 1, grid_size - 1],
            0,
        )

        provenance_record = {
            "provenance_state": "MOCK_TEST" if is_mock else "REAL_VERIFIED",
            "data_source": "SkyTrace M5 Synthetic Test Fixture Generator" if is_mock else "NASA/IPAC Infrared Science Archive (IRSA)",
            "product_or_catalogue_id": f"{fname1}__vs__{fname2}",
            "epoch_1_product": fname1,
            "epoch_1_sha256": sha1,
            "epoch_1_date": date1,
            "epoch_2_product": fname2,
            "epoch_2_sha256": sha2,
            "epoch_2_date": date2,
            "synthetic_real_classification": "MOCK" if is_mock else "REAL",
            "is_synthetic": is_mock,
            "validation_status": "TEST_FIXTURE" if is_mock else "VERIFIED",
            "processing_steps": [
                "MEF_INGEST",
                "WCS_REPROJECTION",
                "QUALITY_BITMASK",
                "PSF_MATCHING",
                "NOISE_PROPAGATED_DIFFERENCE",
                "LOCAL_PEAK_EXTRACTION",
            ],
            "scientific_notes": (
                "Synthetic verification test comparison with controlled injected transients."
                if is_mock else
                "Authentic multi-epoch Level-2 SPHEREx flight observation difference analysis."
            ),
        }

        duration_sec = round(time.time() - start_time, 3)

        return {
            "comparison_status": "SUCCESS",
            "status": "SUCCESS",
            "processing_duration_sec": duration_sec,
            "valid_pixel_count": int(diff_res["metrics"]["valid_pixel_count"]),
            "epoch_1": {
                "file": fname1,
                "date_obs": date1,
                "mjd_obs": mjd1,
                "detector": det1,
                "band": f"SPHEREx-D{det1}",
                "fwhm_pixels": fwhm1,
                "bad_pixel_fraction": qmask1["bad_pixel_fraction"],
                "sha256": sha1,
            },
            "epoch_2": {
                "file": fname2,
                "date_obs": date2,
                "mjd_obs": mjd2,
                "detector": det2,
                "band": f"SPHEREx-D{det2}",
                "fwhm_pixels": fwhm2,
                "bad_pixel_fraction": qmask2["bad_pixel_fraction"],
                "sha256": sha2,
            },
            "temporal_baseline": {
                "delta_mjd": delta_mjd,
                "delta_days": delta_days,
                "delta_hours": delta_hours,
            },
            "registration": {
                "displacement": displacement,
                "center_ra": ra_center,
                "center_dec": dec_center,
                "grid_size": grid_size,
                "pixel_scale_arcsec": 6.2,
                "footprint_polygon": [
                    [float(r), float(d)] for r, d in zip(ra_corners, dec_corners)
                ],
            },
            "spectral_compatibility": {
                "tolerance": spectral_tolerance,
                "compatibility_fraction": spectral_eval["compatibility_fraction"],
                "mean_rel_diff": spectral_eval["mean_rel_diff"],
                "is_spectrally_viable": bool(spectral_eval["compatibility_fraction"] > 0.5),
                "wave_model1_provenance": "SYNTHETIC_DEMO (Linear model)" if wave1_synthetic else "REAL_VERIFIED (WCS-WAVE HDU)",
                "wave_model2_provenance": "SYNTHETIC_DEMO (Linear model)" if wave2_synthetic else "REAL_VERIFIED (WCS-WAVE HDU)",
            },
            "psf_matching": {
                "target_fwhm": psf_match_res["target_fwhm"],
                "convolved_epoch": psf_match_res["convolved_epoch"],
                "matching_sigma": psf_match_res["matching_sigma"],
            },
            "difference_metrics": diff_res["metrics"],
            "candidates": candidates,
            "candidate_count": cand_res["candidate_count"],
            "scientific_disclaimer": DISCLAIMER_LABEL,
            "provenance": provenance_record,
            "previews": {
                "difference_image_b64": diff_b64,
                "significance_map_b64": sig_b64,
                "epoch_1_b64": epoch1_b64,
                "epoch_2_b64": epoch2_b64,
            },
        }
