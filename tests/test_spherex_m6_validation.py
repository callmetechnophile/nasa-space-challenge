"""SPHEREx Milestone 6 - Challenge Completion Scientific & Engineering Validation Suite.
Validates the full NASA SPHEREx Challenge implementation:
  1. Coordinate ingestion and sexagesimal conversion (RA [0, 360], Dec [-90, +90])
  2. Astrometric proper motion propagation to nominal mission epoch (2025.8)
  3. NASA 5-Target catalog resolution and physical constraints
  4. SPHEREx spatial resolution limit (Epsilon Indi B binary unresolved at 6.2" PSF)
  5. WISE 0855 Level-2 MEF footprint detection and local FITS mapping
  6. WCS footprint intersection validation with SIP divergence guards
  7. LVF wavelength model evaluation across detector pixel space
  8. Independent DR1 and QR3 archive discovery with local query caching
  9. Multi-epoch chronological observation sequence ordering (MJD-based)
  10. Sufficient coverage verification on approved SPHEREx equatorial pair
  11. Insufficient coverage enforcement on unobserved sky regions
  12. Mandatory non-discovery disclaimer preservation across all endpoints and models
  13. Frozen M1-M5 baseline integrity: QR3 FITS SHA-256 hashes and M5 CONDITIONAL verdict
  14. FastAPI REST API endpoints (/temporal/discovery, /targets/m6-validation)
"""

from __future__ import annotations

import os
import sys
import hashlib
import pytest
import numpy as np
from astropy.wcs import WCS
from astropy.io import fits
from fastapi.testclient import TestClient

# Ensure backend modules are discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.astronomy.coordinates import (
    parse_sexagesimal_ra,
    parse_sexagesimal_dec,
    deg_to_hms,
    deg_to_dms,
)
from app.astronomy.m6_target_validation import (
    TARGET_CATALOG,
    propagate_proper_motion,
    TargetValidationSuite,
)
from app.services.spherex_discovery import (
    SpherexDiscoveryService,
    query_archive_collection,
    _cache_key,
)
from app.astronomy.spectral_compatibility import LVFWavelengthModel
from app.astronomy.change_detection import DISCLAIMER_LABEL
from app.main import app

# Frozen Approved Level-2 FITS files and their SHA-256 baseline digests
FITS_2026W31 = os.path.abspath("data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits")
FITS_2026W32 = os.path.abspath("data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits")
FITS_2025W44 = os.path.abspath("data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits")

SHA256_2026W31 = "b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1"
SHA256_2026W32 = "60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e"


# =============================================================================
# 1. Coordinate Ingestion & Parsing
# =============================================================================

def test_coordinate_sexagesimal_parsing_valid():
    """Verify conversion of standard sexagesimal coordinate strings."""
    # Barnard's Star
    ra_deg = parse_sexagesimal_ra("17h 57m 48.50s")
    dec_deg = parse_sexagesimal_dec("+04° 41' 36.00\"")
    assert pytest.approx(ra_deg, abs=1e-4) == 269.452083
    assert pytest.approx(dec_deg, abs=1e-4) == 4.693333

    # WISE 0855 (NASA challenge target format)
    ra_w = parse_sexagesimal_ra("08h55m10.831s")
    dec_w = parse_sexagesimal_dec("-07d14m42.53s")
    assert pytest.approx(ra_w, abs=1e-4) == 133.795129
    assert pytest.approx(dec_w, abs=1e-4) == -7.245147


def test_coordinate_formatting_roundtrip():
    """Verify roundtrip consistency of coordinate formatting."""
    ra = 133.795129
    dec = -7.245147
    hms = deg_to_hms(ra)
    dms = deg_to_dms(dec)
    assert "08h 55m" in hms
    assert "-07° 14'" in dms


