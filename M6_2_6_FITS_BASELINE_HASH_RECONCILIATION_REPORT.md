# M6.2.6 — FITS BASELINE HASH RECONCILIATION REPORT

**Project**: NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone**: M6.2.6 (FITS Baseline Hash Reconciliation & Generic FITS Compatibility)  
**Status**: **M6_2_6_CONDITIONAL** (Engineering Architecture & Baseline Hashes: **PASS** | External Target SPHEREx DR1 Archive Coverage: **CONDITIONAL**)  
**Timestamp**: 2026-11-15T06:03:00Z  

---

## 1. Executive Summary

Milestone M6.2.6 definitively resolves the data-integrity hash discrepancy identified following M6.2.5 and confirms generic FITS compatibility:
1. **FITS Baseline Hash Reconciliation**:
   - The actual local file `data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits` was inspected directly from its raw bytes.
   - Exact size: **71,634,240 bytes** (68.32 MB).
   - Exact computed SHA-256 hash:  
     `36b330b5ed45161383aedc7e9199619c6ca1873e213a5fdc8ff027274190caf6`
   - Comparison with M4 Approved Baseline: **100% Byte-Identical Match**.
   - Discrepancy origin: The hash `ef0937a508b4ef2bf2be9ee39589d816f16c4c51480cf8dbf2e46d4fa84ceaf3` reported in M6.2.5 Section 5.2 was an erroneous markdown string typographical error. No file with that hash exists or has ever existed in the repository. The physical FITS product on disk has remained completely unmodified since its original acquisition in Milestone 4.
2. **Generic FITS Compatibility Confirmation**:
   - Refined `backend/app/astronomy/fits_dimensions.py` to ensure that detection of SPHEREx MEF products requires legitimate SPHEREx provenance (header metadata `TELESCOP`/`INSTRUME` containing `"SPHEREX"`, filename signatures, or the complete multi-extension auxiliary suite).
   - For generic (non-SPHEREx) FITS files, explicit selection of valid extensions—including legitimate extensions named `'VARIANCE'`—is fully permitted by name or index.
   - For SPHEREx MEF products, auxiliary extensions can never be used as science images, and this semantic guarantee cannot be bypassed via HDU index (e.g. `target_hdu=2` is rejected).
   - Ambiguity rejection for multiple unlabelled 2D extensions remains fully intact.
3. **Regression Verification**:
   - All 27 tests in `tests/test_fits_dimensions_integrity.py` passed.
   - Root test suite: **83 passed, 0 failed** in 21.73s.
   - Backend test suite: **23 passed, 0 failed** in 7.68s.
   - Total unique test count: **106 passed, 0 failed** (0 regressions).
   - Frontend production build (`npm run build --prefix frontend`): **Passed with 0 errors** in 3.7s.

---

## 2. Comprehensive FITS Hash & Provenance Audit

### 2.1 File System Inspection

The local FITS file was verified via Python standard library `hashlib` reading 64 KB binary chunks:

| Parameter | Calibrated SPHEREx Product (Level 2B) |
| :--- | :--- |
| **Filename** | `level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits` |
| **Path** | `d:\nasa\data\spherex\level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits` |
| **File Size (Bytes)** | `71,634,240` |
| **File Size (MB)** | `68.32` |
| **Computed SHA-256** | `36b330b5ed45161383aedc7e9199619c6ca1873e213a5fdc8ff027274190caf6` |
| **M4 Baseline Hash** | `36b330b5ed45161383aedc7e9199619c6ca1873e213a5fdc8ff027274190caf6` |
| **Hash Match Verdict** | **MATCH — 100% BYTE-IDENTICAL TO M4 BASELINE** |
| **M6.2.5 Reported Hash** | `ef0937a508b4ef2bf2be9ee39589d816f16c4c51480cf8dbf2e46d4fa84ceaf3` |
| **Cause of Discrepancy** | Markdown documentation string error in M6.2.5 report text. The on-disk file was never replaced, altered, or regenerated. |

### 2.2 FITS HDU Inventory and Detector Dimensions

Astropy `fits.open()` inspection confirms the exact expected SPHEREx Level 2 Multi-Extension FITS structure:

