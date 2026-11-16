"""SPHEREx Multi-Epoch Archive Discovery & Time-Series Engine (Milestone 6).
Provides dual-release discovery across DR1 (Surveys 1 & 2) and QR3 (Surveys 3 & 4),
WCS footprint intersection validation, LVF wavelength compatibility grouping,
query result caching, and chronological observation series construction.
"""

from __future__ import annotations

import os
import io
import json
import time
import random
import asyncio
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import httpx
from astropy.io.votable import parse_single_table
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

from app.models.spherex_observation import SpherexObservationRecord
from app.services.spherex_tap import (
    SpherexTapAdapter,
    construct_spherex_tap_query,
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
    STATE_NO_SPATIAL_COVERAGE,
)
from app.astronomy.spectral_compatibility import (
    LVFWavelengthModel,
    evaluate_spectral_compatibility,
)
from app.astronomy.fits_dimensions import (
    extract_and_validate_fits_dimensions,
    FitsDimensionValidationError,
)

logger = logging.getLogger("spherex_discovery")

IRSA_SIA_BASE_URL = "https://irsa.ipac.caltech.edu/SIA"
DATA_DIR = os.getenv("SPHEREX_STORAGE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex")))
CACHE_DIR = os.path.join(DATA_DIR, "cache", "queries")
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
except Exception:
    CACHE_DIR = os.path.join("/tmp", "spherex", "cache", "queries")
    os.makedirs(CACHE_DIR, exist_ok=True)

# Release cataloging prioritizing DR1, DR1 Deep, QR3, QR3 Deep (superseding QR2)
SPHEREx_RELEASES = {
    "dr1": {
        "collection": "spherex_dr1",
        "name": "Data Release 1 (DR1) Wide",
        "surveys": "Surveys 1 & 2",
        "description": "Reprocessed with improved QR3 calibrations",
        "supersedes": ["spherex_qr2"],
    },
    "dr1_deep": {
        "collection": "spherex_dr1_deep",
        "name": "Data Release 1 (DR1) Deep",
        "surveys": "Deep Fields (Surveys 1 & 2)",
        "description": "Deep survey fields reprocessed with improved calibrations",
        "supersedes": ["spherex_qr2"],
    },
    "qr3": {
        "collection": "spherex_qr3",
        "name": "Quick Release 3 (QR3) Wide",
        "surveys": "Surveys 3 & 4",
        "description": "Quick-release science pipeline for second mission year",
        "supersedes": ["spherex_qr2"],
    },
    "qr3_deep": {
        "collection": "spherex_qr3_deep",
        "name": "Quick Release 3 (QR3) Deep",
        "surveys": "Deep Fields (Surveys 3 & 4)",
        "description": "Quick-release deep survey fields",
        "supersedes": ["spherex_qr2"],
    },
}


def _cache_key(collection: str, ra: float, dec: float, radius_deg: float) -> str:
    raw = f"{collection}_{ra:.6f}_{dec:.6f}_{radius_deg:.6f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


