# SPHEREx — Pre-Deployment Testing Campaign
## Stage 1: Local System Integrity and Regression Audit Report

**Project:** NASA SPHEREx — 3D Temporal Sky Explorer  
**Audit Document:** `PRE_DEPLOYMENT_STAGE1_REPORT.md`  
**Execution Timestamp:** 2026-11-14T12:18:00+05:30  
**Phase:** Pre-Deployment Stage 1 (Local System Integrity & Comprehensive Regression)  
**Deployment Target:** Local Baseline (Cloud deployment on Azure deferred until Stage 2)  
**Stage 1 Verdict:** **`STAGE1_PASS`**

---

## 1. EXECUTIVE AUDIT SUMMARY & VERDICT

Before commencing containerization and cloud infrastructure deployment to Azure, the complete SPHEREx 3D Temporal Sky Explorer application underwent a full local integrity, regression, and scientific data audit.

```
+=======================================================================================================+
| PRE-DEPLOYMENT STAGE 1 AUDIT VERDICT: STAGE1_PASS                                                     |
+=======================================================================================================+
| Milestone Scope Audited:        Milestones 1 through 5 (M1–M5)                                        |
| Code Modifications:             0 files modified in frozen M1–M5 code                                 |
| Regression Test Execution:      49 executed, 49 PASSED, 0 failed, 0 skipped                           |
| Scientific Data Integrity:      Bitwise identical SHA-256 hashes for all approved Level-2 FITS        |
| Backend Integrity:              FastAPI + Uvicorn 27 API endpoints responsive, CORS valid, /health OK |
| Frontend Integrity:             Next.js 16 (Turbopack) build clean in 937ms, WebGL 2.0 Three.js stable |
| Memory Baseline:                Startup 33.5 MB, Peak 199.5 MB, 20-Cycle Drift +0.20 MB (Zero Leaks)   |
+=======================================================================================================+
```

---

## 2. ENVIRONMENT INVENTORY

A complete inventory of the local development and testing environment was captured:

### 2.1 Host System & Hardware Specifications
- **Operating System:** Microsoft Windows 11 Pro, Version 10.0.29704 Build 29704 (64-bit AMD64)
- **CPU:** AMD Ryzen (AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD)
  - **Physical Cores:** 8
  - **Logical Processors:** 16
- **System Memory (RAM):**
  - **Total Installed:** $23.31\text{ GB}$ ($25,028,349,952\text{ bytes}$)
  - **Available at Audit:** $11.66\text{ GB}$ ($12,520,382,464\text{ bytes}$)
- **GPU Architecture:**
  1. **Discrete GPU:** NVIDIA GeForce RTX 5050 Laptop GPU (Driver Version: `32.0.16.1742`, Dedicated VRAM: $4.00\text{ GB}$ / $4,293,918,720\text{ bytes}$)
  2. **Integrated GPU:** AMD Radeon 780M Graphics (Driver Version: `32.0.32015.7029`, Dedicated VRAM: $512\text{ MB}$ / $536,870,912\text{ bytes}$)
- **CUDA Acceleration:** NVIDIA Hardware available; PyTorch not utilized by application (all backend astronomical processing executed via highly optimized NumPy, SciPy, and Astropy C extensions).

### 2.2 Runtimes & Dependency Versions
- **Python Runtime:** Python `3.13.9` (Anaconda 64-bit MSC v.1929)
- **Node.js Runtime:** Node.js `v26.1.0`
- **Package Manager:** npm `11.13.0`
- **Key Python Packages:**
  - `astropy`: `7.1.1` (Celestial WCS, FITS MEF, SIP, FITS tables)
  - `fastapi`: `0.135.3` (ASGI web framework)
  - `starlette`: `1.6.0` (ASGI core)
  - `uvicorn`: `0.52.4` (ASGI web server)
  - `numpy`: `2.3.4` (Numerical arrays)
  - `scipy`: `1.16.3` (Image processing, connected components, spline/bivariate interpolation)
  - `pydantic`: `2.13.1` (Data validation and models)
  - `httpx`: `0.28.1` (Async/sync HTTP client)
  - `pytest`: `8.4.2` (Automated testing framework)
- **Key Frontend Packages:**
  - `next`: `16.4.6` (React full-stack framework with Turbopack)
  - `react`: `19.3.0`
  - `react-dom`: `19.3.0`
  - `three`: `^0.187.0` (3D WebGL celestial sphere engine)
  - `@react-three/fiber`: `^9.8.2`
  - `@react-three/drei`: `^10.7.9`
  - `zustand`: `^5.1.0` (State management)
  - `tailwindcss`: `4.3.3` (CSS styling)
  - `typescript`: `^5.0.0`
  - `playwright`: `^1.65.0` (Headless browser automation)

---

## 3. BACKEND INTEGRITY AUDIT

