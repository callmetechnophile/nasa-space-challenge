# NASA SPHEREx 3D Temporal Sky Explorer — Development Timeline

**Repository**: `https://github.com/callmetechnophile/nasa-space-challenge`  
**Reference Timeline Date**: 14 November 2026 – 15 November 2026  
**Status**: Verifiable Milestone History & Provenance Audit  

---

## 1. Provenance & Date Confidence Taxonomy

To maintain scientific integrity and audit defensibility, dates recorded across this repository are categorized by verifiable provenance rather than assumed chronology:

| Category | Definition | Provenance Standard |
| :--- | :--- | :--- |
| **Independently Established** | Events, test executions, and report generations backed by timestamped logs, filesystem metadata, or live execution telemetry. | Verifiable via repo logs, commit timestamps, and test receipts. |
| **Report Verification Date** | Timestamp when an engineering or scientific audit report was formally executed, verified, and saved to disk. | Stated in report headers and confirmed by local file creation timestamps. |
| **Historical Implementation** | Code and features developed during prior architectural iterations where exact commit dates were not preserved prior to git baseline initialization. | Explicitly labeled as `Date not independently established (pre-14 Nov 2026 snapshot)`. |
| **Baseline Repository Import** | Date when the existing code and documentation artifacts were formally committed into Git version control. | 15 November 2026. |

---

## 2. Milestone Development & Verification Chronology

```
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ 14 November 2026 (Historical Baseline & Formal Audits)                                          │
  ├──────────────────────────────┬──────────────────────────────────┬────────────────────────────────┤
  │ M1–M4: Celestial Sphere,     │ M5: Temporal Difference Imaging │ Stage 1.1: Pre-Deployment      │
  │ WCS & SPHEREx Integration    │ & Pair Verification             │ Closure & Verification         │
  └──────────────────────────────┴──────────────────────────────────┴────────────────────────────────┘
                                                  │
                                                  ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ 15 November 2026 (Live Audits & Engineering Closure)                                             │
  ├──────────────────────────────┬──────────────────────────────────┬────────────────────────────────┤
  │ M6: Multi-Epoch Explorer &   │ M6.2.1–M6.2.3: Archive Retry     │ M6.2.4–M6.2.6: FITS Dimension  │
  │ Five-Target Verification     │ Budget & Dimension Derivation    │ Integrity & Hash Reconcile     │
  └──────────────────────────────┴──────────────────────────────────┴────────────────────────────────┘
```

---

### Milestone 1 to 4: Celestial Sphere, Coordinates, WCS Projection & SPHEREx Reader

- **Scope**:
  - Interactive 3D celestial sphere in WebGL (Three.js / React Three Fiber) with true ICRS equatorial grid, constellation asterisms, Galactic and Ecliptic planes, and instanced star field.
  - Astrometric coordinate parser supporting decimal degrees and sexagesimal formats with URL query routing.
  - Astropy WCS integration projecting 2D FITS images directly onto spherical geometry.
  - SPHEREx Multi-Extension FITS (MEF) reader for Level-2 products (`IMAGE`, `FLAGS`, `VARIANCE`, `ZODI`, `PSF`, `WCS-WAVE`).
- **Date Classification**:
  - Initial code development: `Date not independently established (prior snapshot)`.
  - Formal audit and verification: **14 November 2026**.
- **Evidence & Artifacts**:
  - Verification reports: `M3_FINAL_AUDIT_REPORT.md`, `M3_SCIENTIFIC_VALIDATION_REPORT.md`, `M4_FINAL_VALIDATION_REPORT.md`, `M4_REAL_FITS_VALIDATION_REPORT.md`.
  - Test suites: `tests/test_spherex_m4_validation.py` (5 tests passing).
  - Checksum receipt: `evidence/m4/product_provenance_and_checksum.json`.
  - Calibrated FITS product: `data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits` (SHA-256: `36b330b5...`).
- **Validation Status**: **PASS**.

---

### Milestone 5: Temporal Sky Analysis & Scientific Difference Imaging

- **Scope**:
  - Temporal multi-pass observation management (6-month cadence passes).
  - Visual comparison modes: Single epoch, Automated Blink Comparator, Split Side-by-Side.
  - Scientific Difference Imaging Engine: Pixel-aligned differential flux $D(x, y) = I_2(x, y) - I_1(x, y)$ with analytical variance propagation $\sigma_D^2 = \sigma_1^2 + \sigma_2^2$.
  - Median Absolute Deviation (MAD) robust noise estimation and automated transient candidate extraction with mandatory scientific disclaimer labeling.
  - End-to-end difference imaging demonstration on calibrated SPHEREx FITS pair (`level2_2026W31...` and `level2_2026W32...`).
- **Date Classification**:
  - Initial pipeline development: `Date not independently established (prior snapshot)`.
  - Formal scientific validation: **14 November 2026**.
- **Evidence & Artifacts**:
  - Verification reports: `M5_SCIENTIFIC_VALIDATION_REPORT.md`, `M5_FINAL_CALIBRATION_AND_PHOTOMETRY_REPORT.md`, `M5_FINAL_PAIR_VALIDATION_REPORT.md`.
  - Test suites: `tests/test_spherex_m5_validation.py` (12 tests passing), `backend/tests/test_difference_imaging.py` (3 tests passing).
  - Synthetic and calibrated FITS fixtures: `data/spherex/fixtures_m5/`.
