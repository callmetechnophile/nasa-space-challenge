"""SPHEREx TAP-based Archive Discovery Adapter (Milestone 6.3).
Implements the official Caltech-IPAC IRSA TAP query workflow using
spherex.artifact, spherex.plane, spatial polygon containment,
and coordinate-centered cutout URL construction.
"""

from __future__ import annotations

import os
import io
import time
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import httpx
from astropy.io.votable import parse_single_table

logger = logging.getLogger("spherex_tap")

IRSA_TAP_SYNC_URL = "https://irsa.ipac.caltech.edu/TAP/sync"
IRSA_TAP_ASYNC_URL = "https://irsa.ipac.caltech.edu/TAP/async"
IRSA_BASE_URL = "https://irsa.ipac.caltech.edu/"

# 7-State Discovery Taxonomy
STATE_ARCHIVE_QUERY_FAILED = "ARCHIVE_QUERY_FAILED"
STATE_ARCHIVE_QUERY_TIMEOUT = "ARCHIVE_QUERY_TIMEOUT"
STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS = "ARCHIVE_QUERY_SUCCESS_NO_RESULTS"
STATE_NO_SPATIAL_COVERAGE = "NO_SPATIAL_COVERAGE"
STATE_INSUFFICIENT_TEMPORAL_COVERAGE = "INSUFFICIENT_TEMPORAL_COVERAGE"
STATE_SUFFICIENT_TEMPORAL_COVERAGE = "SUFFICIENT_TEMPORAL_COVERAGE"
STATE_UNVERIFIED = "UNVERIFIED"


def construct_spherex_tap_query(
    ra_deg: float,
    dec_deg: float,
    cutout_size_deg: float = 0.05,
    bandpass: Optional[str] = None,
    limit: Optional[int] = None,
) -> str:
    """Construct official Caltech-IPAC IRSA TAP query for SPHEREx artifacts and planes.
    Uses:
      - spherex.artifact a
      - spherex.plane p
      - a.planeid = p.planeid
      - WHERE 1 = CONTAINS(POINT('ICRS', ra, dec), p.poly)
      - Cutout URL: https://irsa.ipac.caltech.edu/ || a.uri || '?center=ra,decd&size=cutout_size_deg'
      - ORDER BY p.time_bounds_lower ASC
    """
    ra_val = f"{ra_deg:.6f}"
    dec_val = f"{dec_deg:.6f}"
    size_val = f"{cutout_size_deg:.4f}"

    top_clause = f"TOP {limit} " if limit and limit > 0 else ""

    band_filter = f"AND p.energy_bandpassname = '{bandpass}'" if bandpass else ""

    query = f"""SELECT {top_clause}'{IRSA_BASE_URL}' || a.uri || '?center={ra_val},{dec_val}d&size={size_val}' AS uri,
       a.uri AS artifact_uri,
       p.planeid,
       p.time_bounds_lower,
       p.time_bounds_upper,
       p.energy_bandpassname,
       p.provenance_version,
       p.poly
FROM spherex.artifact a
JOIN spherex.plane p ON a.planeid = p.planeid
WHERE 1 = CONTAINS(POINT('ICRS', {ra_val}, {dec_val}), p.poly)
      {band_filter}
ORDER BY p.time_bounds_lower ASC"""
    return query.strip()