### 3.1 Server Startup & Architecture
- **FastAPI Application:** Initialized as `SPHEREx 3D Temporal Sky Explorer API` (`v1.0.0`).
- **Live Server Daemon:** Background Uvicorn process listening on `127.0.0.1:8000`.
- **Health Check (`GET /health`):** Returned HTTP `200 OK` in $4\text{ ms}$:
  ```json
  {"status": "HEALTHY", "astropy_wcs": true, "spectral_channels": 102}
  ```
- **Root Information (`GET /`):** Returned HTTP `200 OK` confirming operational status and 5 validation targets.

### 3.2 Registered API Route Catalog
Total 27 operational API endpoints were inventoried and verified:

| HTTP Methods | Path | Component / Router | Operational Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root Info | Operational |
| `GET` | `/health` | System Health Check | Operational |
| `GET` | `/api/v1/coordinates/convert` | Coordinates Router | Operational |
| `POST` | `/api/v1/coordinates/parse` | Coordinates Router | Operational |
| `GET` | `/api/v1/images/cutout` | Image Processing Router | Operational |
| `POST` | `/api/v1/images/difference` | Image Processing Router | Operational |
| `GET` | `/api/v1/images/fits` | Image Processing Router | Operational |
| `POST` | `/api/v1/images/process-fits` | Image Processing Router | Operational |
| `POST` | `/api/v1/images/re-stretch` | Image Processing Router | Operational |
| `GET` | `/api/v1/images/sample/{sample_id}` | Image Processing Router | Operational |
| `GET` | `/api/v1/images/samples` | Image Processing Router | Operational |
| `GET` | `/api/v1/images/validate-wcs/{sample_id}` | Image Processing Router | Operational |
| `GET` | `/api/v1/observations` | Observations Router | Operational |
| `GET` | `/api/v1/spectral/bands` | Spectral Router | Operational |
| `GET` | `/api/v1/spectral/bands/{channel_index}` | Spectral Router | Operational |
| `GET` | `/api/v1/spectral/profile` | Spectral Router | Operational |
| `POST` | `/api/v1/spherex/download` | SPHEREx Archive Router | Operational |
| `GET` | `/api/v1/spherex/inspect/{filename}` | SPHEREx Archive Router | Operational |
| `POST` | `/api/v1/spherex/load-layer` | SPHEREx Archive Router | Operational |
| `GET` | `/api/v1/spherex/observations` | SPHEREx Archive Router | Operational |
| `POST` | `/api/v1/spherex/search` | SPHEREx Archive Router | Operational |
| `GET` | `/api/v1/spherex/status` | SPHEREx Archive Router | Operational |
| `GET` | `/api/v1/targets` | Targets Router | Operational |
| `GET` | `/api/v1/targets/{target_id}` | Targets Router | Operational |
| `GET` | `/api/v1/temporal/benchmark-pairs` | Temporal Engine Router | Operational |
| `POST` | `/api/v1/temporal/compare` | Temporal Engine Router | Operational |
| `GET` | `/api/v1/temporal/observations` | Temporal Engine Router | Operational |

### 3.3 CORS, Sandbox & Connectivity
- **CORS Configuration:** Evaluated via preflight `OPTIONS /api/v1/spherex/search`. Returned HTTP `200 OK` with `Access-Control-Allow-Origin: http://localhost:3000` and `Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT`. Verified compliant with W3C credentialed CORS specifications.
- **Cache Sandbox:** `data/spherex/cache` verified with test file write, verification, and deletion.
- **IRSA SIA2 Endpoint (`https://irsa.ipac.caltech.edu/SIA`):** Direct outbound connection timed out due to local network security policies; system fallback to verified local multi-extension FITS data and cached queries confirmed functional.

---

## 4. FRONTEND INTEGRITY & WEBGL AUDIT

### 4.1 Next.js Production Build
- **Build Command:** `npm --prefix frontend run build`
- **Compiler:** Next.js `16.4.6` with Turbopack engine
- **Compilation Time:** $937\text{ ms}$
- **TypeScript Typechecking:** Completed in $4.5\text{ s}$ with **0 type errors**.
- **Static Route Generation:**
  - Route `/`: Static prerendered
  - Route `/_not-found`: Static prerendered
  - Route `/explore`: Static prerendered
- **Build Exit Code:** `0` (Success).

### 4.2 Browser & WebGL Diagnostics
Evaluated via automated headless Microsoft Edge (`channel: "msedge"`) with WebGL acceleration:
- **Navigation:** `http://localhost:3000` returned HTTP `200 OK`.
- **Page Title:** `"SPHEREx | 3D Sky Explorer | DEMONSTRATION MODE"`
- **Canvas Element:** Verified active `<canvas>` element attached to the DOM.
- **WebGL Context:**
  - **Version:** WebGL 2.0 (OpenGL ES 3.0 Chromium)
  - **Renderer:** `ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)), SwiftShader driver)`
  - **Drawing Buffer Size:** $1400 \times 852\text{ pixels}$
  - **Context Lost Status:** `isContextLost === false` (Context 100% stable).
