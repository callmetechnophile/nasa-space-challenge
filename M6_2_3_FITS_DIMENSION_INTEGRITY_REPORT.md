# M6.2.3 FITS DIMENSION INTEGRITY REPORT
## NASA SPHEREx 3D Temporal Sky Explorer — Dynamic Detector Dimension Enforcement

**Project**: NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone**: M6.2.3 (FITS Dimension Integrity Closure)  
**Execution Timestamp**: 2026-11-15T05:30:00Z  
**Final Status**: **M6_2_3_CONDITIONAL** (Engineering & FITS Dimension Integrity: **PASS**; Astronomical Multi-Epoch Archive Ingestion: **CONDITIONAL**)

---

## 1. Root Cause

In earlier discovery iterations, local observation scanning in `SpherexDiscoveryService.discover_local_observations` (`backend/app/services/spherex_discovery.py`) extracted detector dimensions using silent dictionary fallbacks:
```python
naxis1 = int(h1.get("NAXIS1", 2040))
naxis2 = int(h1.get("NAXIS2", 2040))
```
This design contained several integrity flaws:
1. **Silent Fallback Substitution**: If `NAXIS1` or `NAXIS2` were omitted from the FITS header, the system silently substituted `2040` (and previously `2048`), masking corrupted or non-standard FITS files.
2. **Ambiguous HDU Selection**: The code accessed `hdul[1] if len(hdul) > 1 else hdul[0]` without verifying that the extension was named `IMAGE` or contained valid 2D astronomical image data.
3. **No Array Shape Verification**: The header dimensions were never checked against the actual numpy data array shape `(NAXIS2, NAXIS1)`. If a header claimed $1024 \times 1024$ but the data array was truncated or reshaped, the mismatch was silently ignored.
4. **Non-Positive / Invalid Type Resilience**: Non-positive dimensions ($\le 0$) or non-integer string values were not rejected with structured validation errors.

---

## 2. Production Files Changed

| File Path | Description of Changes |
| :--- | :--- |
| `backend/app/astronomy/fits_dimensions.py` *(NEW)* | Centralized integrity module defining `extract_and_validate_fits_dimensions()` and `FitsDimensionValidationError`. Strictly validates IMAGE HDU presence, positive integer `NAXIS1`/`NAXIS2`, and exact equality with `data.shape == (NAXIS2, NAXIS1)`. |
| `backend/app/services/spherex_discovery.py` | Replaced hardcoded dimension fallback in `discover_local_observations` with `extract_and_validate_fits_dimensions()`. Files failing validation are logged and skipped; valid files have exact dynamic boundaries $[0, \text{NAXIS1}) \times [0, \text{NAXIS2})$ applied to WCS footprint tests. |
| `backend/app/astronomy/spherex_mef_reader.py` | Integrated `extract_and_validate_fits_dimensions()` into `read_spherex_mef_product()`, guaranteeing that IMAGE HDU header cards match array shapes before scientific processing. |
| `backend/app/services/spherex_query.py` | Updated `normalize_observation_record()` to dynamically read validated dimensions directly from local cached FITS files. Eliminated assumed fallbacks for remote records. |
| `backend/app/astronomy/fits_reader.py` | Added array-shape-to-header dimension consistency check in `load_fits_product()`. |
| `tests/test_fits_dimensions_integrity.py` *(NEW)* | Added 9 comprehensive unit tests covering real $2040 \times 2040$ data, $1024 \times 1024$, $800 \times 400$, missing NAXIS, shape mismatches, missing IMAGE HDUs, and non-positive dimensions. |

---

## 3. All Dimension Assumptions Found and Eliminated

An exhaustive scan across `backend/app/` identified the following locations where dimensions were assumed or defaulted:

1. **`backend/app/services/spherex_discovery.py` (Line 605–606)**:
   - *Previous*: `naxis1 = int(h1.get("NAXIS1", 2040))` and `naxis2 = int(h1.get("NAXIS2", 2040))`
   - *Elimination*: Replaced with `naxis1, naxis2, h_img, _ = extract_and_validate_fits_dimensions(hdul, filename=fn)`. Zero fallback numbers.
2. **`backend/app/services/spherex_query.py` (Line 115–116)**:
   - *Previous*: `dim_x = int(raw.get("s_xel1", 2040))` and `dim_y = int(raw.get("s_xel2", 2040))`
   - *Elimination*: Dynamically inspects local cached FITS file via `extract_and_validate_fits_dimensions()`; for remote records, reads `s_xel1`/`s_xel2` directly without substituting 2040 or 2048.
3. **`backend/app/astronomy/spherex_mef_reader.py` (Line 177)**:
   - *Previous*: Checked only `img_data.ndim == 2`, without verifying `NAXIS1` or `NAXIS2` header cards against array shape.
   - *Elimination*: Enforced `extract_and_validate_fits_dimensions()`, raising `ValueError` if header and data array disagree.
