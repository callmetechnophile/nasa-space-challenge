"""SPHEREx Milestone 6.2 — Archive Reliability and Target Verification Test Suite.
Validates:
  1. Archive Failure Taxonomy:
     - ARCHIVE_QUERY_FAILED (HTTP 500, 502, 503, HTML error payload)
     - ARCHIVE_QUERY_TIMEOUT (HTTP 408 / TimeoutException)
     - ARCHIVE_QUERY_SUCCESS_NO_RESULTS (HTTP 200 with 0 matching rows)
     - NO_SPATIAL_COVERAGE (Confirmed zero records within pointing footprint)
     - INSUFFICIENT_TEMPORAL_COVERAGE (Single epoch available, < 2)
     - SUFFICIENT_TEMPORAL_COVERAGE (>= 2 usable epochs)
     - UNVERIFIED (Unresolved archive queries; never converted to zero coverage)
  2. Bounded retries, exponential backoff with jitter, and Retry-After header parsing.
  3. Caching behavior (disk cache hit vs fresh network query).
  4. R Draconis proper motion astrometric propagation correction.
  5. Five-target catalog completeness, units, and frontend/backend coordinate consistency.
  6. Existing frozen baseline preservation (M1–M5 regressions).
"""

from __future__ import annotations

import os
import sys
import json
import pytest
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.astronomy.m6_target_validation import (
    TARGET_CATALOG,
    propagate_proper_motion,
    TargetValidationSuite,
)
from app.services.spherex_discovery import (
    SpherexDiscoveryService,
    query_archive_collection,
    STATE_ARCHIVE_QUERY_FAILED,
    STATE_ARCHIVE_QUERY_TIMEOUT,
    STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS,
    STATE_NO_SPATIAL_COVERAGE,
    STATE_INSUFFICIENT_TEMPORAL_COVERAGE,
    STATE_SUFFICIENT_TEMPORAL_COVERAGE,
    STATE_UNVERIFIED,
)
from app.providers import get_data_provider

SAMPLE_EMPTY_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obs_id" datatype="char" arraysize="*"/>
      <FIELD name="s_ra" datatype="double"/>
      <FIELD name="s_dec" datatype="double"/>
      <DATA>
        <TABLEDATA>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

SAMPLE_ONE_RECORD_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obs_id" datatype="char" arraysize="*"/>
      <FIELD name="s_ra" datatype="double"/>
      <FIELD name="s_dec" datatype="double"/>
      <FIELD name="t_min" datatype="double"/>
      <FIELD name="energy_bandpassname" datatype="char" arraysize="*"/>
      <FIELD name="access_url" datatype="char" arraysize="*"/>
      <DATA>
        <TABLEDATA>
          <TR>
            <TD>SPX_OBS_TEST_001</TD>
            <TD>248.167625</TD>
            <TD>66.755056</TD>
            <TD>61250.5</TD>
            <TD>SPHEREx-D1</TD>
            <TD>https://irsa.ipac.caltech.edu/data/test.fits</TD>
          </TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""


# =============================================================================
# 1. Target Coordinates & Astrometric Propagation
# =============================================================================

