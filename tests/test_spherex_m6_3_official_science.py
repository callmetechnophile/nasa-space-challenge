"""SPHEREx Milestone 6.3 — Official Archive and Scientific Recovery Test Suite.
Validates the 21 required verification gates:
  1. TAP spatial query success
  2. TAP query timeout
  3. TAP HTTP failure
  4. SIA/TAP result deduplication
  5. Cutout URL construction
  6. Product retrieval and checksum
  7. DATE-OBS / time-bounds handling
  8. Spatial WCS with SIP
  9. Spectral WCS with WCS-WAVE
  10. SIP disabled only for spectral WCS
  11. Legacy PSF handling (< 7.0)
  12. Version 7+ ePSF handling (>= 7.0 binary table)
  13. Spatially correct ePSF selection
  14. Gaia proper-motion propagation
  15. Gaia-to-SPHEREx astrometric residuals
  16. WISE external-data provenance
  17. Cross-mission separation (WISE never in SPHEREx player)
  18. Compatible two-epoch temporal comparison
  19. Incompatible spectral response rejection
  20. Incompatible PSF rejection
  21. Null-field false-positive validation
"""

from __future__ import annotations

import os
import sys
import json
import hashlib
import pytest
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.services.spherex_tap import (
    SpherexTapAdapter,
    construct_spherex_tap_query,
    STATE_ARCHIVE_QUERY_FAILED,
    STATE_ARCHIVE_QUERY_TIMEOUT,
    STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS,
)
from app.services.spherex_discovery import SpherexDiscoveryService
from app.astronomy.spherex_spectral_wcs import (
    load_dual_wcs_from_hdulist,
    extract_spectral_properties,
    SpherexSpectralWcsError,
)
from app.astronomy.spherex_psf import (
    determine_psf_architecture,
    determine_parent_detector_pixel,
    select_spatially_varying_epsf,
    match_psf_pair,
    load_psf_or_epsf_model,
    SpherexPsfError,
    CALIB_DIR,
)
from app.astronomy.gaia_astrometry import (
    propagate_gaia_source,
    cross_match_spherex_with_gaia,
    evaluate_astrometric_consistency,
    BENCHMARK_GAIA_DR3_STARS,
)
from app.astronomy.wise_crosscheck import (
    get_wise_0855_ground_truth_epochs,
    get_wiseview_url,
    validate_cross_mission_isolation,
    AUTHENTIC_WISE_OBSERVATIONS,
)
from app.astronomy.spherex_mosaic_hips import (
    evaluate_mosaic_differencing_compatibility,
    get_dr1_hips_cube_specifications,
)
from app.astronomy.m5_scientific_audit import (
    run_epsf_injection_recovery_audit,
    run_null_field_false_positive_audit,
)
from app.astronomy.m6_target_validation import (
    TARGET_CATALOG,
    propagate_proper_motion,
    TargetValidationSuite,
)
from app.astronomy.difference_engine import compare_spherex_temporal_pair

SAMPLE_FITS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits")
)


