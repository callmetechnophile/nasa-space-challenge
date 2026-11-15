# M6.2.4 STRICT FITS HDU AND METADATA VALIDATION REPORT

**Project**: NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone**: M6.2.4 (Strict FITS HDU and Metadata Validation)  
**Status**: **M6_2_4_CONDITIONAL** (Engineering Architecture: **PASS** | External Target SPHEREx DR1 Archive Coverage: **CONDITIONAL**)  
**Timestamp**: 2026-11-15T05:42:00Z  

---

## 1. Executive Summary

Milestone M6.2.4 closes the final two structural FITS integrity vulnerabilities identified during M6.2.3 code review:
1. **Deterministic IMAGE HDU Selection**: Eliminates non-deterministic scanning across extensions. Enforces explicit product-aware selection where SPHEREx Multi-Extension FITS (MEF) products strictly require the `'IMAGE'` extension. Fallback to auxiliary extensions (`VARIANCE`, `FLAGS`, `ZODI`, `PSF`, `EPSF`, `WCS-WAVE`) is strictly prohibited. Single-image FITS files permit a 2D primary HDU, while ambiguous multi-image files are rejected with structured candidate context unless explicitly disambiguated.
2. **Strict Integer Dimension Validation**: Enforces exact, non-truncated positive integer validation for `NAXIS1` and `NAXIS2`. Prohibits boolean types (preventing Python `bool` $\to$ `int` coercion), non-integral floats (preventing truncation of values like `1024.9` to `1024`), non-numeric strings, non-positive values ($\le 0$), and numbers exceeding 32-bit signed integer limits ($> 2^{31} - 1$). Confirms underlying data array shape strictly equals `(NAXIS2, NAXIS1)`.

All 10 adversarial unit test cases and 8 edge cases (18 total in `tests/test_fits_dimensions_integrity.py`) passed. Full test suites (`tests/` with 74 tests and `backend/tests/` with 23 tests, totaling 97 unique tests) and the Next.js production build succeeded with zero errors.

---

## 2. Root Cause Analysis of Previous Defects

| Defect Area | Mechanism / Vulnerability | Risk Prevented |
| :--- | :--- | :--- |
| **Python Boolean Subclassing** | In Python, `issubclass(bool, int)` is `True`, so `isinstance(True, int)` evaluates to `True`. A header containing `NAXIS1=True` would silently parse as `1`. | Corrupt or invalid headers with boolean flags are caught immediately rather than creating $1 \times 1$ degenerate footprints. |
| **Float Truncation** | Standard `int(1024.9)` silently truncates to `1024` without warning. | Non-integral dimensions (e.g. fractional binning or corrupted coordinate grids) are rejected. |
| **Auxiliary HDU Leakage** | SPHEREx MEF products package 2D variance, flag arrays, and 2D/3D PSF cubes alongside primary science images. A generic scan for 2D arrays would erroneously pick `VARIANCE` or `FLAGS` if `IMAGE` was missing or unlabelled. | Ensures scientific photometry and WCS coordinate calculations only operate on genuine calibrated science flux images. |
| **Ambiguous Candidate Resolution** | Non-standard FITS files containing multiple 2D extensions (e.g., split channels `CHANNEL_A` and `CHANNEL_B`) could resolve unpredictably depending on traversal order. | Rejection with detailed diagnostic context unless caller supplies explicit `target_hdu`. |

---

## 3. Implemented HDU Selection and Dimension Validation Architecture

The implementation in `backend/app/astronomy/fits_dimensions.py` implements two core functions:

### 3.1 Strict Dimension Parsing (`validate_strict_dimension_value`)
```python
def validate_strict_dimension_value(val: Any, name: str, filename: str) -> int:
    # 1. Reject None / missing
    if val is None:
        raise FitsDimensionValidationError(...)
    # 2. Reject booleans
    if isinstance(val, bool):
        raise FitsDimensionValidationError(...)
    # 3. Reject non-integral floats and decimal strings
    if isinstance(val, (float, np.floating)):
        if not np.isfinite(val) or not float(val).is_integer():
            raise FitsDimensionValidationError(...)
        parsed = int(val)
    elif isinstance(val, str):
        val_str = val.strip()
        if not val_str or "." in val_str:
            raise FitsDimensionValidationError(...)
        parsed = int(val_str)
    # 4. Enforce positive integer within 32-bit limits
    if parsed <= 0 or parsed > MAX_SUPPORTED_FITS_DIMENSION:
        raise FitsDimensionValidationError(...)
    return parsed
```

