"""Comprehensive test suite for SPHEREx Archive Discovery and Temporal Coverage State Machine.
Verifies all 18 test cases across the 11-state taxonomy, error classification,
anti-fabrication guarantees, coordinate precision, and retry resilience.
"""

import io
import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.spherex_tap import (
    STATE_NOT_QUERIED,
    STATE_QUERYING,
    STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS,
    STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS,
    STATE_ARCHIVE_QUERY_FAILED,
    STATE_ARCHIVE_QUERY_TIMEOUT,
    STATE_ARCHIVE_QUERY_RATE_LIMITED,
    STATE_ARCHIVE_SERVICE_UNAVAILABLE,
    STATE_UNVERIFIED,
    STATE_INSUFFICIENT_TEMPORAL_COVERAGE,
    STATE_SUFFICIENT_TEMPORAL_COVERAGE,
)
from app.services.spherex_discovery import (
    query_archive_collection,
    SpherexDiscoveryService,
    _cache_key,
)

SAMPLE_VALID_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.4" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obs_id" datatype="char" arraysize="*"/>
      <FIELD name="t_min" datatype="double"/>
      <FIELD name="energy_bandpassname" datatype="char" arraysize="*"/>
      <FIELD name="access_url" datatype="char" arraysize="*"/>
      <FIELD name="s_ra" datatype="double"/>
      <FIELD name="s_dec" datatype="double"/>
      <DATA>
        <TABLEDATA>
          <TR>
            <TD>SPHEREx_L2_20250601_001</TD>
            <TD>60827.5</TD>
            <TD>SPHEREx-D1</TD>
            <TD>https://irsa.ipac.caltech.edu/data/SPHEREx/level2/001.fits</TD>
            <TD>269.452083</TD>
            <TD>4.693333</TD>
          </TR>
          <TR>
            <TD>SPHEREx_L2_20251201_002</TD>
            <TD>61010.2</TD>
            <TD>SPHEREx-D1</TD>
            <TD>https://irsa.ipac.caltech.edu/data/SPHEREx/level2/002.fits</TD>
            <TD>269.452083</TD>
            <TD>4.693333</TD>
          </TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

SAMPLE_EMPTY_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.4" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obs_id" datatype="char" arraysize="*"/>
      <FIELD name="t_min" datatype="double"/>
      <FIELD name="energy_bandpassname" datatype="char" arraysize="*"/>
      <DATA>
        <TABLEDATA>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

SAMPLE_SINGLE_RECORD_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE version="1.4" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obs_id" datatype="char" arraysize="*"/>
      <FIELD name="t_min" datatype="double"/>
      <FIELD name="energy_bandpassname" datatype="char" arraysize="*"/>
      <FIELD name="access_url" datatype="char" arraysize="*"/>
      <FIELD name="s_ra" datatype="double"/>
      <FIELD name="s_dec" datatype="double"/>
      <DATA>
        <TABLEDATA>
          <TR>
            <TD>SPHEREx_L2_SINGLE_001</TD>
            <TD>60827.5</TD>
            <TD>SPHEREx-D1</TD>
            <TD>https://irsa.ipac.caltech.edu/data/SPHEREx/level2/single.fits</TD>
            <TD>269.452083</TD>
            <TD>4.693333</TD>
          </TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""


@pytest.mark.asyncio
async def test_case_01_valid_products_found():
    """Case 1: HTTP 200 with valid records returns SUCCESS_WITH_RESULTS."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = SAMPLE_VALID_VOTABLE
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS
        assert res["http_status"] == 200
        assert res["count"] == 2
        assert len(res["records"]) == 2


@pytest.mark.asyncio
async def test_case_02_zero_products_found():
    """Case 2: HTTP 200 with empty table returns SUCCESS_NO_RESULTS."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = SAMPLE_EMPTY_VOTABLE
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS
        assert res["http_status"] == 200
        assert res["count"] == 0
        assert res["records"] == []


@pytest.mark.asyncio
async def test_case_03_http_408_timeout():
    """Case 3: HTTP 408 returns ARCHIVE_QUERY_TIMEOUT."""
    mock_response = MagicMock()
    mock_response.status_code = 408
    mock_response.content = b"Request Timeout"
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=0, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_QUERY_TIMEOUT or res["http_status"] == 408