class SpherexTapAdapter:
    """Independent TAP discovery adapter for the SPHEREx archive."""

    def __init__(
        self,
        tap_url: str = IRSA_TAP_SYNC_URL,
        timeout_sec: float = 3.0,
        max_retries: int = 2,
    ):
        self.tap_url = tap_url
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries

    @staticmethod
    def construct_cutout_url(
        artifact_uri: str,
        ra_deg: float,
        dec_deg: float,
        size_deg: float = 0.05,
    ) -> str:
        """Construct coordinate-centered cutout URL per official IRSA tutorial specification."""
        clean_uri = artifact_uri.lstrip("/")
        base = IRSA_BASE_URL.rstrip("/")
        return f"{base}/{clean_uri}?center={ra_deg:.6f},{dec_deg:.6f}d&size={size_deg:.4f}"

    async def query_spatial_tap(
        self,
        ra_deg: float,
        dec_deg: float,
        cutout_size_deg: float = 0.05,
        bandpass: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute TAP query against IRSA with bounded retries, detailed error taxonomy,
        and preservation of original HTTP status and error messages.
        """
        query_sql = construct_spherex_tap_query(
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            cutout_size_deg=cutout_size_deg,
            bandpass=bandpass,
            limit=limit,
        )

        attempts_log: List[Dict[str, Any]] = []
        last_error = None
        status_code = None

        req_payload = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "QUERY": query_sql,
            "FORMAT": "votable",
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_sec, connect=5.0),
            headers={"User-Agent": "SPHEREx-Temporal-Explorer/M6.3"},
        ) as client:
            for attempt in range(1, self.max_retries + 1):
                attempt_meta: Dict[str, Any] = {
                    "attempt": attempt,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                }
                t0 = time.perf_counter()
                try:
                    resp = await client.post(self.tap_url, data=req_payload)
                    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                    status_code = resp.status_code
                    attempt_meta["status_code"] = status_code
                    attempt_meta["duration_ms"] = duration_ms

                    if resp.status_code == 200:
                        records = self._parse_votable_records(resp.content, ra_deg, dec_deg)
                        attempts_log.append(attempt_meta)

                        if len(records) == 0:
                            classification = STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS
                        else:
                            classification = "TAP_QUERY_SUCCESS"

                        return {
                            "status": "success",
                            "http_status": 200,
                            "classification": classification,
                            "query_sql": query_sql,
                            "records_count": len(records),
                            "records": records,
                            "attempts": attempts_log,
                            "error": None,
                        }

                    # Non-200 response
                    err_snippet = resp.text[:300] if resp.text else f"HTTP {status_code}"
                    attempt_meta["error"] = err_snippet
                    last_error = f"HTTP {status_code}: {err_snippet}"
                    attempts_log.append(attempt_meta)

                    # Do not retry on client error (4xx) except 429
                    if 400 <= status_code < 500 and status_code != 429:
                        break

                except httpx.TimeoutException as exc:
                    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                    attempt_meta["status_code"] = None
                    attempt_meta["duration_ms"] = duration_ms
                    attempt_meta["error"] = f"Timeout after {self.timeout_sec}s: {exc}"
                    last_error = attempt_meta["error"]
                    attempts_log.append(attempt_meta)
                except Exception as exc:
                    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                    attempt_meta["status_code"] = None
                    attempt_meta["duration_ms"] = duration_ms
                    attempt_meta["error"] = f"Connection error: {type(exc).__name__}: {exc}"
                    last_error = attempt_meta["error"]
                    attempts_log.append(attempt_meta)

                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * attempt)

        # Classify final failure
        is_timeout = any("Timeout" in a.get("error", "") for a in attempts_log)
        final_class = STATE_ARCHIVE_QUERY_TIMEOUT if is_timeout else STATE_ARCHIVE_QUERY_FAILED

        return {
            "status": "error",
            "http_status": status_code,
            "classification": final_class,
            "query_sql": query_sql,
            "records_count": 0,
            "records": [],
            "attempts": attempts_log,
            "error": last_error or "Unknown TAP error",
        }

    def _parse_votable_records(
        self,
        votable_bytes: bytes,
        target_ra: float,
        target_dec: float,
    ) -> List[Dict[str, Any]]:
        """Parse VOTable XML from TAP service into structured observation records."""
        records: List[Dict[str, Any]] = []
        try:
            table_obj = parse_single_table(io.BytesIO(votable_bytes)).to_table()
            col_map = {c.lower(): c for c in table_obj.colnames}

            for row in table_obj:
                row_dict = {c_lower: row[c_orig] for c_lower, c_orig in col_map.items()}

                uri = str(row_dict.get("uri", "")).strip()
                artifact_uri = str(row_dict.get("artifact_uri", "")).strip()
                planeid = str(row_dict.get("planeid", "")).strip()
                bandpass = str(row_dict.get("energy_bandpassname", "")).strip()
                prov_ver = str(row_dict.get("provenance_version", "")).strip()
                poly_str = str(row_dict.get("poly", "")).strip()

                t_lower = row_dict.get("time_bounds_lower")
                t_upper = row_dict.get("time_bounds_upper")

                # Parse timestamps
                obs_time_iso = None
                if t_lower is not None:
                    try:
                        # MJD or ISO string
                        if isinstance(t_lower, (float, int)):
                            obs_time_iso = str(t_lower)
                        else:
                            obs_time_iso = str(t_lower).strip()
                    except Exception:
                        obs_time_iso = None

                obs_id = str(row_dict.get("obs_id", "")).strip()
                if not obs_id:
                    obs_id = os.path.basename(artifact_uri).replace(".fits", "") if artifact_uri else f"plane_{planeid}"

                mjd_val = 0.0
                if t_lower is not None:
                    try:
                        mjd_val = float(t_lower)
                    except Exception:
                        mjd_val = 0.0

                rec = {
                    "obs_id": obs_id,
                    "uri": uri,
                    "cutout_url": uri,
                    "artifact_uri": artifact_uri,
                    "planeid": int(planeid) if str(planeid).isdigit() else planeid,
                    "bandpass": bandpass,
                    "energy_bandpassname": bandpass,
                    "provenance_version": prov_ver,
                    "time_bounds_lower": t_lower,
                    "time_bounds_upper": t_upper,
                    "mjd_obs": mjd_val,
                    "observation_time_iso": obs_time_iso,
                    "spatial_footprint_poly": poly_str,
                    "target_ra_deg": target_ra,
                    "target_dec_deg": target_dec,
                    "adapter": "TAP",
                }
                records.append(rec)

        except Exception as exc:
            logger.warning("Error parsing TAP VOTable: %s", exc)

        return records