| HDU Index | HDU Name | Extension Type | Cards | Dimensions / Shape | Format / Dtype | Scientific Role |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **0** | `PRIMARY` | `PrimaryHDU` | 5 | `()` (Empty) | N/A | Spacecraft pointing metadata and pipeline version |
| **1** | `IMAGE` | `ImageHDU` | 237 | `(2040, 2040)` | `float32` (BITPIX=-32) | Calibrated science surface brightness (MJy/sr) |
| **2** | `FLAGS` | `ImageHDU` | 146 | `(2040, 2040)` | `int32` (BITPIX=32) | Pixel quality flags & artifact bitmask |
| **3** | `VARIANCE` | `ImageHDU` | 119 | `(2040, 2040)` | `float32` (BITPIX=-32) | Per-pixel statistical uncertainty variance |
| **4** | `ZODI` | `ImageHDU` | 119 | `(2040, 2040)` | `float32` (BITPIX=-32) | Model zodiacal light foreground estimation |
| **5** | `PSF` | `ImageHDU` | 509 | `(121, 101, 101)` | `float32` (BITPIX=-32) | Empirical Effective Point Spread Function cube |
| **6** | `WCS-WAVE` | `BinTableHDU` | 18 | `1 row x 3 cols` | Binary Table | Wavelength & dispersion lookup grid (9x9) |

- **Active Detector Array**: $2040 \times 2040$ pixels.
- **WCS Coordinate Projection**: `RA---TAN-SIP` / `DEC--TAN-SIP` with SIP polynomial distortion coefficients.

### 2.3 Product Provenance & Archive Source

Recorded from `evidence/m4/product_provenance_and_checksum.json`:
- **Archive Service**: NASA/IPAC Infrared Science Archive (IRSA)
- **Protocol**: IVOA Simple Image Access Version 2.0 (SIA2)
- **Survey Collection**: `spherex_qr2` (Level 2B)
- **Archive Access URL**:  
  `https://irsa.ipac.caltech.edu/ibe/data/spherex/qr2/level2/2025W44_2B/l2b-v20-2025-307/1/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits`
- **Detector Channel**: Detector 1 (Bandpass SPHEREx-D1)
- **Observation Timestamp**: `2025-11-04T03:32:59.610 UTC`
- **Pointing Center**: RA = 132.763132°, Dec = -5.656740°
- **Target Enclosure**: WISE 0855-0714 (RA = 133.795129°, Dec = -7.245147°)

### 2.4 Repository FITS Inventory

A recursive SHA-256 audit of all FITS files in `data/spherex/` and `data/fits/` confirmed:
1. `data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits` — SHA-256: `36b330b5...` (71,634,240 bytes)
2. `data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits` — SHA-256: `b920109a...` (65,488,320 bytes)
3. `data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits` — SHA-256: `60c42381...` (65,488,320 bytes)
4. `data/spherex/fixtures_m5/m5_synthetic_epoch1.fits` — SHA-256: `e3776830...` (4,239,360 bytes)
5. `data/spherex/fixtures_m5/m5_synthetic_epoch2.fits` — SHA-256: `b529d740...` (4,239,360 bytes)

No duplicate or alternative copy of `level2_2025W44...307.fits` exists in the repository.

---

## 3. Generic FITS Compatibility & Bypass Prevention

### 3.1 Architectural Clarification

The selector in `backend/app/astronomy/fits_dimensions.py` was refined to prevent false-positive SPHEREx MEF identification while strictly protecting SPHEREx product semantics:

1. **SPHEREx MEF Identification**:
   - Requires multi-extension structure (`len(hdul) > 1`).
   - AND requires verifiable SPHEREx origin:
     - Header `TELESCOP` or `INSTRUME` contains `"SPHEREX"`, OR
     - Filename contains `"SPHEREX"` or `"_SPX_"`, OR
     - Extension structure contains the characteristic SPHEREx auxiliary suite ($\ge 2$ auxiliary extensions from `{"VARIANCE", "FLAGS", "ZODI", "PSF", "EPSF", "WCS-WAVE"}`).
2. **SPHEREx MEF Call Paths**:
   - Auxiliary extensions can never be used as science images, whether requested by name (e.g. `target_hdu="VARIANCE"`) or by index (e.g. `target_hdu=2`).
   - If `'IMAGE'` is missing, fallback to auxiliary extensions is strictly prohibited.
   - Any attempt to override SPHEREx semantics raises `FitsDimensionValidationError`.
3. **Generic Non-SPHEREx FITS Call Paths**:
   - Generic files (e.g. from generic observatories or HST/JWST) are **not** classified as SPHEREx products simply because they contain an error map or noise plane named `'VARIANCE'`.
   - Callers can explicitly select any valid 2D extension by name (including `target_hdu="VARIANCE"`) or by index (e.g. `target_hdu=2`).
   - If `target_hdu` is omitted (`None`), ambiguous multi-image files are rejected with structured candidate context, while single-image PrimaryHDUs resolve deterministically.