# =========================================================================
# 1. TAP Spatial Query Success
# =========================================================================
@pytest.mark.asyncio
async def test_tap_spatial_query_success():
    """Verify TAP spatial query construction and execution with polygon containment."""
    adapter = SpherexTapAdapter()
    query = construct_spherex_tap_query(ra_deg=133.795129, dec_deg=-7.245147, cutout_size_deg=0.05)
    assert "CONTAINS(POINT('ICRS', 133.795129, -7.245147), p.poly)" in query
    assert "spherex.artifact a" in query
    assert "spherex.plane p" in query
    assert "a.planeid = p.planeid" in query

    # Mock successful HTTP 200 with VOTable response
    mock_votable = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="uri" datatype="char" arraysize="*"/>
      <FIELD name="artifact_uri" datatype="char" arraysize="*"/>
      <FIELD name="planeid" datatype="long"/>
      <FIELD name="time_bounds_lower" datatype="double"/>
      <FIELD name="time_bounds_upper" datatype="double"/>
      <FIELD name="energy_bandpassname" datatype="char" arraysize="*"/>
      <FIELD name="provenance_version" datatype="char" arraysize="*"/>
      <FIELD name="poly" datatype="char" arraysize="*"/>
      <DATA>
        <TABLEDATA>
          <TR>
            <TD>https://irsa.ipac.caltech.edu/data/SPHEREx/level2/cutout.fits?center=133.795129,-7.245147d&amp;size=0.05</TD>
            <TD>/data/SPHEREx/level2/cutout.fits</TD>
            <TD>100234</TD>
            <TD>60995.120000</TD>
            <TD>60995.120500</TD>
            <TD>SPHEREx_Band_1</TD>
            <TD>v20.0</TD>
            <TD>133.7 -7.3, 133.9 -7.3, 133.9 -7.1, 133.7 -7.1</TD>
          </TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = mock_votable
        mock_post.return_value = mock_resp

        res = await adapter.query_spatial_tap(133.795129, -7.245147)
        assert res["status"] == "success"
        assert res["http_status"] == 200
        assert res["classification"] == "TAP_QUERY_SUCCESS"
        assert res["records_count"] == 1
        rec = res["records"][0]
        assert rec["planeid"] == 100234
        assert rec["mjd_obs"] == pytest.approx(60995.120000)
        assert rec["energy_bandpassname"] == "SPHEREx_Band_1"
        assert "cutout.fits" in rec["uri"]


# =========================================================================
# 2. TAP Query Timeout
# =========================================================================
@pytest.mark.asyncio
async def test_tap_query_timeout():
    """Verify TAP query timeout raises structured error and preserves UNVERIFIED state."""
    adapter = SpherexTapAdapter(timeout_sec=0.1, max_retries=2)
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
        res = await adapter.query_spatial_tap(133.795129, -7.245147)
        assert res["status"] == "error"
        assert res["classification"] == STATE_ARCHIVE_QUERY_TIMEOUT
        assert len(res["attempts"]) == 2
        assert "Timeout" in res["error"]


# =========================================================================
# 3. TAP HTTP Failure (e.g. 502 Proxy Error)
# =========================================================================
@pytest.mark.asyncio
async def test_tap_http_failure():
    """Verify TAP HTTP failure (502 Proxy Error) preserves status and error payload."""
    adapter = SpherexTapAdapter(max_retries=2)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        mock_resp.text = "<html><body><h1>502 Proxy Error</h1><p>Error reading from remote server</p></body></html>"
        mock_post.return_value = mock_resp

        res = await adapter.query_spatial_tap(133.795129, -7.245147)
        assert res["status"] == "error"
        assert res["http_status"] == 502
        assert res["classification"] == STATE_ARCHIVE_QUERY_FAILED
        assert "502 Proxy Error" in res["error"]
        assert len(res["attempts"]) == 2


# =========================================================================
# 4. SIA/TAP Result Deduplication
# =========================================================================
@pytest.mark.asyncio
async def test_sia_tap_deduplication():
    """Verify dual discovery across SIA and TAP deduplicates identical products by observation ID."""
    svc = SpherexDiscoveryService()

    # Mock SIA and TAP returning the same observation ID
    mock_sia_obs = [
        {"obs_id": "SPX_L2_20251114_001", "mjd_obs": 60995.1, "band": "1", "release": "dr1"},
        {"obs_id": "SPX_L2_20251114_002", "mjd_obs": 60995.2, "band": "1", "release": "dr1"},
    ]
    mock_tap_obs = [
        {"obs_id": "SPX_L2_20251114_002", "mjd_obs": 60995.2, "band": "1", "release": "dr1"},
        {"obs_id": "SPX_L2_20251114_003", "mjd_obs": 60995.3, "band": "1", "release": "dr1"},
    ]

    with patch.object(svc, "query_archive_collection_direct", new_callable=AsyncMock) as mock_coll, \
         patch.object(svc, "query_archive_tap", new_callable=AsyncMock) as mock_tap:

        mock_coll.return_value = {"status": "OK", "records": mock_sia_obs}
        mock_tap.return_value = {
            "status": "success",
            "records": [
                {"obs_id": o["obs_id"], "mjd_obs": o["mjd_obs"], "energy_bandpassname": "SPHEREx_Band_1"}
                for o in mock_tap_obs
            ]
        }

        res = await svc.discover_dual_archive(ra=133.79, dec=-7.25, fov_deg=0.5)
        obs_ids = [o["obs_id"] for o in res["observations"]]
        # Distinct IDs: SPX_L2_20251114_001, SPX_L2_20251114_002, SPX_L2_20251114_003
        assert len(obs_ids) == len(set(obs_ids))
        assert "SPX_L2_20251114_001" in obs_ids
        assert "SPX_L2_20251114_002" in obs_ids
        assert "SPX_L2_20251114_003" in obs_ids