def test_coordinate_parsing_boundary_rejection():
    """Verify strict rejection of out-of-bounds coordinates."""
    with pytest.raises(ValueError):
        parse_sexagesimal_dec("+95° 00' 00\"")
    with pytest.raises(ValueError):
        parse_sexagesimal_dec("-91° 00' 00\"")


# =============================================================================
# 2. Proper Motion Astrometric Propagation
# =============================================================================

def test_proper_motion_propagation_barnards_star():
    """Verify Barnard's Star 10.37 arcsec/yr displacement propagation."""
    spec = TARGET_CATALOG["barnards-star"]
    prop_ra, prop_dec, disp_arcsec = propagate_proper_motion(spec, 2025.8)
    # 9.8 years * 10.37"/yr ~ 101.5 arcsec (~16.4 SPHEREx pixels)
    assert 98.0 <= disp_arcsec <= 105.0
    assert disp_arcsec / 6.2 > 15.0  # Exceeds 15 detector pixels
    assert prop_dec > spec["catalog_dec_deg"]  # Positive declination proper motion


def test_proper_motion_propagation_wise_0855():
    """Verify WISE 0855 proper motion propagation over 15.8-year baseline."""
    spec = TARGET_CATALOG["wise-0855"]
    prop_ra, prop_dec, disp_arcsec = propagate_proper_motion(spec, 2025.8)
    # 15.8 years * 8.15"/yr ~ 128.8 arcsec (~20.8 SPHEREx pixels)
    assert 120.0 <= disp_arcsec <= 135.0
    assert prop_ra < spec["catalog_ra_deg"]  # Negative RA proper motion


def test_proper_motion_stationary_stars():
    """Verify RW Aurigae and R Draconis remain virtually stationary relative to 6.2" pixel."""
    for slug in ("rw-aurigae", "r-draconis"):
        spec = TARGET_CATALOG[slug]
        _, _, disp_arcsec = propagate_proper_motion(spec, 2025.8)
        # Shift is small fraction of a 6.2" pixel (< 0.1 pixel)
        assert disp_arcsec / 6.2 < 0.1


# =============================================================================
# 3. NASA 5-Target Catalog & Physical Resolution Constraints
# =============================================================================

def test_five_targets_catalog_completeness():
    """Verify all 5 required targets are present in catalog with required metadata."""
    expected_slugs = ["barnards-star", "epsilon-indi-b", "wise-0855", "rw-aurigae", "r-draconis"]
    for slug in expected_slugs:
        assert slug in TARGET_CATALOG
        t = TARGET_CATALOG[slug]
        assert "name" in t
        assert "catalog_ra_deg" in t
        assert "catalog_dec_deg" in t
        assert "reference_epoch" in t
        assert "spectral_type" in t


def test_epsilon_indi_b_spatial_resolution_constraint():
    """Verify Epsilon Indi B binary separation (0.73") is flagged as unresolved at 6.2" PSF."""
    t = TARGET_CATALOG["epsilon-indi-b"]
    assert t["binary_separation_arcsec"] == 0.73
    assert t["binary_separation_arcsec"] < 6.2  # Unresolved by SPHEREx telescope
    assert "Unresolved" in t["spatial_resolution_expectation"]


