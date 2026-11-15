# M6.2.5 — FINAL FITS SELECTOR AND ARCHIVE-STATUS CLOSURE REPORT

**Project**: NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone**: M6.2.5 (Final FITS Selector and Archive-Status Closure)  
**Status**: **M6_2_5_CONDITIONAL** (Engineering Architecture: **PASS** | External Target SPHEREx DR1 Archive Evidence: **CONDITIONAL**)  
**Timestamp**: 2026-11-15T05:52:00Z  

---

## 1. Executive Summary

Milestone M6.2.5 closes the two remaining review findings from M6.2.4 through targeted engineering enhancements:
1. **Enforce SPHEREx IMAGE Selection Under Every Call Path**:
   - Implemented strict product-aware HDU resolution in `backend/app/astronomy/fits_dimensions.py`.
   - SPHEREx Multi-Extension FITS (MEF) products are deterministically detected via product metadata headers (`TELESCOP` or `INSTRUME` containing `"SPHEREX"`) and extension structure (presence of known SPHEREx auxiliary extensions `VARIANCE`, `FLAGS`, `ZODI`, `PSF`, `EPSF`, `WCS-WAVE`).
   - For all SPHEREx MEF products, the exact `'IMAGE'` extension is strictly required as the science image.
   - Auxiliary extensions can **never** be extracted as the science image under any call path.
   - Caller input cannot override SPHEREx product semantics: passing `target_hdu="VARIANCE"` or `target_hdu="PSF"` is rejected with a structured error, even if the requested auxiliary extension exists in the file.
   - Preserves explicit `target_hdu` disambiguation for non-SPHEREx generic multi-image FITS files and preserves valid single-image `PrimaryHDU` handling.
2. **Correct Archive Coverage Reporting**:
   - Replaced imprecise generalizations regarding external target availability with the strict 7-state discovery taxonomy.
   - Confirmed that HTTP 408 (Request Timeout) and HTTP 502 (Bad Gateway) errors from IPAC TAP/SIA services are classified as `UNVERIFIED` (under `ARCHIVE_QUERY_TIMEOUT` / `ARCHIVE_QUERY_FAILED`) and are never conflated with empty results or evidence of absent archive data.
   - Updated the M6.2.4 report Section 7.1 to accurately reflect telemetry evidence.

All test suites and production builds succeeded with zero errors:
- `tests/test_fits_dimensions_integrity.py`: **25 passed, 0 failed** (including all 7 M6.2.5 call-path tests).
- Root test suite (`tests/`): **81 passed, 0 failed, 147 warnings in 24.08s**.
- Backend test suite (`backend/tests/`): **23 passed, 0 failed, 1 warning in 8.83s**.
- **Total Unique Tests**: **104 passed, 0 failed** (0 regressions, no double-counting).
- Frontend production build: **Passed with 0 errors** (Next.js 16.4.6 prerendered all routes).

---

## 2. SPHEREx IMAGE Selection Under Every Call Path

### 2.1 Technical Specification & Architecture

The selection pipeline in `backend/app/astronomy/fits_dimensions.py` implements a deterministic 3-tier hierarchy:

```
                            ┌───────────────────────────────┐
                            │    Open FITS File (hdul)      │
                            └───────────────┬───────────────┘
                                            │
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │  Auxiliary HDU Request Interceptor      │
                       │  target_hdu in {VARIANCE, FLAGS, PSF,   │
                       │  EPSF, ZODI, WCS-WAVE}?                 │
                       └────────────┬────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                 Yes│                               │No
                    ▼                               ▼
       ┌───────────────────────────┐  ┌───────────────────────────┐
       │ REJECT: Auxiliary HDU     │  │ SPHEREx MEF Detection     │
       │ cannot be used as science │  │ (len > 1 and (SPHEREx     │
       │ image under ANY call path │  │  header or aux extensions))│
       └───────────────────────────┘  └─────────────┬─────────────┘
                                                    │
                                    ┌───────────────┴───────────────┐
                                 Yes│                               │No (Generic FITS)
                                    ▼                               ▼
       ┌───────────────────────────────────────────┐  ┌───────────────────────────┐
       │ SPHEREx MEF Product:                      │  │ Generic FITS:             │
       │ 1. "IMAGE" missing? -> REJECT             │  │ 1. target_hdu provided?   │
       │ 2. target_hdu specifies non-IMAGE?        │  │    -> Disambiguate        │
       │    -> REJECT (caller cannot override)     │  │ 2. target_hdu is None?    │
       │ 3. target_hdu is "IMAGE" or None          │  │    - 1 2D candidate: OK   │
       │    -> ACCEPT hdul["IMAGE"]                │  │    - >1 candidates: REJECT│
       └───────────────────────────────────────────┘  │      (ambiguous)          │
                                                      │    - 0 candidates: REJECT │
                                                      └───────────────────────────┘
```