# =========================================================================
# 5. Cutout URL Construction
# =========================================================================
def test_cutout_url_construction():
    """Verify coordinate-centered cutout URL construction conforms to Caltech tutorial specs."""
    adapter = SpherexTapAdapter()
    url = adapter.construct_cutout_url(
        artifact_uri="/data/SPHEREx/level2/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits",
        ra_deg=133.795129,
        dec_deg=-7.245147,
        size_deg=0.05,
    )
    assert url.startswith("https://irsa.ipac.caltech.edu/data/SPHEREx/level2/")
    assert "?center=133.795129,-7.245147d&size=0.0500" in url


# =========================================================================
# 6. Product Retrieval and Checksum
# =========================================================================
def test_product_retrieval_and_checksum():
    """Verify authentic SPHEREx FITS product retrieval and SHA-256 verification against baseline."""
    assert os.path.exists(SAMPLE_FITS_PATH), f"Sample FITS missing: {SAMPLE_FITS_PATH}"
    with open(SAMPLE_FITS_PATH, "rb") as f:
        file_bytes = f.read()
    digest = hashlib.sha256(file_bytes).hexdigest()
    # Baseline hashes reconciled in M6.2.6
    valid_hashes = (
        "36b330b5ed45161383aedc7e9199619c6ca1873e213a5fdc8ff027274190caf6",  # M4 baseline copy
        "ef0937a508b4ef2bf2be9ee39589d816f16c4c51480cf8dbf2e46d4fa84ceaf3",  # M6.2.5 reported copy
    )
    assert digest in valid_hashes
    assert len(file_bytes) in (71634240, 66735360)


# =========================================================================
# 7. DATE-OBS / Time-Bounds Handling
# =========================================================================
def test_time_bounds_and_date_obs():
    """Verify correct DATE-OBS and time-bounds extraction from authentic SPHEREx FITS header."""
    with fits.open(SAMPLE_FITS_PATH) as hdul:
        hdr = hdul["IMAGE"].header
        date_obs = hdr.get("DATE-OBS")
        assert date_obs is not None
        assert date_obs.startswith("2025-")
        mjd = hdr.get("MJD-OBS", hdr.get("MJD"))
        assert mjd is not None
        assert 60000.0 < mjd < 62000.0


# =========================================================================
# 8. Spatial WCS with SIP
# =========================================================================
def test_spatial_wcs_with_sip():
    """Verify primary spatial WCS retains SIP distortion polynomials intact."""
    with fits.open(SAMPLE_FITS_PATH) as hdul:
        spatial_wcs, _ = load_dual_wcs_from_hdulist(hdul)
        assert spatial_wcs.sip is not None
        assert "TAN-SIP" in spatial_wcs.wcs.ctype[0]
        # Verify valid sky round-trip
        pix = spatial_wcs.all_world2pix([[132.76, -5.65]], 0)
        assert np.isfinite(pix).all()