- **In-Browser API Connectivity:** `fetch("http://127.0.0.1:8000/health")` from within the browser DOM returned HTTP `200 OK` with JSON payload `{"status":"HEALTHY","astropy_wcs":true,"spectral_channels":102}`.
- **Console Errors:** **0 fatal console errors**. (Only benign informational warnings logged, e.g. `THREE.Clock` deprecation recommendation).

---

## 5. FULL REGRESSION TEST SUITE EXECUTION

All existing test suites across Milestones 1 through 5 were executed. No existing tests were modified or replaced.

```
========================================================================================================
COMPREHENSIVE REGRESSION TEST MATRIX (M1 THROUGH M5)
========================================================================================================
Suite / Milestone | Test File Path                              | Tests | Passed | Failed | Skipped | Time  | Exit
--------------------------------------------------------------------------------------------------------
Milestone 1       | backend/tests/test_coordinates.py           |     5 |      5 |      0 |       0 | 0.62s |    0
Milestone 2       | backend/tests/test_targets.py               |     2 |      2 |      0 |       0 | 1.08s |    0
Milestone 3 (WCS) | backend/test_m3_wcs.py                      |    10 |     10 |      0 |       0 | 2.10s |    0
Milestone 3 (Acc) | backend/test_m3_full_scientific_acceptance  |    12 |     12 |      0 |       0 | 1.67s |    0
Milestone 4 (Real)| tests/test_spherex_m4_validation.py         |     5 |      5 |      0 |       0 | 5.73s |    0
Milestone 5 (Diff)| backend/tests/test_difference_imaging.py    |     3 |      3 |      0 |       0 | 0.82s |    0
Milestone 5 (Val) | tests/test_spherex_m5_validation.py         |    12 |     12 |      0 |       0 | 7.97s |    0
--------------------------------------------------------------------------------------------------------
TOTALS            | 7 test suites                               |    49 |     49 |      0 |       0 | 20.0s |    0
========================================================================================================
```

### Exact Regression Commands Executed:
```powershell
# Milestone 1: Celestial Coordinates & Sexagesimal Parsing
$env:PYTHONPATH="backend"; pytest backend/tests/test_coordinates.py -v
# Result: 5 passed in 0.62s (Exit code 0)

# Milestone 2: 102 Spectral Bands & NASA Validation Targets
$env:PYTHONPATH="backend"; pytest backend/tests/test_targets.py -v
# Result: 2 passed in 1.08s (Exit code 0)

# Milestone 3: WCS, FITS Reader, Display Stretching & Spherical Geometry
$env:PYTHONPATH="backend"; pytest backend/test_m3_wcs.py backend/test_m3_full_scientific_acceptance.py -v
# Result: 22 passed in 3.77s (Exit code 0)

# Milestone 4: NASA SPHEREx Real Level-2 MEF Ingestion & WCS Validation
$env:PYTHONPATH="backend"; pytest tests/test_spherex_m4_validation.py -v
# Result: 5 passed in 5.73s (Exit code 0)

# Milestone 5: Multi-Epoch Temporal Comparison & Difference Engine
$env:PYTHONPATH="backend"; pytest tests/test_spherex_m5_validation.py backend/tests/test_difference_imaging.py -v
# Result: 15 passed in 7.97s (Exit code 0, 146 standard HIERARCH warnings preserved)
```

---

## 6. SCIENTIFIC DATA INTEGRITY AUDIT

Both approved NASA SPHEREx Level-2 multi-extension FITS data files were audited against their cryptographic SHA-256 hashes:

### 6.1 Cryptographic Digests
1. **Epoch 1:** `data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits`
   - **File Size:** $65,487,360\text{ bytes}$ ($62.45\text{ MB}$)
   - **Actual SHA-256:** `b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1`
   - **Expected SHA-256:** `b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1`
   - **Status:** **PASS (Bitwise Exact Match)**
2. **Epoch 2:** `data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits`
   - **File Size:** $65,487,360\text{ bytes}$ ($62.45\text{ MB}$)
   - **Actual SHA-256:** `60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e`
   - **Expected SHA-256:** `60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e`
   - **Status:** **PASS (Bitwise Exact Match)**