def test_r_draconis_coordinate_propagation_correction():
    """Verify R Draconis proper motion astrometric propagation is mathematically correct.
    Tests:
      - Canonical Gaia DR3 / Hipparcos reference values:
          RA: 248.167625 deg, Dec: +66.755056 deg, Epoch: J2016.0
          pmRA * cos(Dec): +14.82 mas/yr, pmDec: -18.45 mas/yr
      - Guards against spurious +31.25 mas/yr (errant documentation note in M6.2.1 text).
      - Numerical propagation to 2025.8 (delta_t = 9.80 yr).
      - Displacement direction: delta_RA > 0 (eastward), delta_Dec < 0 (southward).
      - Displacement magnitude: sqrt(d_ra_cosdec^2 + d_dec^2) / 1000 = ~0.2319 arcsec.
      - Relative displacement compared to SPHEREx 6.2" pixel (< 0.04 pixel).
    """
    spec = TARGET_CATALOG["r-draconis"]
    # 1. Reference catalog coordinates and proper motion
    assert spec["catalog_ra_deg"] == pytest.approx(248.167625, abs=1e-5)
    assert spec["catalog_dec_deg"] == pytest.approx(66.755056, abs=1e-5)
    assert spec["reference_epoch_year"] == 2016.0
    # Must equal canonical 14.82 mas/yr, NOT spurious 31.25
    assert spec["proper_motion_ra_cosdec_mas_yr"] == pytest.approx(14.82, abs=1e-2)
    assert abs(spec["proper_motion_ra_cosdec_mas_yr"] - 31.25) > 10.0
    assert spec["proper_motion_dec_mas_yr"] == pytest.approx(-18.45, abs=1e-2)

    # 2. Mathematical propagation verification
    delta_t = 2025.8 - 2016.0
    assert delta_t == pytest.approx(9.80, abs=1e-5)

    d_ra_cosdec_mas = 14.82 * delta_t  # +145.236 mas
    d_dec_mas = -18.45 * delta_t       # -180.810 mas
    expected_disp_arcsec = np.hypot(d_ra_cosdec_mas, d_dec_mas) / 1000.0  # ~0.23192"

    cos_dec = np.cos(np.radians(66.755056))
    d_ra_deg = (d_ra_cosdec_mas / 1000.0 / 3600.0) / cos_dec
    d_dec_deg = d_dec_mas / 1000.0 / 3600.0

    # 3. Propagate using engine
    prop_ra, prop_dec, disp_arcsec = propagate_proper_motion(spec, 2025.8)

    # Displacement direction checks:
    # pmRA*cos(Dec) > 0 implies delta_RA > 0
    assert prop_ra > spec["catalog_ra_deg"]
    assert (prop_ra - spec["catalog_ra_deg"]) == pytest.approx(d_ra_deg, abs=1e-7)
    # pmDec < 0 implies delta_Dec < 0
    assert prop_dec < spec["catalog_dec_deg"]
    assert (prop_dec - spec["catalog_dec_deg"]) == pytest.approx(d_dec_deg, abs=1e-7)

    # Propagated coordinates numerical assertion
    assert prop_ra == pytest.approx(248.167727, abs=1e-4)
    assert prop_dec == pytest.approx(66.755006, abs=1e-4)

    # Displacement magnitude assertion
    assert disp_arcsec == pytest.approx(expected_disp_arcsec, abs=1e-4)
    assert disp_arcsec == pytest.approx(0.2319, abs=1e-3)
    assert disp_arcsec / 6.2 < 0.05  # < 0.04 pixel (virtually stationary)


def test_five_targets_catalog_completeness_and_units():
    """Verify all five targets have complete canonical attributes and proper units."""
    expected_targets = ["barnards-star", "epsilon-indi-b", "wise-0855", "rw-aurigae", "r-draconis"]
    for slug in expected_targets:
        assert slug in TARGET_CATALOG
        t = TARGET_CATALOG[slug]
        assert "catalog_ra_deg" in t and 0.0 <= t["catalog_ra_deg"] <= 360.0
        assert "catalog_dec_deg" in t and -90.0 <= t["catalog_dec_deg"] <= 90.0
        assert "proper_motion_ra_cosdec_mas_yr" in t
        assert "proper_motion_dec_mas_yr" in t
        assert "reference_epoch_year" in t
        assert "catalog_source" in t
        assert "target_type" in t


