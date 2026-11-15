"""IRSA SIA2 Client and Query Service for SPHEREx Archive Data (Milestone 4).
Handles asynchronous and robust HTTP communication with the official
NASA/IPAC Infrared Science Archive SIA2 endpoint.
"""

from __future__ import annotations

import os
import io
import time
import asyncio
import logging
import urllib.parse
from typing import Dict, Any, List, Optional
import httpx
from astropy.io.votable import parse_single_table
from astropy.io import fits

from app.models.spherex_observation import (
    SpherexSearchRequest,
    SpherexSearchResponse,
    SpherexObservationRecord,
)
from app.astronomy.fits_dimensions import (
    extract_and_validate_fits_dimensions,
    FitsDimensionValidationError,
)

logger = logging.getLogger("spherex_query")

IRSA_SIA_BASE_URL = "https://irsa.ipac.caltech.edu/SIA"
DEFAULT_STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex"))


def get_cached_filenames() -> set[str]:
    """Return set of filenames already downloaded in the local cache directory."""
    if not os.path.exists(DEFAULT_STORAGE_DIR):
        return set()
    return set(os.listdir(DEFAULT_STORAGE_DIR))


async def query_irsa_sia_collection(
    collection: str,
    ra: float,
    dec: float,
    radius_deg: float,
    timeout_sec: float = 50.0,
    max_retries: int = 0
) -> List[Dict[str, Any]]:
    """Execute a single SIA2 query against IRSA for a specific collection."""
    pos_str = f"circle {ra} {dec} {radius_deg}"
    params = {
        "COLLECTION": collection,
        "POS": pos_str,
    }
    encoded_url = f"{IRSA_SIA_BASE_URL}?{urllib.parse.urlencode(params)}"
    logger.info("Querying IRSA SIA2: %s", encoded_url)

    last_error: Optional[Exception] = None
    timeout_cfg = httpx.Timeout(timeout_sec, connect=15.0, read=timeout_sec)
    async with httpx.AsyncClient(timeout=timeout_cfg, follow_redirects=True) as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.get(
                    encoded_url,
                    headers={"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0 (NASA Space Apps)"}
                )
                if response.status_code != 200:
                    raise RuntimeError(f"IRSA SIA returned HTTP {response.status_code}: {response.text[:200]}")

                content = response.content
                table = parse_single_table(io.BytesIO(content))
                rows = table.array

                results = []
                for row in rows:
                    item = {}
                    for field in table.fields:
                        val = row[field.name]
                        if isinstance(val, (bytes, bytearray)):
                            val = val.decode("utf-8", errors="replace")
                        elif hasattr(val, "item"):
                            val = val.item()
                        item[field.name] = val
                    results.append(item)
                return results

            except Exception as exc:
                last_error = exc
                logger.warning("IRSA SIA attempt %d for %s failed: %s", attempt + 1, collection, exc)
                if attempt < max_retries:
                    await asyncio.sleep(1.0 * (2 ** attempt))

    raise RuntimeError(f"IRSA SIA query failed after {max_retries + 1} attempts: {last_error}")

    raise RuntimeError(f"IRSA SIA query failed after {max_retries + 1} attempts: {last_error}")