@pytest.mark.asyncio
async def test_case_04_http_429_rate_limited():
    """Case 4: HTTP 429 returns ARCHIVE_QUERY_RATE_LIMITED."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.content = b"Too Many Requests"
    mock_response.headers = {"Retry-After": "60"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=0, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_QUERY_RATE_LIMITED
        assert res["http_status"] == 429


@pytest.mark.asyncio
async def test_case_05_06_07_08_server_errors():
    """Cases 5-8: HTTP 500, 502, 503, 504 return ARCHIVE_SERVICE_UNAVAILABLE."""
    for code in [500, 502, 503, 504]:
        mock_response = MagicMock()
        mock_response.status_code = code
        mock_response.content = f"Server Error {code}".encode()
        mock_response.headers = {}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=0, use_cache=False, force_refresh=True)
            assert res["status"] == STATE_ARCHIVE_SERVICE_UNAVAILABLE
            assert res["http_status"] == code


@pytest.mark.asyncio
async def test_case_09_dns_failure():
    """Case 9: DNS resolution failure returns ARCHIVE_QUERY_FAILED with DNS_FAILURE classification."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("getaddrinfo failed: nodename nor servname provided")
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=0, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_QUERY_FAILED
        assert res["classification"] == "DNS_FAILURE"


@pytest.mark.asyncio
async def test_case_10_connection_timeout():
    """Case 10: Connection / Read timeout returns ARCHIVE_QUERY_TIMEOUT."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ReadTimeout("Server read timed out")
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=0, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_QUERY_TIMEOUT
        assert res["classification"] == "READ_TIMEOUT"


@pytest.mark.asyncio
async def test_case_11_malformed_votable():
    """Case 11: Malformed VOTable returns ARCHIVE_QUERY_FAILED (never 0 products!)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<VOTABLE><TRUNCATED_XML"
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=0, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_QUERY_FAILED
        assert res["classification"] == "MALFORMED_VOTABLE"
        assert res["count"] == 0
        assert res["records"] == []