def test_frontend_backend_coordinate_consistency():
    """Verify backend TARGET_CATALOG, Curated data provider, and Frontend presets share identical coordinates."""
    provider = get_data_provider("curated")
    for slug, spec in TARGET_CATALOG.items():
        curated_target = provider.get_target_by_id(slug)
        assert curated_target is not None, f"Target {slug} missing in curated provider"
        assert curated_target.ra_deg == pytest.approx(spec["catalog_ra_deg"], abs=1e-5), (
            f"RA mismatch for {slug}: catalog={spec['catalog_ra_deg']} vs curated={curated_target.ra_deg}"
        )
        assert curated_target.dec_deg == pytest.approx(spec["catalog_dec_deg"], abs=1e-5), (
            f"Dec mismatch for {slug}: catalog={spec['catalog_dec_deg']} vs curated={curated_target.dec_deg}"
        )

    # Verify frontend presets in SpherexSearchPanel.tsx match backend TARGET_CATALOG
    frontend_panel_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../frontend/components/controls/SpherexSearchPanel.tsx")
    )
    if os.path.exists(frontend_panel_path):
        with open(frontend_panel_path, "r", encoding="utf-8") as f:
            content = f.read()

        import re
        # Match lines like: { name: "R Draconis", ra: 248.167625, dec: 66.755056, ... }
        pattern = r'name:\s*"([^"]+)",\s*ra:\s*([0-9.]+),\s*dec:\s*([-0-9.]+)'
        frontend_presets = {
            m.group(1): (float(m.group(2)), float(m.group(3)))
            for m in re.finditer(pattern, content)
        }

        name_to_slug = {
            "Barnard's Star": "barnards-star",
            "Epsilon Indi B": "epsilon-indi-b",
            "WISE 0855": "wise-0855",
            "RW Aurigae": "rw-aurigae",
            "R Draconis": "r-draconis",
        }

        for name, slug in name_to_slug.items():
            assert name in frontend_presets, f"Preset {name} missing from frontend SpherexSearchPanel"
            f_ra, f_dec = frontend_presets[name]
            spec = TARGET_CATALOG[slug]
            assert f_ra == pytest.approx(spec["catalog_ra_deg"], abs=1e-5), f"Frontend RA mismatch for {name}"
            assert f_dec == pytest.approx(spec["catalog_dec_deg"], abs=1e-5), f"Frontend Dec mismatch for {name}"


# =============================================================================
# 2. Archive Retrieval Reliability & Error Taxonomy
# =============================================================================

@pytest.mark.asyncio
async def test_archive_query_502_handling():
    """Verify HTTP 502 produces ARCHIVE_QUERY_FAILED without being converted to 0 observations."""
    mock_resp = MagicMock()
    mock_resp.status_code = 502
    mock_resp.headers = {}
    mock_resp.content = b"<html><body>502 Bad Gateway</body></html>"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=248.167625,
            dec=66.755056,
            radius_deg=0.5,
            timeout_sec=1.0,
            max_retries=1,
            use_cache=False,
        )

        assert res["status"] == STATE_ARCHIVE_QUERY_FAILED
        assert res["http_status"] == 502
        assert "502" in res["message"]
        assert res["count"] == 0
        assert res["from_cache"] is False
        assert "queried_at_utc" in res
        assert "response_duration_ms" in res
        assert res["retry_count"] == 1
        assert "POS=" in res["request_url"]


@pytest.mark.asyncio
async def test_archive_query_500_handling():
    """Verify HTTP 500 produces ARCHIVE_QUERY_FAILED with exception metadata preserved."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.headers = {}
    mock_resp.content = b"Internal Server Error"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await query_archive_collection(
            collection="spherex_qr3",
            ra=133.795129,
            dec=-7.245147,
            radius_deg=0.5,
            timeout_sec=1.0,
            max_retries=1,
            use_cache=False,
        )

        assert res["status"] == STATE_ARCHIVE_QUERY_FAILED
        assert res["http_status"] == 500
        assert res["count"] == 0
        assert res["retry_count"] == 1


@pytest.mark.asyncio
async def test_archive_query_timeout_handling():
    """Verify TimeoutException produces ARCHIVE_QUERY_TIMEOUT."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Connection timed out")
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=269.452083,
            dec=4.693333,
            radius_deg=0.5,
            timeout_sec=0.5,
            max_retries=1,
            use_cache=False,
        )

        assert res["status"] == STATE_ARCHIVE_QUERY_TIMEOUT
        assert res["http_status"] == 408
        assert "timed out" in res["message"].lower()
        assert res["count"] == 0
        assert res["retry_count"] == 1