4. **`backend/app/astronomy/fits_reader.py` (Line 108)**:
   - *Previous*: Derived `height, width = clean_data.shape` without asserting equality with `header["NAXIS1"]` or `header["NAXIS2"]`.
   - *Elimination*: Enforced that header cards `NAXIS1 == width` and `NAXIS2 == height`.

---

## 4. FITS Header Validation Implementation

The validation logic is standardized in `backend/app/astronomy/fits_dimensions.py`:

```python
def extract_and_validate_fits_dimensions(
    hdul: fits.HDUList,
    filename: str = "<unknown>",
) -> Tuple[int, int, fits.Header, Any]:
    if len(hdul) == 0:
        raise FitsDimensionValidationError(f"FITS file {filename} is empty (0 HDUs)")

    # 1. Identify the correct scientific IMAGE HDU
    image_hdu = None
    if "IMAGE" in hdul:
        image_hdu = hdul["IMAGE"]
    elif len(hdul) == 1 and hdul[0].data is not None and getattr(hdul[0].data, "ndim", 0) == 2:
        image_hdu = hdul[0]
    else:
        for hdu in hdul:
            if isinstance(hdu, (fits.ImageHDU, fits.PrimaryHDU)) and hdu.data is not None:
                if getattr(hdu.data, "ndim", 0) == 2:
                    image_hdu = hdu
                    break

    if image_hdu is None:
        raise FitsDimensionValidationError(f"FITS file {filename} contains no valid 2D scientific IMAGE HDU")

    header = image_hdu.header

    # 2. Read NAXIS1 and NAXIS2 directly from header (no silent fallbacks allowed)
    naxis1_raw = header.get("NAXIS1")
    naxis2_raw = header.get("NAXIS2")

    if naxis1_raw is None or naxis2_raw is None:
        raise FitsDimensionValidationError(
            f"IMAGE HDU in {filename} is missing NAXIS1 or NAXIS2 in header: NAXIS1={naxis1_raw!r}, NAXIS2={naxis2_raw!r}"
        )

    # 3. Validate positive integer types
    try:
        naxis1 = int(naxis1_raw)
        naxis2 = int(naxis2_raw)
    except (ValueError, TypeError) as err:
        raise FitsDimensionValidationError(
            f"IMAGE HDU in {filename} contains non-integer NAXIS dimensions: NAXIS1={naxis1_raw!r}, NAXIS2={naxis2_raw!r} ({err})"
        )

    if naxis1 <= 0 or naxis2 <= 0:
        raise FitsDimensionValidationError(
            f"IMAGE HDU in {filename} contains non-positive dimensions: NAXIS1={naxis1}, NAXIS2={naxis2}"
        )

    # 4. Validate data array presence and shape (shape in numpy is (NAXIS2, NAXIS1))
    if image_hdu.data is None:
        raise FitsDimensionValidationError(f"IMAGE HDU in {filename} contains no data array to validate dimensions against")

    data = image_hdu.data
    if data.ndim != 2:
        raise FitsDimensionValidationError(
            f"IMAGE HDU data in {filename} has unsupported dimensionality: {data.ndim}D with shape {data.shape}, expected 2D"
        )

    expected_shape = (naxis2, naxis1)
    if data.shape != expected_shape:
        raise FitsDimensionValidationError(
            f"IMAGE HDU data shape {data.shape} does not match header dimensions (NAXIS2={naxis2}, NAXIS1={naxis1}) in {filename}"
        )

    return naxis1, naxis2, header, image_hdu
```

---

## 5. Test Results (New & Dedicated Dimension Tests)

Executed via `python -m pytest tests/test_fits_dimensions_integrity.py`:

| Test Name | Tested Scenario | Expected Outcome | Result |
| :--- | :--- | :--- | :---: |
| `test_fits_dimensions_2040x2040_real_calibrated_file` | Real calibrated SPHEREx MEF product (`level2_2025W44`) | Returns $(2040, 2040)$, shape matches | **PASS** |
| `test_fits_dimensions_1024x1024_square` | Standard square $1024 \times 1024$ image array | Returns $(1024, 1024)$ | **PASS** |
| `test_fits_dimensions_800x400_non_square` | Rectangular $800 \times 400$ array (data shape $400 \times 800$) | Returns $(800, 400)$, shape matches | **PASS** |
| `test_fits_dimensions_missing_naxis_metadata` | Header missing `NAXIS1` or `NAXIS2` | Explicit `FitsDimensionValidationError` | **PASS** |
| `test_fits_dimensions_header_data_array_shape_mismatch` | Header says $1024 \times 1024$, data is $300 \times 500$ | Explicit `FitsDimensionValidationError` | **PASS** |
| `test_fits_dimensions_missing_image_hdu` | HDUList with table only (no 2D image) | Explicit `FitsDimensionValidationError` | **PASS** |
| `test_fits_dimensions_invalid_or_non_positive` | $0$, negative ($-50$), or string `"invalid"` | Explicit `FitsDimensionValidationError` | **PASS** |
| `test_discovery_service_uses_dynamic_dimensions_without_fallback` | Local discovery on $800 \times 400$ custom FITS file | Enforces $[0, 800) \times [0, 400)$ WCS footprint | **PASS** |
| `test_discovery_service_skips_malformed_dimensions_cleanly` | Corrupted FITS with shape mismatch in data directory | Skips file cleanly, no unhandled crash | **PASS** |