- **Validation Status**: **CONDITIONAL**.
  - *Scientific Caveat*: Approved for synthetic and aligned sample pairs under sub-pixel registration; full automated general-sky difference imaging on arbitrary public SPHEREx data remains conditional upon live archive data release and cross-detector PSF homogenization.

---

### Milestone 6: Challenge Completion & Five-Target Verification

- **Scope**:
  - Public-facing time-series video/player for SPHEREx images.
  - Integration of NASA's five required test targets:
    1. **Barnard's Star** (High proper motion M dwarf, $10.37''/\text{yr}$)
    2. **Epsilon Indi B** (T-dwarf binary, sub-stellar benchmark)
    3. **WISE 0855** (Sub-freezing brown dwarf, $RA = 08^h 55^m 10.831^s, Dec = -07^\circ 14' 42.53''$)
    4. **RW Aurigae** (T Tauri variable star with circumstellar occultations)
    5. **R Draconis** (Mira long-period pulsating variable giant)
  - Implementation of proper motion propagation from reference catalog epochs (J2000.0, J2010.0, J2016.0) to observation epochs ($2025.8$).
- **Date Classification**:
  - Implementation & verification: **14 November 2026 – 15 November 2026**.
- **Evidence & Artifacts**:
  - Reports: `M6_CHALLENGE_COMPLETION_REPORT.md`, `M6_1_FINAL_TARGET_COVERAGE_AND_ACCEPTANCE_REPORT.md`.
  - Target documentation: `TARGET_BARNARDS_STAR.md`, `TARGET_EPSILON_INDI_B.md`, `TARGET_WISE_0855.md`, `TARGET_RW_AURIGAE.md`, `TARGET_R_DRACONIS.md`.
  - Target tests: `tests/test_spherex_m6_validation.py` (20 tests passing).
- **Validation Status**: **CONDITIONAL**.
  - *Scientific Caveat*: Engineering interface and coordinate propagation passed 100%. External target verification remains conditional due to temporal coverage availability in public SPHEREx data releases.

---

### Milestone 6.2.x: Archive Reliability, FITS Metadata Integrity & Hash Reconciliation

- **Scope**:
  - **M6.2.1**: Granular network error taxonomy, attempt-by-attempt telemetry logging, 5.0s `Retry-After` cap, and dual coordinate search (catalog + propagated).
  - **M6.2.2**: Proper-motion numerical consistency correction for R Draconis (+14.82 mas/yr canonical) and elimination of duplicate fixtures.
  - **M6.2.3**: Elimination of hardcoded $2040 \times 2040$ fallback; dynamic derivation of FITS dimensions directly from headers and array shapes.
  - **M6.2.4**: Deterministic IMAGE HDU selection preventing auxiliary fallback, strict non-boolean positive integer dimension parsing ($1 \le \text{dim} \le 2^{31}-1$).
  - **M6.2.5**: Universal call-path enforcement ensuring caller input cannot override SPHEREx semantics; alignment of archive status reporting with HTTP 408/502 telemetry.
  - **M6.2.6**: FITS baseline hash reconciliation proving local calibrated file `level2_2025W44...307.fits` is 100% byte-identical to M4 approved hash (`36b330b5...`); confirmation of generic FITS explicit `'VARIANCE'` selection.
- **Date Classification**:
  - Engineering execution and verification: **15 November 2026**.
- **Evidence & Artifacts**:
  - Reports:
    - `M6_2_1_FINAL_EVIDENCE_CLOSURE_REPORT.md`
    - `M6_2_2_FINAL_CONSISTENCY_CORRECTION_REPORT.md`
    - `M6_2_3_FITS_DIMENSION_INTEGRITY_REPORT.md`
    - `M6_2_4_STRICT_FITS_VALIDATION_REPORT.md`
    - `M6_2_5_FINAL_SELECTOR_AND_ARCHIVE_CLOSURE_REPORT.md`
    - `M6_2_6_FITS_BASELINE_HASH_RECONCILIATION_REPORT.md`
  - Test suites:
    - `tests/test_spherex_m6_2_reliability.py` (19 tests passing).
    - `tests/test_fits_dimensions_integrity.py` (27 tests passing).
- **Validation Status**: **M6_2_6_CONDITIONAL** (Engineering Architecture: **PASS** | Live External Public SPHEREx DR1 Target Availability: **CONDITIONAL**).

---

## 3. Summary of Verifiable Scientific Caveats

1. **Difference Imaging Pipeline Status (M5)**:
   - Evaluated as **CONDITIONAL**.
   - Fully functional on pixel-aligned and calibrated image pairs. Full automated real-time subtraction on uncalibrated or single-epoch public archives requires multi-epoch spatial coverage and PSF homogenization across disparate detector quadrants.
2. **External Five-Target Archive Status (M6.2.x)**:
   - Queries to NASA/IPAC SIA2 and TAP endpoints for Barnard's Star, Epsilon Indi B, RW Aurigae, and R Draconis returned HTTP 408 (Request Timeout) and HTTP 502 (Bad Gateway). In accordance with strict archive taxonomy, these targets are classified as **`UNVERIFIED`** rather than asserting an absence of archive data.
   - WISE 0855 spatial intersection was verified on the active $2040 \times 2040$ detector array of local calibrated product `level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits`. Because multi-epoch temporal discovery strictly requires $\ge 2$ usable epochs and only 1 is currently available locally, WISE 0855 is classified as **`INSUFFICIENT_TEMPORAL_COVERAGE`**.
   - **Zero observations or temporal detections are fabricated.**