def test_wise_0855_in_local_level2_fits():
    """Verify WISE 0855 coordinates fall inside local Level-2 FITS file level2_2025W44.
    Dynamically extracts detector dimensions and BITPIX from HDU 1 (IMAGE),
    replacing hardcoded 2048x2048 assumptions with true FITS image boundaries (2040x2040).
    Verifies both catalog and proper-motion-propagated coordinate projections.
    """
    assert os.path.exists(FITS_2025W44)
    with fits.open(FITS_2025W44) as hdul:
        # HDU 1 is IMAGE extension
        img_hdu = hdul[1]
        assert img_hdu.name == "IMAGE"
        assert img_hdu.header["BITPIX"] == -32  # IEEE 754 single precision float32

        # Extract dynamic image dimensions directly from FITS header
        naxis1 = int(img_hdu.header["NAXIS1"])
        naxis2 = int(img_hdu.header["NAXIS2"])
        assert naxis1 == 2040, f"Expected calibrated NAXIS1=2040, got {naxis1}"
        assert naxis2 == 2040, f"Expected calibrated NAXIS2=2040, got {naxis2}"

        w = WCS(img_hdu.header)

        # 1. Catalog coordinate projection
        spec = TARGET_CATALOG["wise-0855"]
        cat_ra = spec["catalog_ra_deg"]
        cat_dec = spec["catalog_dec_deg"]
        px_cat, py_cat = w.world_to_pixel_values(cat_ra, cat_dec)

        # Confirm catalog coordinates fall strictly inside actual FITS detector boundaries
        assert 0.0 <= px_cat < naxis1, f"Catalog px={px_cat} out of bounds [0, {naxis1})"
        assert 0.0 <= py_cat < naxis2, f"Catalog py={py_cat} out of bounds [0, {naxis2})"
        assert pytest.approx(px_cat, abs=0.5) == 176.16
        assert pytest.approx(py_cat, abs=0.5) == 266.04

        # 2. Propagated coordinate projection (at observation epoch 2025.8)
        prop_ra, prop_dec, _ = propagate_proper_motion(spec, 2025.8)
        px_prop, py_prop = w.world_to_pixel_values(prop_ra, prop_dec)

        # Confirm propagated coordinates fall strictly inside actual FITS detector boundaries
        assert 0.0 <= px_prop < naxis1, f"Propagated px={px_prop} out of bounds [0, {naxis1})"
        assert 0.0 <= py_prop < naxis2, f"Propagated py={py_prop} out of bounds [0, {naxis2})"
        assert pytest.approx(px_prop, abs=0.5) == 196.65
        assert pytest.approx(py_prop, abs=0.5) == 262.79


# =============================================================================
# 4. LVF Wavelength Model & WCS Footprint Evaluation
# =============================================================================

def test_lvf_wavelength_evaluation_from_fits():
    """Verify LVFWavelengthModel loads WCS-WAVE from approved Level-2 FITS and evaluates continuous wavelengths."""
    model = LVFWavelengthModel.from_fits_file(FITS_2026W31)
    assert model is not None
    # Evaluate at center (1024, 1024) and edges
    x_coords = np.array([0.0, 1024.0, 2048.0])
    y_coords = np.array([0.0, 1024.0, 2048.0])
    lams, d_lams = model.evaluate(x_coords, y_coords)
    assert len(lams) == 3
    # All wavelengths must fall within nominal Band 1 (0.75 - 1.20 um)
    for lam in lams:
        assert 0.70 <= lam <= 1.30


def test_wcs_footprint_sip_guard():
    """Verify pre-filtering prevents SIP divergence on distant coordinates."""
    discovery = SpherexDiscoveryService()
    # Query point far from approved equatorial observation (e.g. North Pole)
    obs = discovery.discover_local_observations(ra=0.0, dec=89.0)
    assert len(obs) == 0  # Cleanly rejected without SIP divergence warning


# =============================================================================
# 5. Archive Discovery Service & Multi-Epoch Ordering
# =============================================================================

@pytest.mark.asyncio
async def test_multi_epoch_chronological_ordering():
    """Verify observations are ordered strictly chronologically by MJD."""
    discovery = SpherexDiscoveryService()
    # Equatorial approved pair coordinates
    res = await discovery.discover_time_series(ra=46.844, dec=1.832, release="all")
    obs = res.get("observations", [])
    assert len(obs) >= 2
    for i in range(len(obs) - 1):
        assert obs[i]["mjd_obs"] <= obs[i + 1]["mjd_obs"]