**Summary**: 9 passed, 0 failed in 4.28s.

---

## 6. Regression Results Across Full Test Suites

Both test suites were re-executed:

| Test Discovery Command | Collected Tests | Passed | Failed | Skipped | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `python -m pytest tests/` | **65** | 65 | 0 | 0 | **100% Pass** |
| `python -m pytest backend/tests/` | **23** | 23 | 0 | 0 | **100% Pass** |
| **Combined Unique Tests** | **88** | **88** | **0** | **0** | **100% Pass Rate** |

### Breakdown by Test File
- `tests/test_fits_dimensions_integrity.py`: **9 tests** *(NEW)*
- `tests/test_spherex_m6_2_reliability.py`: **19 tests**
- `tests/test_spherex_m6_validation.py`: **20 tests**
- `tests/test_spherex_m5_validation.py`: **12 tests**
- `tests/test_spherex_m4_validation.py`: **5 tests**
- `backend/tests/test_coordinates.py`: **5 tests**
- `backend/tests/test_difference_imaging.py`: **3 tests**
- `backend/tests/test_spherex_m5_validation.py`: **13 tests**
- `backend/tests/test_targets.py`: **2 tests**

*Regression Preservation Certified*:
- M1 3D Celestial Sphere & M2 Coordinate Navigation intact.
- M3 WCS projections & M4 FITS ingestion intact.
- M5 Difference imaging, synthetic injection recovery, and candidate extraction intact.
- Approved FITS cryptographic hashes verified unchanged.
- R Draconis canonical proper motion ($+14.82\,\text{mas/yr}$) and propagation ($248.167727^\circ, +66.755006^\circ$) intact.
- WISE 0855 catalog $(176.16, 266.04)$ and propagated $(196.65, 262.79)$ WCS projections inside active array intact.

---

## 7. Production Build Result

Next.js frontend production compilation executed via `npm run build --prefix frontend`:
- **Engine**: Next.js 16.4.6 (Turbopack)
- **Compilation Duration**: 650ms
- **TypeScript Typecheck Duration**: 3.8s (0 errors)
- **Static Page Generation**: 5/5 static pages prerendered (`/`, `/_not-found`, `/explore`) in 1286ms
- **Build Status**: **SUCCESS (Exit Code 0)**

---

## 8. Remaining Limitations

1. **Remote Archive Availability**:
   - Live IPAC SIA queries for SPHEREx DR1 coordinates continue to encounter HTTP 408/502 timeouts during external downtime.
   - The system handles these deterministically and preserves the `UNVERIFIED` discovery state.
2. **WISE 0855 Temporal Multi-Epoch Coverage**:
   - WISE 0855 is confirmed present in local storage in 1 calibrated Level-2 observation (`level2_2025W44`). Because $\ge 2$ epochs are required for difference imaging, it is correctly classified as `INSUFFICIENT_TEMPORAL_COVERAGE`.
   - The 2-epoch equatorial benchmark pair at $(\alpha = 46.844^\circ, \delta = +1.832^\circ)$ remains the primary operational target for multi-epoch temporal subtraction.

---

## 9. Final Milestone Verdict

$$\mathbf{M6\_2\_3\_CONDITIONAL}$$

### Rationale
- **FITS Dimension Integrity & Engineering Closure**: **PASS**.
  - All hardcoded detector dimension fallbacks ($2040, 2048$) have been completely eliminated from production code.
  - Dimensions are strictly extracted from the scientific IMAGE HDU and verified against numpy data array shapes.
  - Missing, invalid, or mismatched headers fail explicitly with structured exceptions.
  - 88 unique tests pass across both suites (100% test pass rate), and the Next.js production build succeeds with 0 errors.
- **Astronomical Multi-Epoch Target Ingestion**: **CONDITIONAL**.
  - Remains conditional on live external network response from IPAC SIA endpoints for the 5 challenge targets.

---
*Report certified by Antigravity Autonomous Verification Engine. Preserved under baseline freeze rules.*