### 3.2 Product-Aware HDU Selector (`extract_and_validate_fits_dimensions`)
```
                          ┌───────────────────────────┐
                          │ Open FITS HDUList (hdul)  │
                          └─────────────┬─────────────┘
                                        │
                         Target HDU Specified by Caller?
                                ├── Yes ──► Resolve explicitly (by name or index)
                                └── No
                                        │
                                "IMAGE" Extension in HDUList?
                                ├── Yes ──► Deterministically select hdul["IMAGE"]
                                └── No
                                        │
                       Contains SPHEREx Auxiliary Extensions?
                    (VARIANCE, FLAGS, ZODI, PSF, EPSF, WCS-WAVE)
                                ├── Yes ──► REJECT: FitsDimensionValidationError
                                │           (Prohibits auxiliary fallback)
                                └── No
                                        │
                           Scan 2D Image Candidates
                                ├── 0 candidates  ──► REJECT: No valid 2D IMAGE HDU
                                ├── 1 candidate   ──► ACCEPT: Single primary / 2D HDU
                                └── >1 candidates ──► REJECT: Multiple ambiguous candidates
                                                      (Requires target_hdu)
```

---

## 4. Adversarial Test Verification Matrix

Eighteen unit and integration tests are maintained in `tests/test_fits_dimensions_integrity.py`. All ten explicit adversarial test requirements from M6.2.4 were executed and confirmed passing:

| # | Test Case Identifier | Test Scenario Description | Expected Outcome | Actual Result |
| :---: | :--- | :--- | :--- | :---: |
| **1** | `test_fits_dimensions_1_valid_spherex_image_hdu` | Calibrated Level-2 SPHEREx MEF file (`level2_2025W44`) | Extracts $2040 \times 2040$, HDU `'IMAGE'` | **PASS** |
| **2** | `test_fits_dimensions_2_missing_image_with_valid_2d_variance` | SPHEREx product with `PRIMARY` + 2D `VARIANCE` (no `IMAGE`) | Raises `FitsDimensionValidationError`, prohibits fallback | **PASS** |
| **3** | `test_fits_dimensions_3_missing_image_with_valid_2d_psf` | SPHEREx product with `PRIMARY` + 2D `PSF` (no `IMAGE`) | Raises `FitsDimensionValidationError`, prohibits fallback | **PASS** |
| **4** | `test_fits_dimensions_4_single_image_primary` | Single-image primary FITS ($512 \times 1024$) | Resolves `PrimaryHDU` cleanly | **PASS** |
| **5** | `test_fits_dimensions_5_multiple_ambiguous_image_extensions` | Multiple 2D extensions (`CHANNEL_A`, `CHANNEL_B`) | Rejects without `target_hdu`; resolves with `target_hdu` | **PASS** |
| **6** | `test_fits_dimensions_6_floating_point_dimension` | `NAXIS1=1024.9` and string `"1024.9"` | Raises `FitsDimensionValidationError` | **PASS** |
| **7** | `test_fits_dimensions_7_boolean_dimension` | `NAXIS1=True` and `NAXIS2=False` | Raises `FitsDimensionValidationError` | **PASS** |
| **8** | `test_fits_dimensions_8_invalid_string_dimension` | `NAXIS1="abc"`, `""`, and whitespace | Raises `FitsDimensionValidationError` | **PASS** |
| **9** | `test_fits_dimensions_9_zero_and_negative_dimensions` | `NAXIS1=0` and `NAXIS2=-50` | Raises `FitsDimensionValidationError` | **PASS** |
| **10** | `test_fits_dimensions_10_header_data_shape_mismatch` | Header $(1024, 1024)$ vs numpy data $(300, 500)$ | Raises `FitsDimensionValidationError` | **PASS** |
| **11** | `test_fits_dimensions_missing_naxis_metadata` | Omitted `NAXIS1` or `NAXIS2` card | Raises `FitsDimensionValidationError` | **PASS** |
| **12** | `test_fits_dimensions_exceeds_max_supported_bounds` | Dimension exceeding signed 32-bit limit ($> 2^{31} - 1$) | Raises `FitsDimensionValidationError` | **PASS** |
| **13** | `test_fits_dimensions_valid_string_integer` | Clean integer string card (e.g., `"2040"`) | Parses safely to `2040` integer | **PASS** |
| **14** | `test_fits_dimensions_1024x1024_square` | Square $1024 \times 1024$ image | Extracts $(1024, 1024)$ | **PASS** |
| **15** | `test_fits_dimensions_800x400_non_square` | Non-square $800 \times 400$ rectangular image | Extracts $(800, 400)$ | **PASS** |
| **16** | `test_fits_dimensions_missing_image_hdu_no_candidates` | FITS file containing only table HDUs | Raises `FitsDimensionValidationError` | **PASS** |
| **17** | `test_discovery_service_uses_dynamic_dimensions_without_fallback` | Footprint discovery with dynamic $800 \times 400$ product | Computes dynamic WCS boundary without fallback | **PASS** |
| **18** | `test_discovery_service_skips_malformed_dimensions_cleanly` | Discovery scan encountering corrupted dimension FITS | Skips gracefully without crashing or false hits | **PASS** |

