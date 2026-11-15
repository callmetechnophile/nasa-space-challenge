# NASA SPHEREx 3D Temporal Sky Explorer — Project Status

**Repository**: `https://github.com/callmetechnophile/nasa-space-challenge`  
**Current Date**: 15 November 2026  
**Engineering Status**: **PRODUCTION READY (PASS)**  
**Scientific Validation Status**: **CONDITIONAL (Caveats Documented)**  

---

## 1. Completed Engineering Milestones

The SPHEREx 3D Temporal Sky Explorer fulfills the requirements of the NASA Space Apps Challenge through an architecture uniting interactive 3D WebGL visualization, rigorous astrometric coordinate navigation, and an Astropy-driven scientific image processing backend:

| Milestone | Title | Key Engineering Deliverables | Test Coverage | Status |
| :---: | :--- | :--- | :---: | :---: |
| **M1** | 3D Celestial Sphere | Three.js / React Three Fiber interactive celestial sphere; true ICRS equatorial grid; RA hour circles & Dec parallels; Galactic & Ecliptic planes; 5,000+ star field with authentic B-V spectral colors. | UI / E2E | **PASS** |
| **M2** | Coordinate Engine | Decimal degree and sexagesimal string coordinate parser (RA/Dec); dynamic Galactic ($l, b$) and Ecliptic ($\lambda, \beta$) transformation; bidirectional URL routing. | 5 Unit Tests | **PASS** |
| **M3** | WCS Image Rendering | Sub-pixel tangent plane projection (`RA---TAN`, `DEC--TAN`, `TAN-SIP`); display stretches (linear, log, sqrt, asinh); dynamic canvas tile generation and spherical texture projection. | Unit & Integration | **PASS** |
| **M4** | SPHEREx MEF Pipeline | Typed multi-extension FITS reader (`IMAGE`, `FLAGS`, `VARIANCE`, `ZODI`, `PSF`, `WCS-WAVE`); NASA IRSA SIA2 live query client; local observation cache; cryptographic verification. | 5 Validation Tests | **PASS** |
| **M5** | Difference Imaging | Multi-pass observation timeline (6-month survey cadence); Blink comparator, split-view comparator; pixel-aligned differential flux $D = I_2 - I_1$; analytical variance propagation $\sigma_D^2 = \sigma_1^2 + \sigma_2^2$; MAD noise floor; automated candidate extraction. | 15 Validation Tests | **CONDITIONAL** |
| **M6** | Challenge Completion | Interactive time-series video/player; five-target NASA benchmark integration; astrometric proper motion propagation across arbitrary epochs; target preset navigation. | 20 Target Tests | **CONDITIONAL** |
| **M6.2.x** | Archive Reliability & FITS Integrity | Attempt-by-attempt telemetry logging; 5.0s `Retry-After` operational cap; dynamic header/array dimension derivation; deterministic HDU selector preventing auxiliary fallback; index-bypass prevention; cryptographic baseline hash reconciliation (`36b330b5...`). | 46 Integrity Tests | **PASS** |

---

## 2. Scientific Validation Status & Caveats

### 2.1 Milestone 5 (Difference Imaging): CONDITIONAL
- **Verified Capabilities**: Analytical subtraction, error propagation, bitwise pixel quality masking, and synthetic transient injection/recovery are mathematically proven and pass all Gate 1–12 validation tests.
- **Limitation**: Real automated subtraction across arbitrary public sky tiles requires sub-pixel astrometric cross-matching, background matching, and PSF homogenization across disparate focal plane detectors. The system enforces a mandatory disclaimer label on all change candidates:  
  `"Change Candidate - Subject to Astrometric & Photometric Verification"`.

### 2.2 Milestone 6 (Five Challenge Targets): CONDITIONAL
- **Barnard's Star, Epsilon Indi B, RW Aurigae, R Draconis**:
  - Live queries against NASA/IPAC SIA2 and TAP endpoints returned HTTP 408 (Request Timeout) and HTTP 502 (Bad Gateway).
  - In accordance with rigorous scientific taxonomy, these targets are classified as **`UNVERIFIED`** rather than assuming an absence of data.