# =========================================================================
# 9. Spectral WCS with WCS-WAVE
# =========================================================================
def test_spectral_wcs_with_wcs_wave():
    """Verify alternate spectral WCS (key='W') links to WCS-WAVE lookup table."""
    with fits.open(SAMPLE_FITS_PATH) as hdul:
        _, spectral_wcs = load_dual_wcs_from_hdulist(hdul)
        assert "WAVE-TAB" in spectral_wcs.wcs.ctype[0]
        assert "WCS-WAVE" in hdul


# =========================================================================
# 10. SIP Disabled ONLY for Spectral WCS
# =========================================================================
def test_sip_disabled_only_for_spectral_wcs():
    """Verify SIP distortion is explicitly disabled on spectral WCS while intact on spatial WCS."""
    with fits.open(SAMPLE_FITS_PATH) as hdul:
        spatial_wcs, spectral_wcs = load_dual_wcs_from_hdulist(hdul)
        # Spatial WCS must retain SIP
        assert spatial_wcs.sip is not None
        # Spectral WCS must have SIP disabled per Caltech tutorial convention
        assert spectral_wcs.sip is None

        # Verify physical wavelength extraction at center pixel
        spec_props = extract_spectral_properties(hdul, pixel_xy=(1024.0, 1024.0))
        assert 0.70 < spec_props["wavelength_um"] < 5.20
        assert spec_props["bandwidth_um"] > 0.0


# =========================================================================
# 11. Legacy PSF Handling (< 7.0)
# =========================================================================
def test_legacy_psf_handling():
    """Verify version < 7.0 legacy PSF selection and format handling."""
    arch = determine_psf_architecture(pipeline_version="v6.4")
    assert arch == "legacy"

    # Mock legacy PSF in primary or PSF extension
    dummy_psf = np.zeros((21, 21), dtype=np.float32)
    dummy_psf[10, 10] = 1.0
    hdu = fits.ImageHDU(data=dummy_psf, name="PSF")
    hdul = fits.HDUList([fits.PrimaryHDU(), hdu])

    psf_model = load_psf_or_epsf_model(hdul, pipeline_version="v6.4")
    assert psf_model["architecture"] == "legacy"
    assert psf_model["kernel"].shape == (21, 21)


# =========================================================================
# 12. Version 7+ ePSF Handling (>= 7.0 binary table)
# =========================================================================
def test_version_7_epsf_handling():
    """Verify version >= 7.0 binary table ePSF format and zone grid handling."""
    arch = determine_psf_architecture(pipeline_version="v20.0")
    assert arch == "epsf"

    # Check cached calibration file for Detector 1
    d1_calib = os.path.join(CALIB_DIR, "epsf_D1_spx_cal-epsf-v1-2026-191.fits")
    assert os.path.exists(d1_calib), f"Detector 1 ePSF missing: {d1_calib}"

    with fits.open(d1_calib) as hdul:
        assert "EPSF" in hdul
        epsf_table = Table.read(hdul["EPSF"])
        assert len(epsf_table) == 441  # 21 x 21 spatial zone grid
        assert "EPSF" in epsf_table.colnames
        assert "XCENTER" in epsf_table.colnames
        assert "YCENTER" in epsf_table.colnames
        assert "NEFF_MEAN" in epsf_table.colnames
        # Subpixel 2D kernel
        kernel_0 = epsf_table["EPSF"][0]
        assert kernel_0.shape == (33, 33)


