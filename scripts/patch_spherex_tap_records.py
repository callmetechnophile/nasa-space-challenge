"""Update spherex_discovery.py and spherex_tap.py to implement the strict 11-state taxonomy."""
import re

# 1. Patch spherex_tap.py
with open("backend/app/services/spherex_tap.py", "r", encoding="utf-8") as f:
    tap_content = f.read()

# Make sure _parse_votable_records returns error and query_spatial_tap handles it
old_tap_parse_call = """                    if resp.status_code == 200:
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
                        }"""

new_tap_parse_call = """                    if resp.status_code == 200:
                        records, parse_err = self._parse_votable_records(resp.content, ra_deg, dec_deg)
                        if parse_err:
                            attempt_meta["error"] = f"Malformed VOTable: {parse_err}"
                            last_error = attempt_meta["error"]
                            attempts_log.append(attempt_meta)
                            return {
                                "status": "error",
                                "http_status": 200,
                                "classification": STATE_ARCHIVE_QUERY_FAILED,
                                "query_sql": query_sql,
                                "records_count": 0,
                                "records": [],
                                "attempts": attempts_log,
                                "error": last_error,
                            }

                        attempts_log.append(attempt_meta)
                        if len(records) == 0:
                            classification = STATE_ARCHIVE_QUERY_SUCCESS_NO_RESULTS
                        else:
                            classification = STATE_ARCHIVE_QUERY_SUCCESS_WITH_RESULTS

                        return {
                            "status": "success",
                            "http_status": 200,
                            "classification": classification,
                            "query_sql": query_sql,
                            "records_count": len(records),
                            "records": records,
                            "attempts": attempts_log,
                            "error": None,
                        }"""

if old_tap_parse_call in tap_content:
    tap_content = tap_content.replace(old_tap_parse_call, new_tap_parse_call)
    print("Replaced tap parse call in spherex_tap.py")

old_parse_def = """    def _parse_votable_records(
        self,
        votable_bytes: bytes,
        target_ra: float,
        target_dec: float,
    ) -> List[Dict[str, Any]]:
        \"\"\"Parse VOTable XML from TAP service into structured observation records.\"\"\"
        records: List[Dict[str, Any]] = []
        try:"""

new_parse_def = """    def _parse_votable_records(
        self,
        votable_bytes: bytes,
        target_ra: float,
        target_dec: float,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        \"\"\"Parse VOTable XML from TAP service into structured observation records.\"\"\"
        records: List[Dict[str, Any]] = []
        try:"""

if old_parse_def in tap_content:
    tap_content = tap_content.replace(old_parse_def, new_parse_def)

# Return tuple from _parse_votable_records
old_return_block = """        except Exception as exc:
            logger.warning("Error parsing TAP VOTable: %s", exc)

        return records"""

new_return_block = """        except Exception as exc:
            logger.warning("Error parsing TAP VOTable: %s", exc)
            return [], str(exc)

        return records, None"""

if old_return_block in tap_content:
    tap_content = tap_content.replace(old_return_block, new_return_block)
    print("Updated _parse_votable_records return signature in spherex_tap.py")

with open("backend/app/services/spherex_tap.py", "w", encoding="utf-8") as f:
    f.write(tap_content)

print("spherex_tap.py patched successfully.")