---

## 5. Source File Inventory

The following source files were modified or created to fulfill M6.2.4:

| File Path | Description of Changes |
| :--- | :--- |
| `backend/app/astronomy/fits_dimensions.py` | Added `validate_strict_dimension_value` with boolean, non-integral float, empty string, negative, and 32-bit bounds validation. Implemented deterministic product-aware HDU resolution preventing auxiliary fallbacks and ambiguous multi-image selection. |
| `tests/test_fits_dimensions_integrity.py` | Expanded to 18 unit and integration tests covering all 10 M6.2.4 adversarial cases, boundary conditions, dynamic footprint resolution, and discovery error resilience. |

All M1–M5 frozen scientific algorithms (WCS transformation, sub-pixel bicubic resampling, difference imaging, noise variance propagation, and ZOGY-style subtraction) were preserved without modification.

---

## 6. Regression and Production Build Verification

### 6.1 Test Suites Execution
1. **Root Test Suite (`tests/`)**:
   - Command: `python -m pytest tests/`
   - Result: **74 passed, 147 warnings in 23.39s**
   - Failures: **0**
2. **Backend Test Suite (`backend/tests/`)**:
   - Command: `python -m pytest backend/tests/`
   - Result: **23 passed, 1 warning in 7.90s**
   - Failures: **0**
3. **Total Unique Tests**: **97 passed** across all modules with zero regressions.

### 6.2 Frontend Production Build
- Command: `npm run build --prefix frontend`
- Next.js Version: 16.4.6 (Turbopack)
- Routes Prerendered:
  - `/` (Home)
  - `/_not-found` (404 Page)
  - `/explore` (3D Temporal Sky Explorer, interactive player, difference engine)
- TypeScript Verification: **Passed (0 type errors)**
- Build Status: **Success**

---

## 7. Current Project Status and Next Actions

### 7.1 Scientific Status
- **Engineering Quality**: **PASS**. All FITS ingestion, dimension verification, HDU isolation, coordinate propagation, and archive error classification gates are complete and hardened against adversarial inputs.
- **External Target Availability**: **CONDITIONAL**. Live archive discovery against the NASA/IPAC SPHEREx DR1 and QR3 SIA/TAP endpoints for four targets (Barnard's Star, Epsilon Indi B, RW Aurigae, and R Draconis) resulted in HTTP 408 request timeouts and HTTP 502 bad gateway responses. In accordance with strict archive taxonomy, these responses are classified as `UNVERIFIED` (under `ARCHIVE_QUERY_TIMEOUT` and `ARCHIVE_QUERY_FAILED`), rather than misinterpreting network or gateway failures as evidence that the archive contains no data. For WISE 0855, local calibrated SPHEREx MEF footprint evaluation established spatial coverage for one epoch, while remote queries timed out; because multi-epoch temporal discovery strictly requires $\ge 2$ usable epochs, WISE 0855 is classified as `INSUFFICIENT_TEMPORAL_COVERAGE`. No observations are fabricated.

### 7.2 Milestone Gate Verdict
**`M6_2_4_CONDITIONAL`**

Execution is complete and halted in accordance with task instructions.