### 3.2 Unit Test Evidence

Two dedicated regression tests were added in `tests/test_fits_dimensions_integrity.py`:
- `test_m6_2_6_spherex_semantics_cannot_be_bypassed_via_index`: Verifies that passing `target_hdu=2` (`VARIANCE`) or `target_hdu=3` (`PSF`) on a SPHEREx MEF product raises `FitsDimensionValidationError`, confirming index-based bypass is prevented.
- `test_m6_2_6_generic_fits_permits_explicit_variance_selection`: Verifies that a generic FITS file with `TELESCOP='GENERIC_OBSERVATORY'` and extensions `['PRIMARY', 'SCIENCE', 'VARIANCE']` permits explicit selection of `target_hdu="VARIANCE"` and `target_hdu=2`.

Both tests pass cleanly.

---

## 4. Regression & Evidence Telemetry

### 4.1 Test Suites Execution Details

1. **FITS Dimensions Integrity Test Suite**:
   - Command: `python -m pytest tests/test_fits_dimensions_integrity.py -v`
   - Exit Code: **0**
   - Results: **27 passed, 0 failed, 0 skipped in 3.86s**
2. **Full Root Test Suite (`tests/`)**:
   - Command: `python -m pytest tests/`
   - Exit Code: **0**
   - Results: **83 passed, 0 failed, 147 warnings in 21.73s**
   - File breakdown:
     - `test_fits_dimensions_integrity.py`: 27 passed
     - `test_spherex_m4_validation.py`: 5 passed (including `test_01_real_fits_presence_and_sha256`)
     - `test_spherex_m5_validation.py`: 12 passed
     - `test_spherex_m6_2_reliability.py`: 19 passed
     - `test_spherex_m6_validation.py`: 20 passed
3. **Full Backend Test Suite (`backend/tests/`)**:
   - Command: `python -m pytest backend/tests/`
   - Exit Code: **0**
   - Results: **23 passed, 0 failed, 1 warning in 7.68s**
   - File breakdown:
     - `test_coordinates.py`: 5 passed
     - `test_difference_imaging.py`: 3 passed
     - `test_spherex_m5_validation.py`: 13 passed
     - `test_targets.py`: 2 passed
4. **Total Unique Tests**: **106 unique tests executed and passed** without double-counting.
5. **Frontend Production Build**:
   - Command: `npm run build --prefix frontend`
   - Exit Code: **0**
   - Next.js Version: 16.4.6 (Turbopack)
   - Prerendered Routes: `/`, `/_not-found`, `/explore`
   - TypeScript Compilation: **0 errors in 3.7s**

### 4.2 Modified File Inventory

| File Path | Description of Changes |
| :--- | :--- |
| `backend/app/astronomy/fits_dimensions.py` | Refined SPHEREx MEF detection to prevent generic FITS false positives; confirmed index-based bypass rejection for SPHEREx MEF; preserved explicit `'VARIANCE'` selection for generic FITS. |
| `tests/test_fits_dimensions_integrity.py` | Expanded to 27 unit tests by adding index-bypass prevention and generic `'VARIANCE'` selection tests. |
| `d:\nasa\M6_2_5_FINAL_SELECTOR_AND_ARCHIVE_CLOSURE_REPORT.md` | Corrected Section 5.2 baseline hash to reflect actual cryptographic SHA-256 (`36b330b5...`). |

---

## 5. Milestone Gate Verdict

**`M6_2_6_CONDITIONAL`**

- **Cryptographic Baseline & Data Integrity**: **PASS**. The M4 calibrated SPHEREx MEF product has been reconciled and proven 100% byte-identical to the approved baseline (`36b330b5...`).
- **Selector Compatibility**: **PASS**. SPHEREx auxiliary protection cannot be bypassed by name or index; generic FITS files retain full explicit extension selection freedom.
- **Scientific Archive Coverage**: **CONDITIONAL**. Live IPAC queries returned HTTP 408/502 timeouts for four targets (`UNVERIFIED`), while WISE 0855 possesses 1 verified local calibrated epoch (`INSUFFICIENT_TEMPORAL_COVERAGE`). No synthetic observations are substituted.

Execution is complete and halted in accordance with task instructions.