def normalize_observation_record(
    raw: Dict[str, Any],
    collection: str,
    cached_files: set[str]
) -> SpherexObservationRecord:
    """Normalize raw SIA2 VOTable fields into a structured SpherexObservationRecord."""
    obs_id = str(raw.get("obs_id", "UNKNOWN"))
    access_url = str(raw.get("access_url", ""))
    filename = os.path.basename(access_url.split("?")[0]) if access_url else f"{obs_id}.fits"
    
    # access_estsize in SIA2 is typically in kilobytes (KB)
    raw_size = raw.get("access_estsize", 0)
    try:
        size_kb = int(raw_size)
        size_bytes = size_kb * 1024
        size_mb = round(size_bytes / (1024 * 1024), 2)
    except Exception:
        size_bytes = 71634240  # Standard SPHEREx ~68.3 MB default
        size_mb = 68.32

    # Check local download cache
    is_cached = filename in cached_files
    dim_x = 0
    dim_y = 0
    if is_cached:
        local_path = os.path.join(DEFAULT_STORAGE_DIR, filename)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            try:
                with fits.open(local_path) as hdul:
                    dim_x, dim_y, _, _ = extract_and_validate_fits_dimensions(hdul, filename=filename)
            except Exception as e:
                logger.debug("Could not read FITS dimensions from %s: %s", filename, e)
        else:
            is_cached = False

    # If not obtained from cached FITS, read from remote record fields without assumed fallbacks
    if dim_x <= 0 or dim_y <= 0:
        raw_x = raw.get("s_xel1") or raw.get("naxis1")
        raw_y = raw.get("s_xel2") or raw.get("naxis2")
        dim_x = int(raw_x) if raw_x is not None else 0
        dim_y = int(raw_y) if raw_y is not None else 0

    # Center coordinates

    return SpherexObservationRecord(
        obs_id=obs_id,
        collection=collection,
        facility_name=str(raw.get("facility_name", "SPHEREx")),
        instrument_name=str(raw.get("instrument_name", "SPHEREx")),
        detector_band=detector_band,
        ra_deg=ra_val,
        dec_deg=dec_val,
        dimensions=(dim_x, dim_y),
        access_url=access_url,
        access_format=str(raw.get("access_format", "image/fits")),
        file_size_bytes=size_bytes,
        file_size_mb=size_mb,
        obs_date=str(raw.get("obs_release_date", raw.get("t_min", ""))),
        cloud_access=raw.get("cloud_access"),
        s_region=raw.get("s_region"),
        is_downloaded=is_cached,
        local_filename=filename if is_cached else None,
    )


async def execute_spherex_search(request: SpherexSearchRequest) -> SpherexSearchResponse:
    """Execute complete archive discovery pipeline with automatic QR2 fallback."""
    cached_files = get_cached_filenames()
    target_coll = request.collection
    fallback_triggered = False
    fallback_coll = None

    try:
        raw_results = await query_irsa_sia_collection(
            collection=target_coll,
            ra=request.ra,
            dec=request.dec,
            radius_deg=request.radius_deg,
            timeout_sec=20.0,
            max_retries=0,
        )
    except Exception as exc:
        logger.warning("Primary collection %s query error: %s", target_coll, exc)
        raw_results = []

    # If QR3 yielded 0 matches and fallback is enabled, query QR2
    if len(raw_results) == 0 and request.allow_fallback and target_coll != "spherex_qr2":
        fallback_coll = "spherex_qr2"
        logger.info("QR3 yielded 0 matches. Initiating fallback query to %s", fallback_coll)
        try:
            fallback_results = await query_irsa_sia_collection(
                collection=fallback_coll,
                ra=request.ra,
                dec=request.dec,
                radius_deg=request.radius_deg,
                timeout_sec=50.0,
                max_retries=0,
            )
            if len(fallback_results) > 0:
                raw_results = fallback_results
                fallback_triggered = True
                target_coll = fallback_coll
        except Exception as exc:
            logger.error("Fallback query to %s failed: %s", fallback_coll, exc)

    # Normalize records
    records: List[SpherexObservationRecord] = []
    for raw in raw_results:
        rec = normalize_observation_record(raw, target_coll, cached_files)
        # Apply detector filter if specified
        if request.detector_filter and rec.detector_band != request.detector_filter:
            continue
        records.append(rec)

    status_str = "OK" if len(records) > 0 else "EMPTY"
    msg = None
    if fallback_triggered:
        msg = f"No observations found in {request.collection}. Successfully retrieved {len(records)} matching observation(s) from fallback collection {fallback_coll}."
    elif len(records) == 0:
        msg = f"No SPHEREx observations found within radius {request.radius_deg}° of ({request.ra:.4f}, {request.dec:.4f}) in {request.collection}."

    return SpherexSearchResponse(
        query_ra=request.ra,
        query_dec=request.dec,
        query_radius_deg=request.radius_deg,
        collection_queried=request.collection,
        fallback_triggered=fallback_triggered,
        fallback_collection=fallback_coll if fallback_triggered else None,
        match_count=len(records),
        observations=records,
        archive_status=status_str,
        message=msg,
    )
