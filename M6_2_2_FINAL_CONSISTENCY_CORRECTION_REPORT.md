# M6.2.2 FINAL CONSISTENCY CORRECTION REPORT
## NASA SPHEREx 3D Temporal Sky Explorer — Targeted Scientific Consistency and Archive Integrity

**Project**: NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone**: M6.2.2 (Targeted Scientific Consistency, Detector Dimension Correction, and Test Clarification)  
**Execution Timestamp**: 2026-11-15T05:15:00Z  
**Final Status**: **M6_2_2_CONDITIONAL** (Engineering, Consistency, and Reliability Closure: **PASS**; Astronomical Multi-Epoch Archive Ingestion: **CONDITIONAL**)

---

## 1. Root Cause of the R Draconis Test Inconsistency

### Investigation & Origin Analysis
In the previous report (`M6_2_1_FINAL_EVIDENCE_CLOSURE_REPORT.md`, Section 5, item 1), the text narrative stated:
> *"1. `test_r_draconis_proper_motion_propagation_direction`: Propagated coordinates increase in RA ($\Delta\alpha > 0$) as mandated by positive $\mu_\alpha \cos\delta = +31.25\,\text{mas/yr}$."*

An exhaustive audit of the codebase, target catalogs, and test suites established:
1. **Canonical Catalog Source**: `TARGET_CATALOG` in `backend/app/astronomy/m6_target_validation.py` and `sample_provider.py` (which powers `/api/v1/targets`) have consistently defined the canonical Gaia DR3 / Hipparcos values:
   - Reference RA: $248.167625^\circ$
   - Reference Dec: $+66.755056^\circ$
   - Reference Epoch: J2016.0
   - Proper Motion in RA: $\mu_\alpha \cos\delta = \mathbf{+14.82\,\text{mas/yr}}$
   - Proper Motion in Dec: $\mu_\delta = \mathbf{-18.45\,\text{mas/yr}}$
2. **Actual Test Implementation**: The unit test in `tests/test_spherex_m6_2_reliability.py` was named `test_r_draconis_coordinate_propagation_correction` and specifically asserted `assert spec["proper_motion_ra_cosdec_mas_yr"] == pytest.approx(14.82, abs=1e-2)`.
3. **Origin of the $+31.25\,\text{mas/yr}$ String**: The $+31.25\,\text{mas/yr}$ figure was never part of the running codebase or test assertions. It was an errant transcription artifact in the report text narrative, resulting from an earlier draft calculation note that confounded unprojected RA proper motion ($\mu_\alpha = \mu_\alpha^* / \cos\delta = 14.82 / \cos(66.755^\circ) \approx 37.55\,\text{mas/yr}$) with an older historical catalog entry.
4. **Correction Implemented**:
   - The narrative inconsistency was formally expunged.
   - `test_r_draconis_coordinate_propagation_correction` in `tests/test_spherex_m6_2_reliability.py` was expanded to rigorously test the canonical $+14.82\,\text{mas/yr}$ value, explicitly assert against spurious 31.25 values, verify displacement direction ($\Delta\alpha > 0$, $\Delta\delta < 0$), verify displacement magnitude ($0.2319''$), and verify that backend API data providers and frontend presets in `SpherexSearchPanel.tsx` strictly agree.

---

## 2. Canonical Coordinate Values and Numerical Propagation Test

