"""Patch spherex_discovery.py to implement 11-state taxonomy, precision coordinates, VOTable validation, and bypassable cache."""
import sys

with open("backend/app/services/spherex_discovery.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update imports
old_imports = """from app.services.spherex_tap import (
    SpherexTapAdapter,
    construct_spherex_tap_query,
    STATE_ARCHIVE_QUERY_FAILED,
    STATE_ARCHIVE_QUERY_TIMEOUT,
    STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS,
    STATE_NO_SPATIAL_COVERAGE,
    STATE_INSUFFICIENT_TEMPORAL_COVERAGE,
    STATE_SUFFICIENT_TEMPORAL_COVERAGE,
    STATE_UNVERIFIED,
)"""

new_imports = """from app.services.spherex_tap import (
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
)"""

if old_imports in code:
    code = code.replace(old_imports, new_imports)
    print("Updated imports in spherex_discovery.py")

# 2. Update _cache_key to full precision (6 decimals)
old_cache_key = """def _cache_key(collection: str, ra: float, dec: float, radius_deg: float) -> str:
    raw = f"{collection}_{ra:.4f}_{dec:.4f}_{radius_deg:.4f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]"""

new_cache_key = """def _cache_key(collection: str, ra: float, dec: float, radius_deg: float) -> str:
    raw = f"{collection}_{ra:.6f}_{dec:.6f}_{radius_deg:.6f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]"""

if old_cache_key in code:
    code = code.replace(old_cache_key, new_cache_key)
    print("Updated _cache_key precision")

# 3. Update query_archive_collection signature and cache check
old_sig = """async def query_archive_collection(
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
) -> Dict[str, Any]:
    \"\"\"Execute SIA query with local file caching, bounded exponential backoff with jitter,
    respect for Retry-After headers, and explicit 7-state error taxonomy.
    Records every individual HTTP attempt.
    \"\"\"
    ck = _cache_key(collection, ra, dec, radius_deg)
    cache_path = os.path.join(CACHE_DIR, f"sia_{ck}.json")

    # Check local cache first
    if use_cache and os.path.exists(cache_path):"""

new_sig = """async def query_archive_collection(
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
    \"\"\"Execute SIA query with local file caching, bounded exponential backoff with jitter,
    respect for Retry-After headers, and explicit 11-state error taxonomy.
    Records every individual HTTP attempt.
    \"\"\"
    ck = _cache_key(collection, ra, dec, radius_deg)
    cache_path = os.path.join(CACHE_DIR, f"sia_{ck}.json")

    # Check local cache first (bypass if force_refresh is True)
    if use_cache and not force_refresh and os.path.exists(cache_path):"""

if old_sig in code:
    code = code.replace(old_sig, new_sig)
    print("Updated query_archive_collection signature and cache check")

# 4. In query_archive_collection, update 429 status code handling to STATE_ARCHIVE_QUERY_RATE_LIMITED
old_retry_exceeded = """                            last_error_dict = {
                                "status": STATE_ARCHIVE_QUERY_FAILED,
                                "collection": collection,
                                "http_status": response.status_code,
                                "classification": classification,
                                "message": f"Retry-After ({retry_after_val}s) exceeds operational limit ({max_retry_after_sec}s). Request deferred.",
                                "original_exception": "RetryAfterExceeded","""

new_retry_exceeded = """                            last_error_dict = {
                                "status": STATE_ARCHIVE_QUERY_RATE_LIMITED,
                                "collection": collection,
                                "http_status": response.status_code,
                                "classification": classification,
                                "message": f"Retry-After ({retry_after_val}s) exceeds operational limit ({max_retry_after_sec}s). Request deferred.",
                                "original_exception": "RetryAfterExceeded","""

if old_retry_exceeded in code:
    code = code.replace(old_retry_exceeded, new_retry_exceeded)
    print("Updated retry_after exceeded status to RATE_LIMITED")

old_retry_exhausted = """                                last_error_dict = {
                                    "status": STATE_ARCHIVE_QUERY_FAILED,
                                    "collection": collection,
                                    "http_status": response.status_code,
                                    "classification": classification,
                                    "message": f"IRSA SIA HTTP {response.status_code} retry budget exhausted ({attempt + 1} attempts)","""

new_retry_exhausted = """                                last_error_dict = {
                                    "status": STATE_ARCHIVE_QUERY_RATE_LIMITED if response.status_code == 429 else STATE_ARCHIVE_SERVICE_UNAVAILABLE,
                                    "collection": collection,
                                    "http_status": response.status_code,
                                    "classification": classification,
                                    "message": f"IRSA SIA HTTP {response.status_code} retry budget exhausted ({attempt + 1} attempts)","""

if old_retry_exhausted in code:
    code = code.replace(old_retry_exhausted, new_retry_exhausted)
    print("Updated retry exhausted status to RATE_LIMITED/SERVICE_UNAVAILABLE")

# 5. In query_archive_collection, update 5xx server errors to STATE_ARCHIVE_SERVICE_UNAVAILABLE
old_server_err = """                    last_error_dict = {
                        "status": STATE_ARCHIVE_QUERY_FAILED,
                        "collection": collection,
                        "http_status": response.status_code,
                        "classification": classification,
                        "message": f"IRSA SIA returned HTTP {response.status_code}","""

new_server_err = """                    last_error_dict = {
                        "status": STATE_ARCHIVE_SERVICE_UNAVAILABLE,
                        "collection": collection,
                        "http_status": response.status_code,
                        "classification": classification,
                        "message": f"IRSA SIA returned HTTP {response.status_code}","""

if old_server_err in code:
    code = code.replace(old_server_err, new_server_err)
    print("Updated 5xx server error to STATE_ARCHIVE_SERVICE_UNAVAILABLE")

# 6. HTML proxy error to STATE_ARCHIVE_SERVICE_UNAVAILABLE
old_html_err = """                    last_error_dict = {
                        "status": STATE_ARCHIVE_QUERY_FAILED,
                        "collection": collection,
                        "http_status": 502,
                        "classification": classification,
                        "message": "IRSA upstream proxy error (502 / invalid gateway HTML response)","""

new_html_err = """                    last_error_dict = {
                        "status": STATE_ARCHIVE_SERVICE_UNAVAILABLE,
                        "collection": collection,
                        "http_status": 502,
                        "classification": classification,
                        "message": "IRSA upstream proxy error (502 / invalid gateway HTML response)","""

if old_html_err in code:
    code = code.replace(old_html_err, new_html_err)
    print("Updated HTML proxy error to STATE_ARCHIVE_SERVICE_UNAVAILABLE")

# 7. Wrap VOTable parsing with try/except so malformed VOTable never converts to 0 observations!
old_parse_votable = """                # Parse VOTable
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

                if len(rows) > 0:
                    status = "OK"
                    classification = "SUCCESS_RECORDS"
                else:
                    status = STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS
                    classification = "SUCCESS_EMPTY\""""

new_parse_votable = """                # Parse VOTable with strict error guarding
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
                    classification = "SUCCESS_EMPTY\""""

if old_parse_votable in code:
    code = code.replace(old_parse_votable, new_parse_votable)
    print("Updated VOTable parsing and SUCCESS_WITH_RESULTS status")

# 8. Update query_archive_collection_direct signature
old_direct = """    async def query_archive_collection_direct(
        self,
        collection: str,
        ra: float,
        dec: float,
        radius_deg: float,
        timeout_sec: float = 6.0,
        max_retries: int = 2,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        \"\"\"Direct entry point for querying an archive collection with attempt recording.\"\"\"
        return await query_archive_collection(
            collection=collection,
            ra=ra,
            dec=dec,
            radius_deg=radius_deg,
            timeout_sec=timeout_sec,
            max_retries=max_retries,
            use_cache=use_cache,
        )"""

new_direct = """    async def query_archive_collection_direct(
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
        \"\"\"Direct entry point for querying an archive collection with attempt recording.\"\"\"
        return await query_archive_collection(
            collection=collection,
            ra=ra,
            dec=dec,
            radius_deg=radius_deg,
            timeout_sec=timeout_sec,
            max_retries=max_retries,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )"""

if old_direct in code:
    code = code.replace(old_direct, new_direct)
    print("Updated query_archive_collection_direct")

# 9. Update discover_time_series signature and evaluation logic
old_discover_start = """    async def discover_time_series(
        self,
        ra: float,
        dec: float,
        fov_deg: float = 0.5,
        release: str = "all",  # "dr1", "qr3", "both", "all"
        detector: Optional[str] = None,
        date_min: Optional[str] = None,
        date_max: Optional[str] = None,
        timeout_sec: float = 4.0,
    ) -> Dict[str, Any]:
        \"\"\"Discover all matching multi-epoch observations across DR1 and QR3.\"\"\"
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
                use_cache=True,
            )"""

new_discover_start = """    async def discover_time_series(
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
        \"\"\"Discover all matching multi-epoch observations across DR1 and QR3.\"\"\"
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
            )"""

if old_discover_start in code:
    code = code.replace(old_discover_start, new_discover_start)
    print("Updated discover_time_series start and parameters")

old_check_ok = """            if q_res.get("status") == "OK":"""
new_check_ok = """            if q_res.get("status") in ("OK", STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS):"""
if old_check_ok in code:
    code = code.replace(old_check_ok, new_check_ok)
    print("Updated check for successful query records")

# 10. Update state classification at end of discover_time_series
old_state_logic = """        # Check usable count
        usable_count = len(all_records)

        has_failed_queries = any(
            q.get("status") in (
                STATE_ARCHIVE_QUERY_FAILED,
                STATE_ARCHIVE_QUERY_TIMEOUT,
                "TIMEOUT",
                "ARCHIVE_ERROR",
                "PROXY_ERROR",
                "EXCEPTION",
            )
            for q in archive_query_results.values()
        )
        all_empty_success = (
            len(archive_query_results) > 0 and
            all(q.get("status") == STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS for q in archive_query_results.values())
        )

        if usable_count >= 2:
            discovery_state = STATE_SUFFICIENT_TEMPORAL_COVERAGE
            coverage_status = STATE_SUFFICIENT_TEMPORAL_COVERAGE
            temporal_coverage_status = STATE_SUFFICIENT_TEMPORAL_COVERAGE
        elif usable_count == 1:
            discovery_state = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
            coverage_status = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
            temporal_coverage_status = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
        elif usable_count == 0 and has_failed_queries:
            # A 500, 502, timeout, DNS failure or malformed response must never be converted into zero observations.
            # Must remain UNVERIFIED.
            has_timeout = any(
                q.get("status") in (STATE_ARCHIVE_QUERY_TIMEOUT, "TIMEOUT")
                for q in archive_query_results.values()
            )
            discovery_state = STATE_ARCHIVE_QUERY_TIMEOUT if has_timeout else STATE_ARCHIVE_QUERY_FAILED
            coverage_status = STATE_UNVERIFIED
            temporal_coverage_status = STATE_UNVERIFIED
        elif usable_count == 0 and all_empty_success:
            # Archive successfully queried; verified zero matching records in pointing footprint
            discovery_state = STATE_NO_SPATIAL_COVERAGE
            coverage_status = STATE_NO_SPATIAL_COVERAGE
            temporal_coverage_status = STATE_NO_SPATIAL_COVERAGE
        else:
            discovery_state = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
            coverage_status = STATE_INSUFFICIENT_TEMPORAL_COVERAGE
            temporal_coverage_status = STATE_INSUFFICIENT_TEMPORAL_COVERAGE"""

new_state_logic = """        # Check usable count
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
                is_sufficient = False"""

if old_state_logic in code:
    code = code.replace(old_state_logic, new_state_logic)
    print("Updated state logic in discover_time_series")

old_return = """"is_sufficient_for_differencing": usable_count >= 2,"""
new_return = """"is_sufficient_for_differencing": is_sufficient,"""
if old_return in code:
    code = code.replace(old_return, new_return)
    print("Updated is_sufficient_for_differencing")

with open("backend/app/services/spherex_discovery.py", "w", encoding="utf-8") as f:
    f.write(code)

print("spherex_discovery.py successfully patched!")