### 2.2 Implemented Logic in `fits_dimensions.py`

```python
# 1. Product Identification
auxiliary_names = {"VARIANCE", "FLAGS", "ZODI", "PSF", "EPSF", "WCS-WAVE"}
present_aux = [h.name for h in hdul if (getattr(h, "name", None) or "").upper() in auxiliary_names]
available_hdus = [getattr(h, "name", None) or f"HDU_{i}" for i, h in enumerate(hdul)]

telescop = str(hdul[0].header.get("TELESCOP", "")).upper() if len(hdul) > 0 and hasattr(hdul[0], "header") else ""
instrume = str(hdul[0].header.get("INSTRUME", "")).upper() if len(hdul) > 0 and hasattr(hdul[0], "header") else ""
is_spherex_mef = (len(hdul) > 1) and (bool(present_aux) or ("SPHEREX" in telescop) or ("SPHEREX" in instrume))

# 2. Universal Auxiliary Request Rejection
is_aux_request = False
if isinstance(target_hdu, str) and target_hdu.strip().upper() in auxiliary_names:
    is_aux_request = True
elif isinstance(target_hdu, int) and 0 <= target_hdu < len(hdul):
    if (getattr(hdul[target_hdu], "name", None) or "").upper() in auxiliary_names:
        is_aux_request = True

if is_aux_request:
    product_type = "SPHEREx MEF product" if is_spherex_mef else "Generic FITS product"
    raise FitsDimensionValidationError(
        f"{product_type} {filename}: attempting to use auxiliary extension {target_hdu!r} as the science image is strictly prohibited. "
        f"Requested HDU: {target_hdu!r}, available HDUs: {available_hdus}."
    )

# 3. SPHEREx MEF Enforcement
if is_spherex_mef:
    if "IMAGE" not in hdul:
        found_str = ", ".join(present_aux) if present_aux else "none"
        raise FitsDimensionValidationError(
            f"SPHEREx MEF product {filename} is missing required 'IMAGE' extension "
            f"(requested_hdu={target_hdu!r}, available_hdus={available_hdus}); "
            f"fallback to auxiliary extensions ({found_str}) is strictly prohibited."
        )

    if target_hdu is not None:
        is_valid_image_selection = False
        if isinstance(target_hdu, str) and target_hdu.strip().upper() == "IMAGE":
            is_valid_image_selection = True
        elif isinstance(target_hdu, int) and 0 <= target_hdu < len(hdul):
            if (getattr(hdul[target_hdu], "name", "") or "").upper() == "IMAGE":
                is_valid_image_selection = True

        if not is_valid_image_selection:
            raise FitsDimensionValidationError(
                f"SPHEREx MEF product {filename} requires the exact 'IMAGE' extension as the science image "
                f"(requested_hdu={target_hdu!r}, available_hdus={available_hdus}). "
                "Overriding SPHEREx product semantics is strictly prohibited."
            )

    image_hdu = hdul["IMAGE"]
```

---

## 3. Seven M6.2.5 Selector & Call-Path Enforcement Tests

The test suite in `tests/test_fits_dimensions_integrity.py` incorporates dedicated test methods verifying all seven required call paths:

| # | Test Function | Call Scenario | Expected Behavior | Result |
| :---: | :--- | :--- | :--- | :---: |
| **1** | `test_m6_2_5_1_spherex_mef_with_valid_image` | Calibrated SPHEREx MEF (`target_hdu=None`) | Resolves `'IMAGE'` extension ($2040 \times 2040$) | **PASS** |
| **2** | `test_m6_2_5_2_spherex_mef_missing_image_explicit_target_variance` | SPHEREx MEF without `IMAGE`, explicit `target_hdu="VARIANCE"` | Rejects auxiliary HDU request with structured error | **PASS** |
| **3** | `test_m6_2_5_3_spherex_mef_missing_image_explicit_target_psf` | SPHEREx MEF without `IMAGE`, explicit `target_hdu="PSF"` | Rejects auxiliary HDU request with structured error | **PASS** |
| **4** | `test_m6_2_5_4_spherex_mef_with_image_explicit_target_image` | SPHEREx MEF with `IMAGE`: `target_hdu="IMAGE"` vs `target_hdu="VARIANCE"` | Resolves with `"IMAGE"`; strictly rejects `"VARIANCE"` | **PASS** |
| **5** | `test_m6_2_5_5_generic_multi_image_explicit_disambiguation` | Generic FITS with `CHANNEL_A` ($200 \times 200$) & `CHANNEL_B` ($400 \times 400$) | Resolves by name (`"CHANNEL_A"`) or index (`1`) | **PASS** |
| **6** | `test_m6_2_5_6_generic_ambiguous_multi_image_without_disambiguation` | Generic FITS with multiple channels, `target_hdu=None` | Rejects ambiguous extensions, lists candidates | **PASS** |
| **7** | `test_m6_2_5_7_valid_single_image_primary_hdu` | Generic FITS with single 2D Primary HDU ($512 \times 512$) | Resolves `PrimaryHDU` cleanly | **PASS** |

---

## 4. Rigorous Archive Coverage Taxonomy & Actual Telemetry

### 4.1 Canonical Archive Taxonomy

To prevent misinterpreting network or gateway issues as scientific conclusions about archive contents, the system enforces the following distinct discovery states:

| State Identifier | Definition | Correct Usage | Prohibited Usage |
| :--- | :--- | :--- | :--- |
| `ARCHIVE_QUERY_FAILED` | HTTP request failed with an unrecoverable error (e.g. HTTP 500, DNS resolution failure, malformed response). | Remote service failure. | Must NOT be reported as "target has no data". |
| `ARCHIVE_QUERY_TIMEOUT` | HTTP request timed out (e.g. HTTP 408, socket connect timeout, read timeout). | Network/gateway timeout. | Must NOT be reported as "archive searched and empty". |
| `ARCHIVE_QUERY_SUCCESS_NO_RESULTS` | Request succeeded (HTTP 200), parsed VOTable response contains 0 matching observation records. | Spatial cone contains no pointing centers. | Must NOT be used when query timed out or failed. |
| `NO_SPATIAL_COVERAGE` | Query succeeded with candidate records, but rigorous Astropy WCS polygon intersection confirmed coordinate is outside all detector footprints. | Verified non-intersection with active detector pixels. | Must NOT be inferred from pointing centers alone. |
| `INSUFFICIENT_TEMPORAL_COVERAGE` | Usable observations exist on active detector array, but fewer than 2 valid epochs are available. | Single epoch available (e.g. WISE 0855 locally). | Cannot support temporal animation or difference imaging. |
| `SUFFICIENT_TEMPORAL_COVERAGE` | At least 2 usable, scientifically compatible epochs exist with valid spatial coverage. | Full multi-epoch time series enabled. | Cannot be declared without verified WCS overlap. |
| `UNVERIFIED` | Available evidence cannot establish coverage due to query failure or timeout. | Default state when queries cannot be completed. | Must NOT be collapsed into zero coverage. |

### 4.2 Actual Five-Target Evidence Summary

| Target Name | Remote SIA/TAP Query Status | Local Calibrated SPHEREx Data | Usable Epochs | Target Discovery Classification | Scientific Assessment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Barnard's Star** | HTTP 408 (Request Timeout) | None | 0 | `UNVERIFIED` | Remote query timed out; external archive coverage cannot be established from failed network requests. |
| **Epsilon Indi B** | HTTP 502 / HTTP 408 | None | 0 | `UNVERIFIED` | Gateway failure / timeout; coverage cannot be determined without successful archive response. |
| **WISE 0855** | HTTP 408 (Request Timeout) | 1 Calibrated MEF Product (`level2_2025W44`) | 1 | `INSUFFICIENT_TEMPORAL_COVERAGE` | Target lies inside active detector array at $(176.2, 266.0)$ catalog / $(196.6, 262.8)$ propagated; 1 epoch verified, 2 required for temporal analysis. |
| **RW Aurigae** | HTTP 408 (Request Timeout) | None | 0 | `UNVERIFIED` | Remote query timed out; coverage unverified. |
| **R Draconis** | HTTP 502 / HTTP 408 | None | 0 | `UNVERIFIED` | Gateway failure / timeout; coverage unverified. |