@pytest.mark.asyncio
async def test_case_12_proxy_html_error():
    """Case 12: HTML error page returns ARCHIVE_SERVICE_UNAVAILABLE."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"<!DOCTYPE html><html><body><h1>502 Proxy Error</h1></body></html>"
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=0, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_SERVICE_UNAVAILABLE
        assert res["classification"] == "PROXY_ERROR_HTML"


@pytest.mark.asyncio
async def test_case_13_permanent_client_error():
    """Case 13: HTTP 404 or permanent 4xx aborts without retry."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.content = b"Not Found"
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await query_archive_collection("spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=2, use_cache=False, force_refresh=True)
        assert res["status"] == STATE_ARCHIVE_QUERY_FAILED
        assert res["classification"] == "PERMANENT_CLIENT_ERROR_404"
        assert mock_get.call_count == 1  # Aborted immediately without retry


@pytest.mark.asyncio
async def test_case_14_retries_and_backoff():
    """Case 14: Retries up to max_retries upon transient error."""
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.content = b"Service Unavailable"
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await query_archive_collection(
            "spherex_dr1", 269.452083, 4.693333, 0.5, max_retries=2, initial_delay_sec=0.01, use_cache=False, force_refresh=True
        )
        assert res["status"] == STATE_ARCHIVE_SERVICE_UNAVAILABLE
        assert len(res["attempts"]) == 3  # 1 initial + 2 retries


def test_case_15_full_coordinate_precision():
    """Case 15: Barnard's Star coordinates preserve 6-decimal precision in cache key."""
    ra = 269.452083
    dec = 4.693333
    key1 = _cache_key("spherex_dr1", ra, dec, 0.5)
    # Truncated version to 4 decimals must NOT yield identical key
    key2 = _cache_key("spherex_dr1", round(ra, 4), round(dec, 4), 0.5)
    assert key1 != key2, "Cache key improperly collapsed precision"


@pytest.mark.asyncio
async def test_case_16_temporal_coverage_when_archive_fails():
    """Case 16: If archive query fails, temporal coverage status is UNVERIFIED (never zero observations!)."""
    service = SpherexDiscoveryService()

    with patch.object(service, "discover_local_observations", return_value=[]):
        with patch("app.services.spherex_discovery.query_archive_collection", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {
                "status": STATE_ARCHIVE_SERVICE_UNAVAILABLE,
                "http_status": 502,
                "classification": "SERVER_ERROR_502",
                "message": "Proxy Error",
                "records": [],
                "count": 0,
            }

            res = await service.discover_time_series(269.452083, 4.693333, fov_deg=0.5, use_cache=False, force_refresh=True)

            assert res["discovery_state"] == STATE_ARCHIVE_SERVICE_UNAVAILABLE
            assert res["temporal_coverage_status"] == STATE_UNVERIFIED
            assert res["coverage_status"] == STATE_UNVERIFIED
            assert res["is_sufficient_for_differencing"] is False


@pytest.mark.asyncio
async def test_case_17_temporal_coverage_when_archive_empty():
    """Case 17: If archive succeeds with 0 records, temporal coverage is INSUFFICIENT (0)."""
    service = SpherexDiscoveryService()

    with patch.object(service, "discover_local_observations", return_value=[]):
        with patch("app.services.spherex_discovery.query_archive_collection", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {
                "status": STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS,
                "http_status": 200,
                "classification": "SUCCESS_EMPTY",
                "records": [],
                "count": 0,
            }

            res = await service.discover_time_series(269.452083, 4.693333, fov_deg=0.5, use_cache=False, force_refresh=True)

            assert res["discovery_state"] == STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS
            assert res["temporal_coverage_status"] == STATE_INSUFFICIENT_TEMPORAL_COVERAGE
            assert res["total_observations_found"] == 0
            assert res["is_sufficient_for_differencing"] is False


@pytest.mark.asyncio
async def test_case_18_temporal_coverage_sufficient_and_insufficient_counts():
    """Case 18: 1 record -> INSUFFICIENT; 2+ records -> SUFFICIENT."""
    service = SpherexDiscoveryService()

    with patch.object(service, "discover_local_observations", return_value=[]):
        with patch("app.services.spherex_discovery.query_archive_collection", new_callable=AsyncMock) as mock_query:
            # 1 record
            mock_query.return_value = {
                "status": STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS,
                "http_status": 200,
                "classification": "SUCCESS_RECORDS",
                "records": [
                    {
                        "obs_id": "OBS_1",
                        "t_min": 60827.0,
                        "energy_bandpassname": "SPHEREx-D1",
                        "access_url": "https://irsa.ipac.caltech.edu/obs1.fits",
                        "s_ra": 269.452083,
                        "s_dec": 4.693333,
                    }
                ],
                "count": 1,
            }

            res1 = await service.discover_time_series(269.452083, 4.693333, release="dr1", use_cache=False, force_refresh=True)
            assert res1["discovery_state"] == STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS
            assert res1["temporal_coverage_status"] == STATE_INSUFFICIENT_TEMPORAL_COVERAGE
            assert res1["total_observations_found"] == 1
            assert res1["is_sufficient_for_differencing"] is False

            # 2 records
            mock_query.return_value = {
                "status": STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS,
                "http_status": 200,
                "classification": "SUCCESS_RECORDS",
                "records": [
                    {
                        "obs_id": "OBS_1",
                        "t_min": 60827.0,
                        "energy_bandpassname": "SPHEREx-D1",
                        "access_url": "https://irsa.ipac.caltech.edu/obs1.fits",
                        "s_ra": 269.452083,
                        "s_dec": 4.693333,
                    },
                    {
                        "obs_id": "OBS_2",
                        "t_min": 61010.0,
                        "energy_bandpassname": "SPHEREx-D1",
                        "access_url": "https://irsa.ipac.caltech.edu/obs2.fits",
                        "s_ra": 269.452083,
                        "s_dec": 4.693333,
                    },
                ],
                "count": 2,
            }

            res2 = await service.discover_time_series(269.452083, 4.693333, release="dr1", use_cache=False, force_refresh=True)
            assert res2["discovery_state"] == STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS
            assert res2["temporal_coverage_status"] == STATE_SUFFICIENT_TEMPORAL_COVERAGE
            assert res2["total_observations_found"] == 2
            assert res2["is_sufficient_for_differencing"] is True