@pytest.mark.asyncio
async def test_archive_query_successful_empty_response():
    """Verify HTTP 200 with 0 records produces ARCHIVE_QUERY_SUCCESS_NO_RESULTS."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/x-votable+xml"}
    mock_resp.content = SAMPLE_EMPTY_VOTABLE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=0.0,
            dec=0.0,
            radius_deg=0.1,
            timeout_sec=1.0,
            max_retries=0,
            use_cache=False,
        )

        assert res["status"] == STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS
        assert res["http_status"] == 200
        assert res["count"] == 0
        assert res["records"] == []


@pytest.mark.asyncio
async def test_archive_query_successful_with_observations():
    """Verify HTTP 200 with valid VOTable parses rows and returns OK."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/x-votable+xml"}
    mock_resp.content = SAMPLE_ONE_RECORD_VOTABLE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await query_archive_collection(
            collection="spherex_qr3",
            ra=55.555,
            dec=55.555,
            radius_deg=0.5,
            timeout_sec=1.0,
            max_retries=0,
            use_cache=False,
        )

        assert res["status"] == "OK"
        assert res["http_status"] == 200
        assert res["count"] == 1
        assert len(res["records"]) == 1
        assert res["records"][0]["obs_id"] == "SPX_OBS_TEST_001"


@pytest.mark.asyncio
async def test_archive_query_cached_behavior():
    """Verify disk caching returns from_cache=True on subsequent calls."""
    from app.services.spherex_discovery import _cache_key, CACHE_DIR
    ck = _cache_key("spherex_qr3", 99.999, -11.111, 0.1)
    cpath = os.path.join(CACHE_DIR, f"sia_{ck}.json")
    if os.path.exists(cpath):
        os.remove(cpath)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.content = SAMPLE_ONE_RECORD_VOTABLE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        # First call: hits network
        res1 = await query_archive_collection(
            collection="spherex_qr3",
            ra=99.999,
            dec=-11.111,
            radius_deg=0.1,
            timeout_sec=1.0,
            use_cache=True,
        )
        assert res1["from_cache"] is False

        # Second call: served from cache
        res2 = await query_archive_collection(
            collection="spherex_qr3",
            ra=99.999,
            dec=-11.111,
            radius_deg=0.1,
            timeout_sec=1.0,
            use_cache=True,
        )
        assert res2["from_cache"] is True
        assert res2["count"] == res1["count"]


@pytest.mark.asyncio
async def test_archive_query_retry_limits():
    """Verify retry attempts are strictly bounded by max_retries."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.headers = {}
    mock_resp.content = b"Server error"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        max_retries = 2
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=11.11,
            dec=22.22,
            radius_deg=0.1,
            timeout_sec=1.0,
            max_retries=max_retries,
            use_cache=False,
        )
        # Total network attempts must equal max_retries + 1 = 3
        assert mock_get.call_count == max_retries + 1
        assert res["retry_count"] == max_retries


@pytest.mark.asyncio
async def test_archive_query_connect_timeout():
    """Verify ConnectTimeout produces ARCHIVE_QUERY_TIMEOUT and classification CONNECT_TIMEOUT."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectTimeout("Connection handshake timed out")
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=12.34,
            dec=56.78,
            radius_deg=0.5,
            timeout_sec=0.5,
            max_retries=1,
            use_cache=False,
        )
        assert res["status"] == STATE_ARCHIVE_QUERY_TIMEOUT
        assert res["http_status"] == 408
        assert res["classification"] == "CONNECT_TIMEOUT"
        assert len(res["attempts"]) == 2
        assert res["attempts"][0]["classification"] == "CONNECT_TIMEOUT"
        assert res["attempts"][0]["retry_delay_sec"] is not None
        assert res["attempts"][1]["retry_delay_sec"] is None