---

## 5. Regression Verification and Evidence

### 5.1 Test Execution Telemetry

1. **Dedicated FITS Dimension Integrity Test Suite**:
   - Command: `python -m pytest tests/test_fits_dimensions_integrity.py -v`
   - Exit Code: **0**
   - Results: **25 passed, 0 failed, 0 skipped** (5.08s)
2. **Full Root Test Suite (`tests/`)**:
   - Command: `python -m pytest tests/`
   - Exit Code: **0**
   - Results: **81 passed, 0 failed, 147 warnings** (24.08s)
   - Breakdown:
     - `tests/test_fits_dimensions_integrity.py`: 25 passed
     - `tests/test_spherex_m4_validation.py`: 5 passed
     - `tests/test_spherex_m5_validation.py`: 12 passed
     - `tests/test_spherex_m6_2_reliability.py`: 19 passed
     - `tests/test_spherex_m6_validation.py`: 20 passed
3. **Full Backend Test Suite (`backend/tests/`)**:
   - Command: `python -m pytest backend/tests/`
   - Exit Code: **0**
   - Results: **23 passed, 0 failed, 1 warning** (8.83s)
   - Breakdown:
     - `backend/tests/test_coordinates.py`: 5 passed
     - `backend/tests/test_difference_imaging.py`: 3 passed
     - `backend/tests/test_spherex_m5_validation.py`: 13 passed
     - `backend/tests/test_targets.py`: 2 passed
4. **Total Unique Tests**: **104 unique tests executed and passed** (zero duplicate counts across the two distinct suites).
5. **Frontend Production Build**:
   - Command: `npm run build --prefix frontend`
   - Next.js Version: 16.4.6 (Turbopack)
   - Exit Code: **0**
   - Prerendered Routes: `/`, `/_not-found`, `/explore`
   - TypeScript Compilation: **0 errors**

### 5.2 Cryptographic File Hashes (Approved QR3 Baseline)

The approved SPHEREx QR3/QR2 baseline FITS files remain unaltered:
- `data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits`:  
  SHA-256: `36b330b5ed45161383aedc7e9199619c6ca1873e213a5fdc8ff027274190caf6` (71,634,240 bytes)
- `data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits`:  
  SHA-256: `b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1` (65,488,320 bytes)
- `data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits`:  
  SHA-256: `60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e` (65,488,320 bytes)

### 5.3 Inventory of Modified Files

| Modified File | Summary of Changes |
| :--- | :--- |
| `backend/app/astronomy/fits_dimensions.py` | Added universal auxiliary HDU request interceptor (`is_aux_request`); enforced SPHEREx product semantics preventing caller overrides; preserved generic FITS disambiguation and single-image PrimaryHDU support. |
| `tests/test_fits_dimensions_integrity.py` | Expanded from 18 to 25 unit tests to include all 7 M6.2.5 selector call-path scenarios. |
| `d:\nasa\M6_2_4_STRICT_FITS_VALIDATION_REPORT.md` | Updated Section 7.1 to align scientific status reporting with actual HTTP 408/502 telemetry evidence. |

---

## 6. Milestone Gate Verdict

**`M6_2_5_CONDITIONAL`**

- **Engineering Architecture & FITS Integrity**: **PASS**. The selector strictly enforces SPHEREx product semantics under every call path, rejects auxiliary extensions as science images, enforces strict integer dimension validation, and preserves generic FITS and single-image handling.
- **Scientific Archive Coverage**: **CONDITIONAL**. Live IPAC queries returned HTTP 408/502 timeouts for four targets (`UNVERIFIED`), while WISE 0855 possesses 1 verified local calibrated epoch (`INSUFFICIENT_TEMPORAL_COVERAGE`). No observations are fabricated.

Execution is complete and halted in accordance with task instructions.