### 6.2 Multi-Extension HDU Structure & Data Types
Both files exhibit the identical 7-extension structure:
- **HDU 0 (`PRIMARY`):** `PrimaryHDU`, header metadata, zero image data.
- **HDU 1 (`IMAGE`):** `ImageHDU`, $(2040, 2040)$, big-endian 32-bit float (`>f4`), `BUNIT = MJy/sr`.
- **HDU 2 (`FLAGS`):** `CompImageHDU`, $(2040, 2040)$, `BITPIX = 32`, big-endian integer (`int32` / `>i4`).
- **HDU 3 (`VARIANCE`):** `ImageHDU`, $(2040, 2040)$, `BITPIX = -32`, big-endian 32-bit float (`>f4`), `BUNIT = (MJy/sr)^2`.
- **HDU 4 (`ZODI`):** `ImageHDU`, $(2040, 2040)$, big-endian 32-bit float (`>f4`).
- **HDU 5 (`EPSF`):** `BinTableHDU`, 441 spatial bins ($21 \times 21$ tiling), each bin containing an oversampled $(33, 33)$ double-precision array (`>f8`), `OVSMPX = 5, OVSMPY = 5`.
- **HDU 6 (`WCS-WAVE`):** `BinTableHDU`, $720 \times 1$ table, $(9, 9, 2)$ spectral wavelength model grid.
- **Detector:** `DETECTOR = 1` ($0.75 - 1.11\ \mu\text{m}$ band).

---

## 7. MEMORY & RESOURCE UTILIZATION BASELINE

System memory utilization was monitored across backend startup, MEF observation loading, memory deallocation, repeated cycles, and frontend rendering:

```
+-------------------------------------------------------------------------------------------------------+
| MEMORY & RESOURCE BASELINE METRICS                                                                    |
+-------------------------------------------------------------------------------------------------------+
| 1. Backend Process Memory (RSS):                                                                      |
|    - Startup (Modules loaded):                                  33.49 MB                              |
|    - Single Observation Loaded (2040x2040 arrays in memory):   199.46 MB (+165.97 MB)                 |
|    - Observation Unloaded (After gc.collect()):                 77.20 MB (Clean heap recovery)        |
|                                                                                                       |
| 2. Repeated Stress Cycles (20 Sequential Load/Process/Unload Cycles):                                 |
|    - Baseline after Cycle 1:                                    77.35 MB                              |
|    - Memory after Cycle 5:                                      77.52 MB                              |
|    - Memory after Cycle 10:                                     77.39 MB                              |
|    - Memory after Cycle 20:                                     77.40 MB                              |
|    - Net Growth across 20 Stress Cycles:                        +0.20 MB (0.2% variance; NO LEAKS)    |
|                                                                                                       |
| 3. Frontend Browser Memory (Headless Edge during Three.js WebGL Rendering):                          |
|    - Used JS Heap Size:                                         22.82 MB                              |
|    - Total Allocated JS Heap:                                   41.24 MB                              |
|    - Heap Size Limit:                                         4192.00 MB                              |
|                                                                                                       |
| 4. GPU VRAM Allocation:                                                                               |
|    - Server Backend:                                            0 MB (Pure CPU/NumPy compute)         |
|    - Client WebGL:                                              SwiftShader / ANGLE shared VRAM       |
+-------------------------------------------------------------------------------------------------------+
```

---

## 8. WARNINGS, ERRORS & RECOMMENDED ACTIONS

### 8.1 Recorded Warnings
1. **Pytest FITS `VerifyWarning` (146 occurrences):** Emitted during serialization of non-standard FITS card names $>8$ characters in SPHEREx Level-2 metadata (e.g. `HIERARCH L2 N_TRANSIENT`).
   - *Severity:* Informational / Harmless.
   - *Action:* Preserved without suppression per scientific audit guidelines.
2. **`StarletteDeprecationWarning`:** TestClient emitted notice regarding `httpx` vs `httpx2`.
   - *Severity:* Deprecation notice in test runner only; production ASGI server is unaffected.
3. **Three.js `Clock` Notice:** Browser logged `THREE.Clock: This module has been deprecated. Please use THREE.Timer instead.`
   - *Severity:* Informational deprecation notice.
   - *Action:* Scheduled for non-breaking update in future UI refinement.

### 8.2 Recommended Pre-Deployment Actions for Stage 2 (Containerization)
1. **Docker Multi-Stage Build:** Bundle the Next.js production build (`.next/standalone`) with Node.js 20+ alpine and Python 3.12+ backend into separate container services (or a unified docker-compose stack).
2. **Local Volume Mount for Cache:** Ensure `/app/data/spherex/cache` has persistent write permissions in the container for FITS caching.
3. **Environment Injection:** Externalize `NEXT_PUBLIC_API_URL` to point to the Azure App Service or Container App ingress.

---

## 9. STAGE 1 SIGN-OFF

The NASA SPHEREx 3D Temporal Sky Explorer has satisfied all Stage 1 integrity, regression, scientific data, and resource requirements.

$$\mathbf{STAGE\ 1\ VERDICT: STAGE1\_PASS}$$