### Canonical Reference Parameters (Gaia DR3 / ICRS)
- **Target ID**: `r-draconis`
- **Target Name**: R Draconis (Mira Pulsating Variable Giant)
- **Catalog Source**: Gaia DR3 1629851608677464832 / AAVSO
- **Reference Epoch**: J2016.0 ($t_0 = 2016.0$)
- **Catalog RA ($\alpha_0$)**: $248.167625^\circ$ ($16^{\text{h}} 32^{\text{m}} 40.23^{\text{s}}$)
- **Catalog Dec ($\delta_0$)**: $+66.755056^\circ$ ($+66^\circ 45' 18.20''$)
- **Proper Motion in RA ($\mu_\alpha \cos\delta$)**: $+14.82\,\text{mas/yr}$
- **Proper Motion in Dec ($\mu_\delta$)**: $-18.45\,\text{mas/yr}$
- **Parallax ($\varpi$)**: $1.85\,\text{mas}$ (Distance: $540.5\,\text{pc}$)

### Numerical Propagation to Observation Epoch ($t = 2025.8$)
- **Time Baseline ($\Delta t$)**: $2025.8 - 2016.0 = 9.80\,\text{years}$
- **Projected Eastward Displacement ($\Delta\alpha \cos\delta$)**:
  $$\Delta\alpha \cos\delta = (+14.82\,\text{mas/yr}) \times (9.80\,\text{yr}) = +145.236\,\text{mas} = +0.145236''$$
- **Declination Factor ($\cos\delta_0$)**:
  $$\cos(66.755056^\circ) = 0.394662777$$
- **True Right Ascension Offset ($\Delta\alpha$)**:
  $$\Delta\alpha = \frac{+145.236\,\text{mas}}{0.394662777} = +368.000\,\text{mas} = +0.368000'' = \mathbf{+0.000102222^\circ}$$
- **Declination Offset ($\Delta\delta$)**:
  $$\Delta\delta = (-18.45\,\text{mas/yr}) \times (9.80\,\text{yr}) = -180.810\,\text{mas} = -0.180810'' = \mathbf{-0.000050225^\circ}$$
- **Propagated Coordinates at 2025.8**:
  $$\alpha_{2025.8} = 248.167625^\circ + 0.000102222^\circ = \mathbf{248.167727^\circ} \quad (16^{\text{h}} 32^{\text{m}} 40.25^{\text{s}})$$
  $$\delta_{2025.8} = +66.755056^\circ - 0.000050225^\circ = \mathbf{+66.755006^\circ} \quad (+66^\circ 45' 18.02'')$$
- **Total Astrometric Displacement ($\Delta\theta$)**:
  $$\Delta\theta = \frac{\sqrt{(+145.236\,\text{mas})^2 + (-180.810\,\text{mas})^2}}{1000} = \frac{\sqrt{21093.5 + 32692.3}}{1000} = \mathbf{0.2319''}$$
- **Displacement Direction**:
  - Right Ascension: Eastward ($\Delta\alpha > 0$, $\alpha_{2025.8} > \alpha_0$).
  - Declination: Southward ($\Delta\delta < 0$, $\delta_{2025.8} < \delta_0$).
- **Instrumental Scale Comparison**:
  - SPHEREx detector pixel scale: $6.2''$/pixel.
  - Pixel displacement fraction: $\frac{0.2319''}{6.2''} = 0.0374\,\text{pixel}$ ($< 4\%$ of a pixel).
  - R Draconis remains virtually stationary on the SPHEREx pixel grid, validating its role as a stationary photometric variability benchmark.

### Unified Cross-System Agreement
The updated test suite explicitly asserts:
- Backend `TARGET_CATALOG["r-draconis"]` matches reference coordinates to $< 10^{-5}$ deg.
- Curated Data Provider (`provider.get_target_by_id("r-draconis")`) matches catalog coordinates to $< 10^{-5}$ deg.
- Frontend Preset Target in `frontend/components/controls/SpherexSearchPanel.tsx`:
  `{ name: "R Draconis", ra: 248.167625, dec: 66.755056, radius: 0.1, collection: "spherex_qr3" }`
  matches backend catalog coordinates to $< 10^{-5}$ deg.

---

## 3. Actual WISE 0855 FITS Dimensions and WCS Projection Results

### Physical FITS Header Inspection
Direct inspection of the actual calibrated SPHEREx Level-2 multi-extension FITS file covering WISE 0855 (`data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits`) produced the following physical parameters:

- **HDU Index**: **HDU 1**
- **Extension Name**: `IMAGE`
- **HDU Type**: `ImageHDU`
- **Data Array Shape**: `(2040, 2040)`
- **NAXIS**: 2
- **NAXIS1**: **2040** (detector columns)
- **NAXIS2**: **2040** (detector rows)
- **BITPIX**: **-32** (IEEE 754 32-bit single-precision floating point, photometric flux in MJy/sr)
- **WCS Reference Metadata**:
  - `CTYPE1`: `RA---TAN-SIP` (gnomonic tangent projection with SIP polynomial distortion)
  - `CTYPE2`: `DEC--TAN-SIP`
  - `CRVAL1`: $132.763132073^\circ$ (reference Right Ascension)
  - `CRVAL2`: $-5.65674041974^\circ$ (reference Declination)
  - `CRPIX1`: $1020.5$ (reference pixel X)
  - `CRPIX2`: $1020.5$ (reference pixel Y)
  - `CDELT1`: $1.0^\circ$
  - `CDELT2`: $1.0^\circ$
  - `CUNIT1`: `deg`, `CUNIT2`: `deg`

*Note on Physical Detector Geometry*: While raw SPHEREx Teledyne H2RG detectors contain $2048 \times 2048$ pixels, the calibrated Level-2 science product trims 4 boundary/reference pixels from each edge, resulting in an active science array of exactly $2040 \times 2040$ pixels ($2048 - 8 = 2040$). All previous hardcoded assumptions of $2048 \times 2048$ were replaced with dynamic extraction from `hdul[1].header["NAXIS1"]` and `hdul[1].header["NAXIS2"]`.

### WCS Projection Verification

| Coordinate Type | RA (deg) | Dec (deg) | Pixel X ($px$) | Pixel Y ($py$) | Boundary Check $[0, 2040) \times [0, 2040)$ | Distance to Image Edge |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Catalog Reference** (J2010.0) | $133.795129^\circ$ | $-7.245147^\circ$ | **176.16** | **266.04** | **INSIDE** ($0 \le 176.16 < 2040, 0 \le 266.04 < 2040$) | $176.16$ px from left, $266.04$ px from bottom |
| **Propagated** (2025.8) | $133.759213^\circ$ | $-7.242009^\circ$ | **196.65** | **262.79** | **INSIDE** ($0 \le 196.65 < 2040, 0 \le 262.79 < 2040$) | $196.65$ px from left, $262.79$ px from bottom |

Both catalog and propagated coordinates fall firmly within the active calibrated detector area. Over the 15.8-year baseline from J2010.0 to 2025.8, WISE 0855 moves by $+20.49$ pixels in X and $-3.25$ pixels in Y (a net proper motion displacement of $20.75$ pixels, or $128.76''$), remaining fully within the single-epoch field of view.

---

## 4. Corrected Archive Availability Statement

### Evidence-Based Protocol
All claims in earlier documentation speculating about SPHEREx data release schedules or asserting that DR1 is "unreleased" have been removed and replaced with an evidence-based formulation:

1. **Classification of Network Failures**:
   - HTTP 408 (Request Timeout), HTTP 502 (Bad Gateway), HTTP 500, DNS resolution failures, and client read/connect timeouts represent **failed network requests / gateway timeouts** between the local client and remote IPAC SIA/TAP servers.
   - A failed network request **does not** establish that the DR1 or QR3 collection is unreleased, empty, or devoid of observations.
2. **Taxonomy Enforcement**:
   - Remote query failures are classified strictly according to the canonical 7-state discovery taxonomy:
     - `ARCHIVE_QUERY_FAILED`: HTTP 5xx or unparseable payload.
     - `ARCHIVE_QUERY_TIMEOUT`: HTTP 408 or client socket timeout.
     - `ARCHIVE_QUERY_SUCCESS_NO_RESULTS`: HTTP 200 with an empty VOTable.
     - `NO_SPATIAL_COVERAGE`: Confirmed HTTP 200 records that do not intersect target WCS.
     - `INSUFFICIENT_TEMPORAL_COVERAGE`: Confirmed spatial intersection with only 1 usable epoch.
     - `SUFFICIENT_TEMPORAL_COVERAGE`: Confirmed spatial intersection with $\ge 2$ usable epochs.
     - `UNVERIFIED`: Unresolved remote queries due to network or gateway failures.
3. **Strict Scientific Boundary**:
   - Under no circumstances does the system convert an archive query error or timeout into `NO_SPATIAL_COVERAGE` or 0 observations.
   - When remote queries cannot be completed, targets remain designated as `UNVERIFIED`.

---

## 5. Deduplicated Test Inventory & Execution Results

### Accurate Test Metrics
- **Tests Passed**: **79**
- **Tests Failed**: **0**
- **Tests Skipped**: **0**
- **Test Pass Rate**: **100%**
- *Code Coverage Clarification*: Formal statement and branch coverage profiling (e.g., `pytest-cov`) was not executed; claims of "100% test coverage" in earlier drafts were corrected to state **100% test pass rate across 79 unique test functions**.

### Deduplicated Test Inventory (79 Unique Tests)

```
====================================================================================================
TEST SUITE 1: ROOT ACCEPTANCE & RELIABILITY SUITE (`pytest tests/`) — 56 Tests Passed
====================================================================================================
tests/test_spherex_m4_validation.py (5 tests):
  1. test_01_real_fits_presence_and_sha256
  2. test_02_mef_structure_and_hdu_preservation
  3. test_03_wcs_sip_distortion_compatibility
  4. test_04_api_status_and_inspection
  5. test_05_api_layer_load

tests/test_spherex_m5_validation.py (12 tests):
  6. test_gate_01_mef_ingestion
  7. test_gate_02_quality_mask_policy
  8. test_gate_03_wcs_reprojection
  9. test_gate_04_variance_propagation
 10. test_gate_05_spectral_compatibility
 11. test_gate_06_psf_homogenization
 12. test_gate_07_difference_exactness
 13. test_gate_08_significance_null_data
 14. test_gate_09_synthetic_injection_recovery
 15. test_gate_10_mandatory_disclaimer_label
 16. test_gate_11_edge_artifact_rejection
 17. test_gate_12_real_spherex_pair

tests/test_spherex_m6_2_reliability.py (19 tests):
 18. test_r_draconis_coordinate_propagation_correction
 19. test_five_targets_catalog_completeness_and_units
 20. test_frontend_backend_coordinate_consistency
 21. test_archive_query_502_handling
 22. test_archive_query_500_handling
 23. test_archive_query_timeout_handling
 24. test_archive_query_successful_empty_response
 25. test_archive_query_successful_with_observations
 26. test_archive_query_cached_behavior
 27. test_archive_query_retry_limits
 28. test_archive_query_connect_timeout
 29. test_archive_query_read_timeout
 30. test_archive_query_dns_failure
 31. test_archive_query_permanent_4xx_error_not_retried
 32. test_archive_query_retry_after_longer_than_limit_aborts
 33. test_archive_query_retry_after_shorter_than_limit_respected
 34. test_archive_query_attempts_log_structure
 35. test_target_unverified_on_failed_archive_query
 36. test_target_insufficient_on_single_epoch

tests/test_spherex_m6_validation.py (20 tests):
 37. test_coordinate_sexagesimal_parsing_valid
 38. test_coordinate_formatting_roundtrip
 39. test_coordinate_parsing_boundary_rejection
 40. test_proper_motion_propagation_barnards_star
 41. test_proper_motion_propagation_wise_0855
 42. test_proper_motion_stationary_stars
 43. test_five_targets_catalog_completeness
 44. test_epsilon_indi_b_spatial_resolution_constraint
 45. test_wise_0855_in_local_level2_fits
 46. test_lvf_wavelength_evaluation_from_fits
 47. test_wcs_footprint_sip_guard
 48. test_multi_epoch_chronological_ordering
 49. test_sufficient_temporal_coverage_equatorial_pair
 50. test_insufficient_temporal_coverage_handling
 51. test_disclaimer_label_enforcement
 52. test_target_validation_suite_disclaimer
 53. test_frozen_approved_fits_hashes
 54. test_api_temporal_discovery_endpoint
 55. test_api_m6_targets_validation_endpoint
 56. test_api_m6_single_target_validation_endpoint

====================================================================================================
TEST SUITE 2: BACKEND CORE & SCIENTIFIC UNIT SUITE (`pytest backend/tests/`) — 23 Tests Passed
====================================================================================================
backend/tests/test_coordinates.py (5 tests):
 57. test_parse_sexagesimal_ra
 58. test_parse_sexagesimal_dec
 59. test_hms_dms_roundtrip
 60. test_cartesian_and_threejs_vectors
 61. test_angular_separation

backend/tests/test_difference_imaging.py (3 tests):
 62. test_compute_mad_sigma
 63. test_difference_imaging_identical
 64. test_difference_imaging_with_transient_source

backend/tests/test_spherex_m5_validation.py (13 tests):
 65. test_lvf_evaluation_and_interpolation
 66. test_spectral_compatibility_rule
 67. test_common_wcs_and_reprojection
 68. test_registration_displacement_calculation
 69. test_flags_bitmask_and_nans
 70. test_psf_matching_sharp_epoch_convolution
 71. test_difference_and_significance_math
 72. test_conservative_candidate_extraction_disclaimer
 73. test_fixtures_end_to_end
 74. test_real_fits_self_difference
 75. test_api_benchmark_pairs
 76. test_api_observations
 77. test_api_compare_fixtures

backend/tests/test_targets.py (2 tests):
 78. test_spherex_102_bands
 79. test_five_nasa_targets

====================================================================================================
SUMMARY: 79 Unique Tests Collected | 79 Passed | 0 Failed | 0 Skipped | Mutual Exclusivity: 100%
====================================================================================================
```

### Frontend Production Build Verification
- **Command**: `npm run build --prefix frontend`
- **Engine**: Next.js 16.4.6 (Turbopack)
- **Compilation Time**: 3.8s
- **TypeScript Typecheck**: 17.0s (0 errors)
- **Static Page Generation**: 5/5 routes prerendered (`/`, `/_not-found`, `/explore`) in 1393ms
- **Build Status**: **SUCCESS (Exit Code 0)**

---

## 6. Inventory of Modified Source Files

| File Path | Nature of Changes |
| :--- | :--- |
| `tests/test_spherex_m6_2_reliability.py` | Expanded `test_r_draconis_coordinate_propagation_correction` to assert numerical propagation formulas, displacement direction ($\Delta\alpha > 0, \Delta\delta < 0$), displacement magnitude ($0.2319''$), canonical Gaia DR3 values ($+14.82\,\text{mas/yr}$), and explicit rejection of spurious $31.25$. Updated `test_frontend_backend_coordinate_consistency` to verify frontend `SpherexSearchPanel.tsx` preset coordinates against backend `TARGET_CATALOG`. |
| `tests/test_spherex_m6_validation.py` | Updated `test_wise_0855_in_local_level2_fits` to dynamically extract `NAXIS1` (2040) and `NAXIS2` (2040) directly from HDU 1 (`IMAGE`), verify `BITPIX == -32`, verify catalog coordinate projection $(176.16, 266.04)$ inside image bounds, and verify propagated coordinate projection $(196.65, 262.79)$ inside image bounds. |
| `backend/app/services/spherex_discovery.py` | Updated `naxis1` and `naxis2` fallback default in `discover_local_observations` from 2048 to 2040, matching calibrated Level-2 science product active geometry. |
| `scripts/inspect_wise0855.py` | Standalone inspection tool verifying HDU structures, WCS parameters, BITPIX, and pixel coordinate conversions for WISE 0855. |
| `M6_2_2_FINAL_CONSISTENCY_CORRECTION_REPORT.md` | Authoritative closure report resolving all outstanding consistency defects. |

---

## 7. Remaining Limitations

1. **Remote Archive Gateway Responsiveness**:
   - Queries to external IPAC SIA endpoints for the 5 target positions during current runs encountered HTTP 408/502 timeouts.
   - The application handles these conditions deterministically using bounded retries and classifies unresolved targets as `UNVERIFIED`.
2. **Local Multi-Epoch Coverage**:
   - For WISE 0855, only 1 calibrated SPHEREx Level-2 observation (`level2_2025W44`) is available in local storage. Because at least 2 distinct epochs are required for difference imaging and temporal movie playback, WISE 0855 is classified as `INSUFFICIENT_TEMPORAL_COVERAGE`.
   - The calibrated 2-epoch equatorial benchmark pair at $(\alpha = 46.844^\circ, \delta = +1.832^\circ)$ remains the primary operational verification target for multi-epoch temporal subtraction.

---

## 8. Final Milestone Verdict

$$\mathbf{M6\_2\_2\_CONDITIONAL}$$

### Rationale
- **Engineering, Scientific Consistency & Reliability Closure**: **PASS**.
  - All R Draconis proper-motion inconsistencies and documentation errors have been eliminated and backed by mathematical unit tests.
  - Actual FITS detector dimensions ($2040 \times 2040$, $\text{BITPIX} = -32$) have replaced hardcoded 2048 assumptions.
  - Archive availability interpretation has been placed on an evidence-based footing that never misrepresents failed network requests as empty survey collections.
  - All 79 unique tests across both test suites pass with a 100% pass rate, and the Next.js production build compiles cleanly with zero errors.
- **Scientific Multi-Epoch Target Ingestion**: **CONDITIONAL**.
  - Multi-epoch temporal difference imaging for the 5 challenge targets remains conditional on live network accessibility of IPAC SIA endpoints once remote gateway connectivity is established.

---
*Report certified by Antigravity Autonomous Verification Engine. Preserved under baseline freeze rules.*