async def query_archive_collection(
    collection: str,
    ra: float,
    dec: float,
    radius_deg: float,
    timeout_sec: float = 6.0,
    max_retries: int = 2,
    max_retry_after_sec: float = 5.0,
    initial_delay_sec: float = 0.4,
    backoff_multiplier: float = 2.0,
    max_delay_sec: float = 3.0,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Execute SIA query with local file caching, bounded exponential backoff with jitter,
    respect for Retry-After headers, and explicit 11-state error taxonomy.
    Records every individual HTTP attempt.
    """
    ck = _cache_key(collection, ra, dec, radius_deg)
    cache_path = os.path.join(CACHE_DIR, f"sia_{ck}.json")

    # Check local cache first (bypass if force_refresh is True)
    if use_cache and not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            logger.info("Serving query from disk cache: %s", cache_path)
            cached["from_cache"] = True
            if "classification" not in cached:
                cached["classification"] = "CACHED_SUCCESS" if cached.get("http_status") == 200 else "CACHED_ERROR"
            if "attempts" not in cached:
                cached["attempts"] = []
            return cached
        except Exception as e:
            logger.warning("Failed to read cache file %s: %s", cache_path, e)

    encoded_url = f"{IRSA_SIA_BASE_URL}?POS=circle+{ra}+{dec}+{radius_deg}&COLLECTION={collection}"

    def _save_cache(payload: Dict[str, Any]):
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.warning("Failed to write query cache %s: %s", cache_path, e)

    attempts_log: List[Dict[str, Any]] = []
    last_error_dict = None

    async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
        for attempt in range(max_retries + 1):
            t0 = time.perf_counter()
            utc_req_time = datetime.now(timezone.utc).isoformat()
            try:
                response = await client.get(
                    encoded_url,
                    headers={"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0 (NASA Space Apps Challenge)"}
                )
                duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)

                # Check for permanent client errors (4xx except 429) - do not retry
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    classification = f"PERMANENT_CLIENT_ERROR_{response.status_code}"
                    attempts_log.append({
                        "attempt": attempt + 1,
                        "timestamp_utc": utc_req_time,
                        "duration_ms": duration_ms,
                        "http_status": response.status_code,
                        "classification": classification,
                        "retry_delay_sec": None,
                    })
                    last_error_dict = {
                        "status": STATE_ARCHIVE_QUERY_FAILED,
                        "collection": collection,
                        "http_status": response.status_code,
                        "classification": classification,
                        "message": f"Permanent client error (HTTP {response.status_code}) — aborting without retry",
                        "original_exception": f"HTTPStatusError: {response.status_code}",
                        "records": [],
                        "count": 0,
                        "from_cache": False,
                        "queried_at_utc": utc_req_time,
                        "response_duration_ms": duration_ms,
                        "retry_count": attempt,
                        "attempts": attempts_log,
                        "request_url": encoded_url,
                    }
                    _save_cache(last_error_dict)
                    return last_error_dict

                # Check for rate-limiting (429) or 503 with Retry-After header
                retry_after_hdr = response.headers.get("Retry-After")
                if retry_after_hdr:
                    try:
                        retry_after_val = float(retry_after_hdr)
                    except ValueError:
                        retry_after_val = None

                    if retry_after_val is not None:
                        if retry_after_val > max_retry_after_sec:
                            # If Retry-After exceeds operational limit, stop retrying and report deferred/failed request
                            classification = "RETRY_AFTER_EXCEEDED"
                            attempts_log.append({
                                "attempt": attempt + 1,
                                "timestamp_utc": utc_req_time,
                                "duration_ms": duration_ms,
                                "http_status": response.status_code,
                                "classification": classification,
                                "retry_delay_sec": None,
                            })
                            last_error_dict = {
                                "status": STATE_ARCHIVE_QUERY_RATE_LIMITED,
                                "collection": collection,
                                "http_status": response.status_code,
                                "classification": classification,
                                "message": f"Retry-After ({retry_after_val}s) exceeds operational limit ({max_retry_after_sec}s). Request deferred.",
                                "original_exception": "RetryAfterExceeded",
                                "records": [],
                                "count": 0,
                                "from_cache": False,
                                "queried_at_utc": utc_req_time,
                                "response_duration_ms": duration_ms,
                                "retry_count": attempt,
                                "attempts": attempts_log,
                                "request_url": encoded_url,
                            }
                            _save_cache(last_error_dict)
                            return last_error_dict
                        else:
                            # Respect server-requested delay exactly: do not retry earlier
                            if attempt < max_retries:
                                classification = "RATE_LIMITED_RETRYABLE"
                                wait_sec = retry_after_val
                                attempts_log.append({
                                    "attempt": attempt + 1,
                                    "timestamp_utc": utc_req_time,
                                    "duration_ms": duration_ms,
                                    "http_status": response.status_code,
                                    "classification": classification,
                                    "retry_delay_sec": round(wait_sec, 3),
                                })
                                logger.warning(
                                    "IRSA SIA HTTP %d for %s (attempt %d/%d). Respecting Retry-After: %.2fs...",
                                    response.status_code, collection, attempt + 1, max_retries + 1, wait_sec
                                )
                                await asyncio.sleep(wait_sec)
                                continue
                            else:
                                classification = "RETRY_EXHAUSTED"
                                attempts_log.append({
                                    "attempt": attempt + 1,
                                    "timestamp_utc": utc_req_time,
                                    "duration_ms": duration_ms,
                                    "http_status": response.status_code,
                                    "classification": classification,
                                    "retry_delay_sec": None,
                                })
                                last_error_dict = {
                                    "status": STATE_ARCHIVE_QUERY_RATE_LIMITED if response.status_code == 429 else STATE_ARCHIVE_SERVICE_UNAVAILABLE,
                                    "collection": collection,
                                    "http_status": response.status_code,
                                    "classification": classification,
                                    "message": f"IRSA SIA HTTP {response.status_code} retry budget exhausted ({attempt + 1} attempts)",
                                    "original_exception": f"HTTPStatusError: {response.status_code}",
                                    "records": [],
                                    "count": 0,
                                    "from_cache": False,
                                    "queried_at_utc": utc_req_time,
                                    "response_duration_ms": duration_ms,
                                    "retry_count": attempt,
                                    "attempts": attempts_log,
                                    "request_url": encoded_url,
                                }
                                _save_cache(last_error_dict)
                                return last_error_dict

                # Check for standard server errors (500, 502, 503, 504)
                if response.status_code != 200:
                    classification = f"SERVER_ERROR_{response.status_code}"
                    if attempt < max_retries:
                        wait_sec = min(max_delay_sec, initial_delay_sec * (backoff_multiplier ** attempt)) + random.uniform(0.05, 0.15)
                        attempts_log.append({
                            "attempt": attempt + 1,
                            "timestamp_utc": utc_req_time,
                            "duration_ms": duration_ms,
                            "http_status": response.status_code,
                            "classification": classification,
                            "retry_delay_sec": round(wait_sec, 3),
                        })
                        logger.warning(
                            "IRSA SIA HTTP %d for %s (attempt %d/%d). Retrying after %.2fs...",
                            response.status_code, collection, attempt + 1, max_retries + 1, wait_sec
                        )
                        await asyncio.sleep(wait_sec)
                        continue

                    attempts_log.append({
                        "attempt": attempt + 1,
                        "timestamp_utc": utc_req_time,
                        "duration_ms": duration_ms,
                        "http_status": response.status_code,
                        "classification": classification,
                        "retry_delay_sec": None,
                    })
                    last_error_dict = {
                        "status": STATE_ARCHIVE_SERVICE_UNAVAILABLE,
                        "collection": collection,
                        "http_status": response.status_code,
                        "classification": classification,
                        "message": f"IRSA SIA returned HTTP {response.status_code}",
                        "original_exception": f"HTTPStatusError: {response.status_code}",
                        "records": [],
                        "count": 0,
                        "from_cache": False,
                        "queried_at_utc": utc_req_time,
                        "response_duration_ms": duration_ms,
                        "retry_count": attempt,
                        "attempts": attempts_log,
                        "request_url": encoded_url,
                    }
                    _save_cache(last_error_dict)
                    return last_error_dict

                # Check for HTML error payloads disguised as 200 (IRSA proxy error page)
                content = response.content
                if b"<!DOCTYPE" in content or b"<html" in content.lower():
                    classification = "PROXY_ERROR_HTML"
                    if attempt < max_retries:
                        wait_sec = min(max_delay_sec, initial_delay_sec * (backoff_multiplier ** attempt)) + random.uniform(0.05, 0.15)
                        attempts_log.append({
                            "attempt": attempt + 1,
                            "timestamp_utc": utc_req_time,
                            "duration_ms": duration_ms,
                            "http_status": 502,
                            "classification": classification,
                            "retry_delay_sec": round(wait_sec, 3),
                        })
                        logger.warning(
                            "IRSA SIA returned HTML error page (attempt %d/%d). Retrying after %.2fs...",
                            attempt + 1, max_retries + 1, wait_sec
                        )
                        await asyncio.sleep(wait_sec)
                        continue

                    attempts_log.append({
                        "attempt": attempt + 1,
                        "timestamp_utc": utc_req_time,
                        "duration_ms": duration_ms,
                        "http_status": 502,
                        "classification": classification,
                        "retry_delay_sec": None,
                    })
                    last_error_dict = {
                        "status": STATE_ARCHIVE_SERVICE_UNAVAILABLE,
                        "collection": collection,
                        "http_status": 502,
                        "classification": classification,
                        "message": "IRSA upstream proxy error (502 / invalid gateway HTML response)",
                        "original_exception": "HTMLProxyError: 502 Bad Gateway",
                        "records": [],
                        "count": 0,
                        "from_cache": False,
                        "queried_at_utc": utc_req_time,
                        "response_duration_ms": duration_ms,
                        "retry_count": attempt,
                        "attempts": attempts_log,
                        "request_url": encoded_url,
                    }
                    _save_cache(last_error_dict)
                    return last_error_dict

                # Parse VOTable with strict error guarding
                try:
                    table = parse_single_table(io.BytesIO(content))
                    rows = []
                    for row in table.array:
                        item = {}
                        for field in table.fields:
                            val = row[field.name]
                            if isinstance(val, (bytes, bytearray)):
                                val = val.decode("utf-8", errors="replace")
                            elif hasattr(val, "item"):
                                val = val.item()
                            item[field.name] = val
                        rows.append(item)
                except Exception as parse_exc:
                    classification = "MALFORMED_VOTABLE"
                    attempts_log.append({
                        "attempt": attempt + 1,
                        "timestamp_utc": utc_req_time,
                        "duration_ms": duration_ms,
                        "http_status": 200,
                        "classification": classification,
                        "retry_delay_sec": None,
                    })
                    last_error_dict = {
                        "status": STATE_ARCHIVE_QUERY_FAILED,
                        "collection": collection,
                        "http_status": 200,
                        "classification": classification,
                        "message": f"Malformed VOTable XML payload: {parse_exc}",
                        "original_exception": str(parse_exc),
                        "records": [],
                        "count": 0,
                        "from_cache": False,
                        "queried_at_utc": utc_req_time,
                        "response_duration_ms": duration_ms,
                        "retry_count": attempt,
                        "attempts": attempts_log,
                        "request_url": encoded_url,
                    }
                    _save_cache(last_error_dict)
                    return last_error_dict

                if len(rows) > 0:
                    status = STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS
                    classification = "SUCCESS_RECORDS"
                else:
                    status = STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS
                    classification = "SUCCESS_EMPTY"

                attempts_log.append({
                    "attempt": attempt + 1,
                    "timestamp_utc": utc_req_time,
                    "duration_ms": duration_ms,
                    "http_status": 200,
                    "classification": classification,
                    "retry_delay_sec": None,
                })
                result = {
                    "status": status,
                    "collection": collection,
                    "http_status": 200,
                    "classification": classification,
                    "count": len(rows),
                    "records": rows,
                    "from_cache": False,
                    "queried_at_utc": utc_req_time,
                    "response_duration_ms": duration_ms,
                    "retry_count": attempt,
                    "attempts": attempts_log,
                    "request_url": encoded_url,
                }
                _save_cache(result)
                return result

            except httpx.TimeoutException as exc:
                duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                is_connect = isinstance(exc, httpx.ConnectTimeout)
                is_read = isinstance(exc, httpx.ReadTimeout)
                classification = "CONNECT_TIMEOUT" if is_connect else ("READ_TIMEOUT" if is_read else "TIMEOUT")

                if attempt < max_retries:
                    wait_sec = min(max_delay_sec, initial_delay_sec * (backoff_multiplier ** attempt)) + random.uniform(0.05, 0.15)
                    attempts_log.append({
                        "attempt": attempt + 1,
                        "timestamp_utc": utc_req_time,
                        "duration_ms": duration_ms,
                        "http_status": 408,
                        "classification": classification,
                        "retry_delay_sec": round(wait_sec, 3),
                    })
                    logger.warning(
                        "IRSA SIA %s for %s (attempt %d/%d). Retrying after %.2fs...",
                        classification, collection, attempt + 1, max_retries + 1, wait_sec
                    )
                    await asyncio.sleep(wait_sec)
                    continue

                attempts_log.append({
                    "attempt": attempt + 1,
                    "timestamp_utc": utc_req_time,
                    "duration_ms": duration_ms,
                    "http_status": 408,
                    "classification": classification,
                    "retry_delay_sec": None,
                })
                last_error_dict = {
                    "status": STATE_ARCHIVE_QUERY_TIMEOUT,
                    "collection": collection,
                    "http_status": 408,
                    "classification": classification,
                    "message": f"Query to IRSA SIA timed out after {timeout_sec}s ({attempt + 1} attempts)",
                    "original_exception": str(exc),
                    "records": [],
                    "count": 0,
                    "from_cache": False,
                    "queried_at_utc": utc_req_time,
                    "response_duration_ms": duration_ms,
                    "retry_count": attempt,
                    "attempts": attempts_log,
                    "request_url": encoded_url,
                }
                _save_cache(last_error_dict)
                return last_error_dict

            except httpx.ConnectError as exc:
                duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                err_str = str(exc).lower()
                is_dns = any(kw in err_str for kw in ("gaierror", "getaddrinfo", "name resolution", "nodename"))
                classification = "DNS_FAILURE" if is_dns else "CONNECT_ERROR"

                if attempt < max_retries:
                    wait_sec = min(max_delay_sec, initial_delay_sec * (backoff_multiplier ** attempt)) + random.uniform(0.05, 0.15)
                    attempts_log.append({
                        "attempt": attempt + 1,
                        "timestamp_utc": utc_req_time,
                        "duration_ms": duration_ms,
                        "http_status": 0,
                        "classification": classification,
                        "retry_delay_sec": round(wait_sec, 3),
                    })
                    await asyncio.sleep(wait_sec)
                    continue

                attempts_log.append({
                    "attempt": attempt + 1,
                    "timestamp_utc": utc_req_time,
                    "duration_ms": duration_ms,
                    "http_status": 0,
                    "classification": classification,
                    "retry_delay_sec": None,
                })
                last_error_dict = {
                    "status": STATE_ARCHIVE_QUERY_FAILED,
                    "collection": collection,
                    "http_status": 0,
                    "classification": classification,
                    "message": f"Connection/DNS failure to IRSA SIA: {exc}",
                    "original_exception": str(exc),
                    "records": [],
                    "count": 0,
                    "from_cache": False,
                    "queried_at_utc": utc_req_time,
                    "response_duration_ms": duration_ms,
                    "retry_count": attempt,
                    "attempts": attempts_log,
                    "request_url": encoded_url,
                }
                _save_cache(last_error_dict)
                return last_error_dict

            except Exception as exc:
                duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                classification = "NETWORK_EXCEPTION"
                if attempt < max_retries:
                    wait_sec = min(max_delay_sec, initial_delay_sec * (backoff_multiplier ** attempt)) + random.uniform(0.05, 0.15)
                    attempts_log.append({
                        "attempt": attempt + 1,
                        "timestamp_utc": utc_req_time,
                        "duration_ms": duration_ms,
                        "http_status": 500,
                        "classification": classification,
                        "retry_delay_sec": round(wait_sec, 3),
                    })
                    await asyncio.sleep(wait_sec)
                    continue

                attempts_log.append({
                    "attempt": attempt + 1,
                    "timestamp_utc": utc_req_time,
                    "duration_ms": duration_ms,
                    "http_status": 500,
                    "classification": classification,
                    "retry_delay_sec": None,
                })
                last_error_dict = {
                    "status": STATE_ARCHIVE_QUERY_FAILED,
                    "collection": collection,
                    "http_status": 500,
                    "classification": classification,
                    "message": str(exc),
                    "original_exception": str(exc),
                    "records": [],
                    "count": 0,
                    "from_cache": False,
                    "queried_at_utc": utc_req_time,
                    "response_duration_ms": duration_ms,
                    "retry_count": attempt,
                    "attempts": attempts_log,
                    "request_url": encoded_url,
                }
                _save_cache(last_error_dict)
                return last_error_dict

    return last_error_dict or {
        "status": STATE_ARCHIVE_QUERY_FAILED,
        "collection": collection,
        "http_status": 500,
        "classification": "UNKNOWN_ERROR",
        "message": "Unknown archive query error",
        "records": [],
        "count": 0,
        "from_cache": False,
        "retry_count": max_retries,
        "attempts": attempts_log,
    }


class SpherexDiscoveryService:
    """Multi-Epoch Observation Discovery & Time-Series Assembly."""

    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.tap_adapter = SpherexTapAdapter()

    def list_available_spherex_collections(self) -> List[str]:
        """Discover available collections dynamically with Astroquery or fallback to prioritized releases.
        Prioritizes: spherex_dr1, spherex_dr1_deep, spherex_qr3, spherex_qr3_deep.
        Discontinues treating QR2 as a current searchable collection.
        """
        try:
            from astroquery.ipac.irsa import Irsa
            cols = Irsa.list_collections(servicetype="SIA", filter="spherex")
            if cols:
                # Exclude obsolete QR2 releases
                active = [c for c in cols if "qr2" not in c.lower()]
                if active:
                    return active
        except Exception as exc:
            logger.debug("Dynamic Irsa.list_collections returned: %s. Using prioritized defaults.", exc)

        return ["spherex_dr1", "spherex_dr1_deep", "spherex_qr3", "spherex_qr3_deep"]

    async def query_archive_tap(
        self,
        ra: float,
        dec: float,
        cutout_size_deg: float = 0.05,
        bandpass: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute official Caltech-IPAC IRSA TAP query."""
        return await self.tap_adapter.query_spatial_tap(
            ra_deg=ra,
            dec_deg=dec,
            cutout_size_deg=cutout_size_deg,
            bandpass=bandpass,
            limit=limit,
        )

    async def discover_dual_archive(
        self,
        ra: float,
        dec: float,
        radius_deg: float = 0.5,
        fov_deg: Optional[float] = None,
        cutout_size_deg: float = 0.05,
        collections: Optional[List[str]] = None,
        bandpass: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute dual-adapter archive discovery using both TAP and SIA.
        Preserves individual adapter provenance and deduplicates by artifact URI / obs ID.
        """
        search_radius = fov_deg if fov_deg is not None else radius_deg
        active_colls = collections or ["spherex_dr1", "spherex_qr3"]

        # Run TAP query
        tap_result = await self.query_archive_tap(
            ra=ra,
            dec=dec,
            cutout_size_deg=cutout_size_deg,
            bandpass=bandpass,
        )

        # Run SIA queries across collections
        sia_results = {}
        for c in active_colls:
            sia_res = await self.query_archive_collection_direct(
                collection=c,
                ra=ra,
                dec=dec,
                radius_deg=search_radius,
            )
            sia_results[c] = sia_res

        # Deduplicate records by observation identifier or artifact URI
        dedup_records = {}
        # Add TAP records
        for rec in tap_result.get("records", []):
            key = rec.get("obs_id") or rec.get("artifact_uri") or rec.get("cutout_url")
            if key:
                dedup_records[key] = {
                    "obs_id": rec.get("obs_id", key),
                    "mjd_obs": rec.get("mjd_obs", 0.0),
                    "access_url": rec.get("cutout_url"),
                    "artifact_uri": rec.get("artifact_uri"),
                    "bandpass": rec.get("bandpass", rec.get("energy_bandpassname")),
                    "adapter": "TAP",
                }

        # Add SIA records
        for c, s_res in sia_results.items():
            for rec in s_res.get("records", []):
                key = rec.get("obs_id") or rec.get("access_url") or rec.get("artifact_uri")
                if key and key not in dedup_records:
                    dedup_records[key] = {
                        "obs_id": rec.get("obs_id", key),
                        "mjd_obs": rec.get("mjd_obs", 0.0),
                        "access_url": rec.get("access_url"),
                        "collection": c,
                        "observation_date": rec.get("date_obs"),
                        "adapter": "SIA",
                    }

        dedup_list = list(dedup_records.values())
        return {
            "target_ra_deg": ra,
            "target_dec_deg": dec,
            "search_radius_deg": search_radius,
            "tap_query": tap_result,
            "sia_queries": sia_results,
            "deduplicated_records_count": len(dedup_records),
            "deduplicated_records": dedup_list,
            "observations": dedup_list,
        }

    async def query_archive_collection_direct(
        self,
        collection: str,
        ra: float,
        dec: float,
        radius_deg: float,
        timeout_sec: float = 6.0,
        max_retries: int = 2,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Direct entry point for querying an archive collection with attempt recording."""
        return await query_archive_collection(
            collection=collection,
            ra=ra,
            dec=dec,
            radius_deg=radius_deg,
            timeout_sec=timeout_sec,
            max_retries=max_retries,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )

    def discover_local_observations(
        self,
        ra: float,
        dec: float,
        fov_deg: float = 0.5,
        detector_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Discover locally cached FITS files whose WCS footprint covers the target coordinate."""
        fits_files = [f for f in os.listdir(self.data_dir) if f.endswith(".fits")]
        discovered = []

        for fn in fits_files:
            fpath = os.path.join(self.data_dir, fn)
            try:
                with fits.open(fpath) as hdul:
                    h0 = hdul[0].header

                    # Enforce FITS-derived dimensions without silent fallbacks
                    try:
                        naxis1, naxis2, h_img, _ = extract_and_validate_fits_dimensions(hdul, filename=fn)
                    except FitsDimensionValidationError as dim_err:
                        logger.warning("Skipping FITS file %s due to dimension integrity error: %s", fn, dim_err)
                        continue

                    crval1 = float(h_img.get("CRVAL1", 0.0))
                    crval2 = float(h_img.get("CRVAL2", 0.0))

                    # Spherical angular separation with RA wraparound and polar guard
                    d_ra = ((ra - crval1 + 180.0) % 360.0) - 180.0
                    ra_rad, dec_rad = np.radians(ra), np.radians(dec)
                    c2_rad = np.radians(crval2)
                    d_ra_rad = np.radians(d_ra)
                    cos_theta = np.sin(dec_rad) * np.sin(c2_rad) + np.cos(dec_rad) * np.cos(c2_rad) * np.cos(d_ra_rad)
                    sep = float(np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0))))

                    # Conservative pre-filter: SPHEREx FOV is 3.5 x 3.5 deg (diagonal radius ~2.47 deg).
                    # Threshold of 3.5 deg guarantees corners are never prematurely pruned while shielding SIP solver.
                    if sep > 3.5:
                        continue

                    # Check WCS using validated image header
                    w = WCS(h_img)
                    px, py = w.world_to_pixel_values(ra, dec)

                    in_footprint = (0.0 <= px < naxis1) and (0.0 <= py < naxis2)
                    if not in_footprint:
                        continue

                    obs_id = str(h0.get("OBS_ID", h_img.get("OBSID", fn.split(".")[0])))
                    date_obs = str(h0.get("DATE-OBS", h_img.get("DATE-OBS", "UNKNOWN")))
                    mjd_obs = float(h0.get("MJD-OBS", h_img.get("MJD-OBS", 0.0)))
                    det_id = str(h0.get("DETECTOR", h_img.get("DETECTOR", "D1")))
                    band_name = f"SPHEREx-{det_id}" if not det_id.startswith("SPHEREx-") else det_id

                    if detector_filter and band_name != detector_filter:
                        continue

                    # Evaluate LVF wavelength at pixel
                    eff_wave_um = 1.0
                    try:
                        wave_model = LVFWavelengthModel.from_fits_file(fpath)
                        if wave_model:
                            lam_arr, _ = wave_model.evaluate(np.array([px]), np.array([py]))
                            eff_wave_um = float(lam_arr[0])
                    except Exception:
                        pass

                    discovered.append({
                        "obs_id": obs_id,
                        "file_name": fn,
                        "file_path": fpath,
                        "file_size_bytes": os.path.getsize(fpath),
                        "archive_release": "local_storage",
                        "survey": "Mission Archive",
                        "detector": band_name,
                        "date_obs": date_obs,
                        "mjd_obs": mjd_obs,
                        "ra_target": ra,
                        "dec_target": dec,
                        "pixel_x": float(px),
                        "pixel_y": float(py),
                        "effective_wavelength_um": round(eff_wave_um, 3),
                        "in_footprint": bool(in_footprint),
                        "is_cached": True,
                        "data_quality_status": "CALIBRATED_LEVEL2",
                    })
            except Exception as e:
                logger.debug("Local observation parse skipped for %s: %s", fn, e)

        # Sort chronologically by MJD
        discovered.sort(key=lambda x: x["mjd_obs"])
        return discovered

    async def discover_time_series(
        self,
        ra: float,
        dec: float,
        fov_deg: float = 0.5,
        release: str = "all",  # "dr1", "qr3", "both", "all"
        detector: Optional[str] = None,
        date_min: Optional[str] = None,
        date_max: Optional[str] = None,
        timeout_sec: float = 4.0,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Discover all matching multi-epoch observations across DR1 and QR3."""
        collections_to_query = []
        if release in ("dr1", "both", "all"):
            collections_to_query.append("spherex_dr1")
        if release in ("qr3", "both", "all"):
            collections_to_query.append("spherex_qr3")

        archive_query_results = {}
        all_records = []
        archive_query_errors = []

        for coll in collections_to_query:
            q_res = await query_archive_collection(
                collection=coll,
                ra=ra,
                dec=dec,
                radius_deg=fov_deg,
                timeout_sec=timeout_sec,
                use_cache=use_cache,
                force_refresh=force_refresh,
            )
            archive_query_results[coll] = {
                "status": q_res.get("status"),
                "count": q_res.get("count", len(q_res.get("records", []))),
                "message": q_res.get("message"),
                "from_cache": q_res.get("from_cache", False),
            }

            if q_res.get("status") in ("OK", STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS):
                for raw in q_res.get("records", []):
                    # Check detector filter
                    band_name = str(raw.get("energy_bandpassname", "SPHEREx-D1"))
                    if detector and band_name != detector:
                        continue

                    # Extract true observation time
                    t_min = raw.get("t_min")
                    mjd = float(t_min) if t_min is not None else 0.0
                    obs_id = str(raw.get("obs_id", "UNKNOWN"))
                    access_url = str(raw.get("access_url", ""))
                    filename = os.path.basename(access_url.split("?")[0]) if access_url else f"{obs_id}.fits"
                    is_cached = os.path.exists(os.path.join(self.data_dir, filename))

                    all_records.append({
                        "obs_id": obs_id,
                        "file_name": filename,
                        "archive_release": coll,
                        "detector": band_name,
                        "date_obs": str(raw.get("obs_release_date", raw.get("t_min", ""))),
                        "mjd_obs": mjd,
                        "ra_center": float(raw.get("s_ra", ra)),
                        "dec_center": float(raw.get("s_dec", dec)),
                        "access_url": access_url,
                        "is_cached": is_cached,
                        "data_quality_status": "ARCHIVE_METADATA_VERIFIED",
                    })
            else:
                archive_query_errors.append({
                    "collection": coll,
                    "status": q_res.get("status"),
                    "message": q_res.get("message"),
                })

        # Also incorporate local observations covering this coordinate
        local_obs = self.discover_local_observations(ra, dec, fov_deg, detector_filter=detector)
        for l in local_obs:
            # Check if already added by obs_id
            if not any(r["obs_id"] == l["obs_id"] for r in all_records):
                all_records.append(l)

        # Sort chronologically by MJD
        all_records.sort(key=lambda x: x.get("mjd_obs", 0.0))

        # Check usable count
        usable_count = len(all_records)

        failed_states = {
            STATE_ARCHIVE_QUERY_FAILED,
            STATE_ARCHIVE_QUERY_TIMEOUT,
            STATE_ARCHIVE_QUERY_RATE_LIMITED,
            STATE_ARCHIVE_SERVICE_UNAVAILABLE,
            "TIMEOUT",
            "ARCHIVE_ERROR",
            "PROXY_ERROR",
            "EXCEPTION",
        }
        failed_queries = [
            q for q in archive_query_results.values()
            if q.get("status") in failed_states
        ]

        if failed_queries:
            # A failed archive query does not establish that zero observations exist.
            # Coverage MUST remain UNVERIFIED.
            if any(q.get("status") == STATE_ARCHIVE_QUERY_RATE_LIMITED for q in failed_queries):
                discovery_state = STATE_ARCHIVE_QUERY_RATE_LIMITED
            elif any(q.get("status") in (STATE_ARCHIVE_SERVICE_UNAVAILABLE, "PROXY_ERROR") for q in failed_queries):
                discovery_state = STATE_ARCHIVE_SERVICE_UNAVAILABLE
            elif any(q.get("status") in (STATE_ARCHIVE_QUERY_TIMEOUT, "TIMEOUT") for q in failed_queries):
                discovery_state = STATE_ARCHIVE_QUERY_TIMEOUT
            else:
                discovery_state = STATE_ARCHIVE_QUERY_FAILED

            temporal_coverage_status = STATE_UNVERIFIED
            coverage_status = STATE_UNVERIFIED
            is_sufficient = False
        else:
            # All queries succeeded
            if usable_count >= 2:
                discovery_state = STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS
                temporal_coverage_status = STATE_SUFFICIENT_TEMPORAL_COVERAGE
                coverage_status = STATE_SUFFICIENT_TEMPORAL_COVERAGE
                is_sufficient = True
            elif usable_count == 1:
                discovery_state = STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS
                temporal_coverage_status = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
                coverage_status = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
                is_sufficient = False
            else:
                # 0 records found in verified query
                discovery_state = STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS
                temporal_coverage_status = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
                coverage_status = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
                is_sufficient = False

        return {
            "query": {
                "ra_deg": ra,
                "dec_deg": dec,
                "fov_deg": fov_deg,
                "release": release,
                "detector": detector,
            },
            "archive_queries": archive_query_results,
            "archive_errors": archive_query_errors,
            "total_observations_found": usable_count,
            "discovery_state": discovery_state,
            "temporal_coverage_status": temporal_coverage_status,
            "coverage_status": coverage_status,
            "is_sufficient_for_differencing": is_sufficient,
            "disclaimer": "CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED. Unverified candidates are not astronomical discoveries.",
            "observations": all_records,
        }