- **WISE 0855**:
  - Local calibrated SPHEREx MEF product (`level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits`) confirmed spatial footprint coverage with the target falling at pixel $(176.2, 266.0)$ catalog / $(196.6, 262.8)$ propagated on the active $2040 \times 2040$ detector array.
  - Because multi-epoch temporal discovery strictly requires $\ge 2$ usable observation epochs and only 1 calibrated epoch is currently available locally, WISE 0855 is classified as **`INSUFFICIENT_TEMPORAL_COVERAGE`**.
  - **Zero observations or temporal detections are fabricated.**

---

## 3. System Architecture & Tech Stack

```
                          USER INTERFACE (Next.js 16 + React 19)
       ┌────────────────────────────────────────────────────────────────────────┐
       │  • 3D Celestial Sphere (Three.js / React Three Fiber / WebGL)           │
       │  • Temporal Player (Single, Blink, Split, Scientific Difference)       │
       │  • 102-Band LVF Near-Infrared Spectral Profile Explorer (0.75 - 5.0 µm)│
       │  • Astrometric Coordinate Bar & 5-Target Quick Navigation Presets      │
       └───────────────────────────────────┬────────────────────────────────────┘
                                           │ HTTP / JSON
                                           ▼
                            BACKEND SERVICE (FastAPI + Python 3.13)
       ┌────────────────────────────────────────────────────────────────────────┐
       │  • Coordinate Engine: Sexagesimal, Decimal, ICRS, Galactic, Ecliptic   │
       │  • Astropy WCS & FITS Reader: Strict Integer NAXIS, Dynamic Footprints  │
       │  • Difference Engine: D = I2 - I1, Analytical Variance Propagation     │
       │  • SPHEREx Discovery: Bounded Retry, 5s Cap, 7-State Archive Taxonomy  │
       └───────────────────────────────────┬────────────────────────────────────┘
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
             LOCAL VERIFIED REPOSITORY             NASA / IPAC IRSA ARCHIVE
         • Calibrated SPHEREx Level 2 MEF         • SIA2 Observation Queries
         • SHA-256: 36b330b5...                   • TAP Catalog Searches
         • 102 LVF Bandpass Tables                • Bounded Retries with Jitter
```

---

## 4. Test & Verification Telemetry

All test suites and production builds execute with zero errors:

| Test Suite / Build Target | Command | Tests Run | Passed | Failed | Execution Time |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **FITS Dimension & HDU Integrity** | `python -m pytest tests/test_fits_dimensions_integrity.py` | 27 | 27 | 0 | 3.86s |
| **Root Regression Test Suite** | `python -m pytest tests/` | 83 | 83 | 0 | 21.73s |
| **Backend Integration Test Suite** | `python -m pytest backend/tests/` | 23 | 23 | 0 | 7.68s |
| **Unique Tests Total** | *(No double-counting)* | **106** | **106** | **0** | **33.27s** |
| **Frontend Production Build** | `npm run build --prefix frontend` | Next.js 16.4.6 | **Success** | 0 errors | 3.70s |

---

## 5. Deployment Readiness

- **Frontend**: Fully production-ready. Next.js 16 App Router prerenders all routes (`/`, `/_not-found`, `/explore`) with zero TypeScript errors.
- **Backend**: FastAPI service runs asynchronously under Uvicorn with robust exception handlers, CORS configuration, and granular telemetry.
- **Data Integrity**: Local calibrated Level-2 SPHEREx FITS product verified byte-identical against M4 baseline hash `36b330b5ed45161383aedc7e9199619c6ca1873e213a5fdc8ff027274190caf6`.
- **Verdict**: **READY FOR DEPLOYMENT** with full transparency regarding archive coverage and conditional scientific validation.