@pytest.mark.asyncio
async def test_archive_query_read_timeout():
    """Verify ReadTimeout produces ARCHIVE_QUERY_TIMEOUT and classification READ_TIMEOUT."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ReadTimeout("Server socket read timed out")
        res = await query_archive_collection(
            collection="spherex_qr3",
            ra=12.34,
            dec=56.78,
            radius_deg=0.5,
            timeout_sec=0.5,
            max_retries=1,
            use_cache=False,
        )
        assert res["status"] == STATE_ARCHIVE_QUERY_TIMEOUT
        assert res["http_status"] == 408
        assert res["classification"] == "READ_TIMEOUT"
        assert len(res["attempts"]) == 2


@pytest.mark.asyncio
async def test_archive_query_dns_failure():
    """Verify socket/DNS resolution failure produces ARCHIVE_QUERY_FAILED with DNS_FAILURE."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("[Errno 11001] getaddrinfo failed")
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=77.77,
            dec=88.88,
            radius_deg=0.5,
            timeout_sec=1.0,
            max_retries=1,
            use_cache=False,
        )
        assert res["status"] == STATE_ARCHIVE_QUERY_FAILED
        assert res["classification"] == "DNS_FAILURE"
        assert len(res["attempts"]) == 2
        assert res["attempts"][0]["classification"] == "DNS_FAILURE"


@pytest.mark.asyncio
async def test_archive_query_permanent_4xx_error_not_retried():
    """Verify permanent 4xx errors (e.g. 400 Bad Request, 404) are aborted without retry."""
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.headers = {}
    mock_resp.content = b"Bad Request: invalid coordinate syntax"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=0.0,
            dec=0.0,
            radius_deg=0.5,
            timeout_sec=1.0,
            max_retries=2,
            use_cache=False,
        )
        # Must not retry: call count must be exactly 1
        assert mock_get.call_count == 1
        assert res["status"] == STATE_ARCHIVE_QUERY_FAILED
        assert res["http_status"] == 400
        assert res["classification"] == "PERMANENT_CLIENT_ERROR_400"
        assert "Permanent client error" in res["message"]
        assert len(res["attempts"]) == 1
        assert res["attempts"][0]["retry_delay_sec"] is None


@pytest.mark.asyncio
async def test_archive_query_retry_after_longer_than_limit_aborts():
    """Verify Retry-After exceeding operational limit halts retrying immediately."""
    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.headers = {"Retry-After": "60.0"}  # 60s exceeds max_retry_after_sec=5.0s
    mock_429.content = b"Too Many Requests"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_429
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=10.0,
            dec=20.0,
            radius_deg=0.5,
            timeout_sec=1.0,
            max_retries=2,
            max_retry_after_sec=5.0,
            use_cache=False,
        )
        # Aborts immediately without retry
        assert mock_get.call_count == 1
        assert res["status"] == STATE_ARCHIVE_QUERY_FAILED
        assert res["http_status"] == 429
        assert res["classification"] == "RETRY_AFTER_EXCEEDED"
        assert "exceeds operational limit" in res["message"]
        assert len(res["attempts"]) == 1