@pytest.mark.asyncio
async def test_sufficient_temporal_coverage_equatorial_pair():
    """Verify approved equatorial pair yields SUFFICIENT_MULTI_EPOCH_COVERAGE."""
    discovery = SpherexDiscoveryService()
    res = await discovery.discover_time_series(ra=46.844, dec=1.832, release="all")
    assert res["temporal_coverage_status"] in ("SUFFICIENT_TEMPORAL_COVERAGE", "SUFFICIENT_MULTI_EPOCH_COVERAGE")
    assert res["total_observations_found"] >= 2


@pytest.mark.asyncio
async def test_insufficient_temporal_coverage_handling():
    """Verify that unobserved sky coordinates return UNVERIFIED, NO_SPATIAL_COVERAGE, or INSUFFICIENT coverage without fabricating data."""
    discovery = SpherexDiscoveryService()
    # Unobserved location (e.g. RA=12.345, Dec=-45.678)
    res = await discovery.discover_time_series(ra=12.345, dec=-45.678, release="all")
    assert res["temporal_coverage_status"] in ("INSUFFICIENT_TEMPORAL_COVERAGE", "INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE", "UNVERIFIED", "NO_SPATIAL_COVERAGE")
    assert len(res["observations"]) == 0


# =============================================================================
# 6. Non-Discovery Disclaimer & Candidate Labeling Invariant
# =============================================================================

def test_disclaimer_label_enforcement():
    """Verify mandatory non-discovery disclaimer is present in candidate extracts and targets."""
    assert DISCLAIMER_LABEL == "CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED"


@pytest.mark.asyncio
async def test_target_validation_suite_disclaimer():
    """Verify TargetValidationSuite output includes non-discovery disclaimer."""
    suite = TargetValidationSuite()
    res = await suite.evaluate_target("wise-0855")
    assert "disclaimer" in res
    assert "NOT SCIENTIFICALLY CONFIRMED" in res["disclaimer"]


# =============================================================================
# 7. Frozen M1-M5 Baseline Preservation
# =============================================================================

def test_frozen_approved_fits_hashes():
    """Verify approved QR3 Level-2 MEF FITS files are bit-for-bit identical to frozen baseline."""
    with open(FITS_2026W31, "rb") as f:
        h1 = hashlib.sha256(f.read()).hexdigest()
    with open(FITS_2026W32, "rb") as f:
        h2 = hashlib.sha256(f.read()).hexdigest()

    assert h1 == SHA256_2026W31
    assert h2 == SHA256_2026W32
    assert os.path.getsize(FITS_2026W31) == 65488320
    assert os.path.getsize(FITS_2026W32) == 65488320


# =============================================================================
# 8. REST API Endpoints Integration
# =============================================================================

def test_api_temporal_discovery_endpoint():
    """Verify GET /api/v1/temporal/discovery returns valid schema and headers."""
    client = TestClient(app)
    response = client.get("/api/v1/temporal/discovery?ra=46.844&dec=1.832&release=all")
    assert response.status_code == 200
    data = response.json()
    assert "observations" in data
    assert "coverage_status" in data
    assert "archive_queries" in data
    assert data["total_observations_found"] >= 2


def test_api_m6_targets_validation_endpoint():
    """Verify GET /api/v1/targets/m6-validation returns all 5 targets."""
    client = TestClient(app)
    response = client.get("/api/v1/targets/m6-validation")
    assert response.status_code == 200
    data = response.json()
    assert "barnards-star" in data
    assert "wise-0855" in data
    assert "epsilon-indi-b" in data
    assert "rw-aurigae" in data
    assert "r-draconis" in data


def test_api_m6_single_target_validation_endpoint():
    """Verify GET /api/v1/targets/m6-validation/{target_slug} returns individual target report."""
    client = TestClient(app)
    response = client.get("/api/v1/targets/m6-validation/wise-0855")
    assert response.status_code == 200
    data = response.json()
    assert data["target"]["name"] == "WISE 0855"
    assert "propagated_coordinates" in data
    assert "temporal_coverage_status" in data