# =========================================================================
# 13. Spatially Correct ePSF Selection
# =========================================================================
def test_spatially_correct_epsf_selection():
    """Verify spatially correct ePSF zone mapping using CRPIX1A/CRPIX2A parent detector frame."""
    d1_calib = os.path.join(CALIB_DIR, "epsf_D1_spx_cal-epsf-v1-2026-191.fits")
    with fits.open(d1_calib) as hdul:
        epsf_table = Table.read(hdul["EPSF"])

    # Cutout with CRPIX1A=-500.0, CRPIX2A=-600.0, cutout pixel at (10.0, 10.0)
    # Per Caltech tutorial: xpix_orig = 1 + xpix_cutout - crpix1a = 1 + 10 - (-500) = 511.0
    parent_x, parent_y = determine_parent_detector_pixel(
        cutout_x=10.0,
        cutout_y=10.0,
        crpix1a=-500.0,
        crpix2a=-600.0,
    )
    assert parent_x == 511.0
    assert parent_y == 611.0

    zone_info = select_spatially_varying_epsf(epsf_table, parent_x=parent_x, parent_y=parent_y)
    assert "kernel" in zone_info
    assert zone_info["kernel"].shape == (33, 33)
    # Zone distance should be small
    assert zone_info["zone_distance_pix"] < 100.0


# =========================================================================
# 14. Gaia Proper-Motion Propagation
# =========================================================================
def test_gaia_proper_motion_propagation():
    """Verify Gaia DR3 proper-motion propagation via space motion or rigorous spherical trig."""
    gaia_src = BENCHMARK_GAIA_DR3_STARS[0]
    prop = propagate_gaia_source(gaia_src, target_epoch_year=2025.8)
    assert prop["source_id"] == gaia_src["source_id"]
    assert prop["target_epoch_year"] == 2025.8
    # Displacement should be finite and positive
    assert prop["proper_motion_displacement_arcsec"] > 0.05
    # Magnitude check: ~13 mas/yr * 9.8 yr ~ 127 mas ~ 0.127 arcsec
    assert 0.08 < prop["proper_motion_displacement_arcsec"] < 0.20


# =========================================================================
# 15. Gaia-to-SPHEREx Astrometric Residuals
# =========================================================================
def test_gaia_to_spherex_astrometric_residuals():
    """Verify astrometric residual computation: Delta alpha cos dec, Delta dec, median, RMS, NMAD."""
    # Propagate benchmark stars to 2025.8
    prop_stars = [propagate_gaia_source(s, target_epoch_year=2025.8) for s in BENCHMARK_GAIA_DR3_STARS]

    # Create synthetic measured centroids with small intentional 0.05 arcsec offset
    measured_centroids = []
    for s in prop_stars:
        measured_centroids.append({
            "ra_deg": s["propagated_ra_deg"] + (0.04 / 3600.0) / np.cos(np.radians(s["propagated_dec_deg"])),
            "dec_deg": s["propagated_dec_deg"] + (0.03 / 3600.0),
        })

    match_res = cross_match_spherex_with_gaia(measured_centroids, prop_stars, max_match_radius_arcsec=1.0)
    assert match_res["matched_count"] == len(prop_stars)
    assert match_res["residual_rms_arcsec"] < 0.15
    assert match_res["robust_scatter_nmad_arcsec"] < 0.15
    assert match_res["outlier_count"] == 0

    consistency = evaluate_astrometric_consistency(match_res, threshold_arcsec=0.5)
    assert consistency["status"] == "CONSISTENT"


# =========================================================================
# 16. WISE External-Data Provenance
# =========================================================================
def test_wise_external_data_provenance():
    """Verify WISE 0855 multi-epoch external data provenance (2010 to 2020) and WiseView URL."""
    epochs = get_wise_0855_ground_truth_epochs()
    assert len(epochs) == 4
    # All 4 epochs must have distinct observation dates and MJDs
    mjds = [e["mjd"] for e in epochs]
    assert len(mjds) == len(set(mjds))
    assert min(mjds) > 55000.0
    assert max(mjds) < 60000.0

    # Test WiseView URL generation
    wv_url = get_wiseview_url()
    assert "byw.tools/wiseview" in wv_url
    assert "ra=133.786245" in wv_url
    assert "dec=-7.247160" in wv_url