@pytest.mark.asyncio
async def test_archive_query_retry_after_shorter_than_limit_respected():
    """Verify Retry-After shorter than the operational limit is respected and retried."""
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.headers = {"Retry-After": "0.05"}
    mock_503.content = b"Service Unavailable"

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.headers = {}
    mock_200.content = SAMPLE_ONE_RECORD_VOTABLE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [mock_503, mock_200]
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=33.33,
            dec=44.44,
            radius_deg=0.1,
            timeout_sec=2.0,
            max_retries=1,
            max_retry_after_sec=5.0,
            use_cache=False,
        )
        assert res["status"] == "OK"
        assert res["count"] == 1
        assert res["retry_count"] == 1
        assert len(res["attempts"]) == 2
        assert res["attempts"][0]["classification"] == "RATE_LIMITED_RETRYABLE"
        assert res["attempts"][0]["retry_delay_sec"] == pytest.approx(0.05, abs=1e-3)
        assert res["attempts"][1]["classification"] == "SUCCESS_RECORDS"


@pytest.mark.asyncio
async def test_archive_query_attempts_log_structure():
    """Verify attempt history records every attempt with required diagnostic metadata."""
    mock_500 = MagicMock()
    mock_500.status_code = 500
    mock_500.headers = {}
    mock_500.content = b"Internal Server Error"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_500
        res = await query_archive_collection(
            collection="spherex_dr1",
            ra=1.0,
            dec=2.0,
            radius_deg=0.1,
            timeout_sec=1.0,
            max_retries=1,
            use_cache=False,
        )
        assert len(res["attempts"]) == 2
        for att in res["attempts"]:
            assert "attempt" in att
            assert "timestamp_utc" in att
            assert "duration_ms" in att
            assert "http_status" in att
            assert "classification" in att
            assert "retry_delay_sec" in att


# =============================================================================
# 3. Discovery States & Target Unverified Invariant
# =============================================================================

@pytest.mark.asyncio
async def test_target_unverified_on_failed_archive_query():
    """Verify that when archive queries fail, target status is UNVERIFIED (never zero coverage)."""
    suite = TargetValidationSuite()
    mock_failed_q = {
        "status": STATE_ARCHIVE_QUERY_FAILED,
        "collection": "spherex_dr1",
        "http_status": 502,
        "classification": "PROXY_ERROR_HTML",
        "message": "502 Bad Gateway",
        "count": 0,
        "records": [],
        "attempts": [],
    }

    with patch.object(suite.discovery_service, "query_archive_collection_direct", new_callable=AsyncMock) as mock_q, \
         patch.object(suite.discovery_service, "discover_local_observations", return_value=[]):
        mock_q.return_value = mock_failed_q
        res = await suite.evaluate_target("barnards-star")

        assert res["target_status"] == STATE_UNVERIFIED
        assert res["temporal_coverage_status"] == STATE_UNVERIFIED
        assert res["discovery_state"] == STATE_ARCHIVE_QUERY_FAILED
        assert any("UNVERIFIED" in note for note in res["scientific_assessment"])


@pytest.mark.asyncio
async def test_target_insufficient_on_single_epoch():
    """Verify that a single available epoch (e.g. WISE 0855) returns INSUFFICIENT_TEMPORAL_COVERAGE."""
    suite = TargetValidationSuite()
    mock_failed_q = {
        "status": STATE_ARCHIVE_QUERY_FAILED,
        "collection": "spherex_dr1",
        "http_status": 502,
        "classification": "PROXY_ERROR_HTML",
        "message": "502 Bad Gateway",
        "count": 0,
        "records": [],
        "attempts": [],
    }
    with patch.object(suite.discovery_service, "query_archive_collection_direct", new_callable=AsyncMock) as mock_q:
        mock_q.return_value = mock_failed_q
        res = await suite.evaluate_target("wise-0855")

        # WISE 0855 has 1 verified local Level-2 MEF observation (level2_2025W44)
        assert res["archive_discovery"]["total_usable_observations"] == 1
        assert res["target_status"] == STATE_INSUFFICIENT_TEMPORAL_COVERAGE
        assert res["discovery_state"] == STATE_INSUFFICIENT_TEMPORAL_COVERAGE
        assert any("INSUFFICIENT_TEMPORAL_COVERAGE" in note for note in res["scientific_assessment"])