# =========================================================================
# 17. Cross-Mission Separation (WISE never in SPHEREx player)
# =========================================================================
def test_cross_mission_separation():
    """Verify strict cross-mission separation: WISE data is never allowed as SPHEREx playback frame."""
    wise_epoch = AUTHENTIC_WISE_OBSERVATIONS[0]
    validation = validate_cross_mission_isolation(
        candidate_observation=wise_epoch,
        pipeline_context="spherex_time_series_player",
    )
    assert validation["permitted"] is False
    assert validation["verdict"] == "REJECTED_CROSS_MISSION_ISOLATION"
    assert "WISE" in validation["reason"]


# =========================================================================
# 18. Compatible Two-Epoch Temporal Comparison
# =========================================================================
def test_compatible_two_epoch_temporal_comparison():
    """Verify compatible two-epoch temporal comparison executes successfully."""
    # Create two synthetic observations with identical bandpass and PSF
    np.random.seed(42)
    frame1 = np.ones((64, 64), dtype=np.float32) * 10.0 + np.random.normal(0, 0.5, (64, 64))
    frame2 = np.ones((64, 64), dtype=np.float32) * 10.0 + np.random.normal(0, 0.5, (64, 64))
    # Inject 1 transient in frame2
    frame2[32, 32] += 15.0

    meta1 = {"bandpass": "SPHEREx_Band_1", "psf_fwhm_arcsec": 6.0, "mjd": 60995.1}
    meta2 = {"bandpass": "SPHEREx_Band_1", "psf_fwhm_arcsec": 6.0, "mjd": 61120.5}

    res = compare_spherex_temporal_pair(frame1, frame2, meta1, meta2, significance_sigma=3.0)
    assert res["status"] == "COMPLETED"
    assert res["compatibility"]["bandpass_match"] is True
    assert res["transient_count"] >= 1


# =========================================================================
# 19. Incompatible Spectral Response Rejection
# =========================================================================
def test_incompatible_spectral_response_rejection():
    """Verify comparison across incompatible spectral bandpasses raises structured rejection."""
    frame1 = np.ones((32, 32), dtype=np.float32)
    frame2 = np.ones((32, 32), dtype=np.float32)
    meta1 = {"bandpass": "SPHEREx_Band_1", "psf_fwhm_arcsec": 6.0}
    meta2 = {"bandpass": "SPHEREx_Band_6", "psf_fwhm_arcsec": 6.0}

    with pytest.raises(ValueError) as excinfo:
        compare_spherex_temporal_pair(frame1, frame2, meta1, meta2)
    assert "Incompatible spectral bandpasses" in str(excinfo.value)


# =========================================================================
# 20. Incompatible PSF Rejection
# =========================================================================
def test_incompatible_psf_rejection():
    """Verify comparison with severely incompatible or missing PSF raises structured rejection."""
    # Attempt PSF matching with incompatible kernel ratios or corrupted PSF
    psf1 = np.ones((5, 5)) / 25.0
    psf2 = np.zeros((5, 5))  # Corrupted zero PSF

    with pytest.raises(SpherexPsfError) as excinfo:
        match_psf_pair(psf1, psf2)
    assert "non-zero" in str(excinfo.value) or "invalid" in str(excinfo.value).lower()


# =========================================================================
# 21. Null-Field False-Positive Validation
# =========================================================================
def test_null_field_false_positive_validation():
    """Verify null-field Monte Carlo difference imaging false-positive density is statistically bounded."""
    audit_res = run_null_field_false_positive_audit(
        image_shape=(128, 128),
        background_sigma=1.0,
        detection_threshold_sigma=5.0,
        n_trials=10,
        pixel_scale_arcsec=6.2,
        seed=123,
    )
    assert audit_res["total_trials"] == 10
    # At 5-sigma detection in pure Gaussian noise, theoretical false positive rate is ~3e-7 per pixel
    # In a 128x128 image (16,384 pixels) over 10 trials, false positives should be near 0
    assert audit_res["false_positive_count"] <= 2
    assert audit_res["mean_false_positives_per_trial"] <= 0.2
    assert audit_res["false_positive_density_per_sq_deg"] < 50.0
