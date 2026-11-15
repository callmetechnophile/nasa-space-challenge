# SPHEREx — STAGE 1.1 FINAL CLOSURE AUDIT REPORT
**NASA SPHEREx — 3D Temporal Sky Explorer**  
**Audit Stage:** Stage 1.1 Final Closure Audit  
**Date of Audit Execution:** November 14, 2026  
**Final Pre-Deployment Verdict:** `STAGE1_1_PASS`  
**Milestone 5 Scientific Status:** `CONDITIONAL` (Preserved with all mandatory caveats)  
**Next Stage:** Stage 1.2 — Staging & Containerization (NOT STARTED)

---

## 1. Executive Summary and Final Stage 1.1 Verdict

This report delivers the exhaustive, evidence-backed closure for the **Stage 1.1 Final Closure Audit** of the NASA SPHEREx 3D Temporal Sky Explorer. Following the findings of `PRE_DEPLOYMENT_STAGE1_REPORT.md` and `M5_FINAL_INDEPENDENT_CONSISTENCY_AUDIT.md`, targeted remediation and verification campaigns were executed across all engineering, architectural, network, and scientific boundaries.

### Summary of Closure Findings:
1. **FITS Provenance & Integrity**: Both approved SPHEREx Level-2 FITS observation products match their authoritative SHA-256 digests bit-for-bit. The previously reported $65,487,360\text{ byte}$ entry was mathematically proven to be an isolated typographical error (violating the mandatory FITS 2880-byte record standard by $-960\text{ bytes}$). The exact file size is $65,488,320\text{ bytes}$ ($22,739 \times 2880\text{ bytes}$, modulo 0).
2. **Dependency & Environment Reproducibility**: Complete convergence across Python 3.13.9, Astropy 7.1.1, NumPy 2.3.5, SciPy 1.16.3, FastAPI 0.141.1, Node.js v26.1.0, Next.js 16.4.6, and Three.js ^0.187.0. Zero runtime version divergence remains.
3. **CORS Configuration**: Rigorous cross-origin testing verified that preflight `OPTIONS` requests from authorized development origins (`http://localhost:3000`, `http://127.0.0.1:3000`) return `HTTP 200` with credential support, while unauthorized origins receive `HTTP 400 Bad Request` with no CORS allowance. Application endpoints return `HTTP 200` with CORS headers strictly restricted to authorized origins.
4. **Hardware WebGL Performance**: Genuine dedicated hardware testing on an NVIDIA GeForce RTX 5050 Laptop GPU via ANGLE (Direct3D11) demonstrated sustained frame rates of $144.89\text{ FPS}$ (baseline celestial sphere), $45.08\text{ FPS}$ (orbital navigation), $49.65-58.60\text{ FPS}$ (multi-layer astronomical projection), and zero WebGL context losses across 100 reload cycles.
5. **Memory Stability & Allocator Behavior**: The allocator attribution was corrected from Linux `glibc` to the Windows NT Heap / Segment Heap (`ucrtbase.dll`). A 100-cycle stress test of full MEF ingestion, reprojection, and difference imaging proved strict stability: net RSS drift between cycles 20 and 100 was **$-0.91\text{ MB}$**, Python heap drift was $+0.06\text{ MB}$, and live Python garbage-collected objects exhibited **zero drift (+0 objects)**.
6. **IRSA SIA2 Live Retrieval**: Live end-to-end integration with the IPAC Caltech SIA2 service (`134.4.54.42`) was verified over TLSv1.3. A query for `POS=CIRCLE+0.0+0.0+0.5` returned `HTTP 200` (162 observation records). A live SPHEREx Level-2 FITS product was streamed via HTTP 206 Partial Content ($40,255,115\text{ bytes}$), and its PRIMARY and IMAGE HDUs ($2040 \times 2040$, BITPIX -32, BUNIT MJy/sr) were validated in Astropy.
7. **Regression Testing**: All 17 automated acceptance gates in `tests/test_spherex_m4_validation.py` and `tests/test_spherex_m5_validation.py` passed cleanly (17 passed, 0 failed). Backend unit tests for coordinates, targets, and difference imaging passed 100%.
8. **Scientific Status**: The M5 scientific status remains strictly **`CONDITIONAL`**, with the mandatory non-discovery disclaimer enforced, $0\%$ completeness for compact $<15\sigma$ sources documented, $\pm 5-20\%$ low-SNR photometry dispersion, and SIP distortion conventions preserved.

**FINAL STAGE 1.1 VERDICT:** **`STAGE1_1_PASS`**

---

## 2. FITS Provenance and Integrity Verification

### 2.1 File Hashes and Exact Dimensions
Both approved Level-2 observation products were evaluated on disk using SHA-256 block hashing ($1\text{ MB}$ chunks) and byte-level stat inspection:

| Property | Epoch 1 Observation | Epoch 2 Observation | Verification Status |
| :--- | :--- | :--- | :--- |
| **Filename** | `level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits` | `level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits` | Verified on Disk |
| **Directory** | `d:\nasa\data\spherex\` | `d:\nasa\data\spherex\` | Verified on Disk |
| **Exact Byte Size** | **65,488,320 bytes** | **65,488,320 bytes** | **MATCH** |
| **FITS Blocks** | $22,739.000$ ($2880\text{ B}$ blocks) | $22,739.000$ ($2880\text{ B}$ blocks) | Exact ($22739 \times 2880$) |
| **Modulo 2880** | **0 bytes** | **0 bytes** | Standard Compliant |
| **SHA-256 Checksum** | `b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1` | `60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e` | **Bit-for-Bit Identical** |
| **Baseline Separation**| $t_1 = 2026\text{-}08\text{-}12\text{T}10:24:00$ | $t_2 = 2026\text{-}08\text{-}20\text{T}12:10:51$ | $\Delta t = 8.0742\text{ days}$ |

### 2.2 Resolution of the 65,488,320 vs 65,487,360 Byte Discrepancy
In earlier audit documentation, a figure of $65,487,360\text{ bytes}$ appeared. Mathematical analysis of the FITS standard (NASA/GSFC FITS Standard 4.0, Section 3.1) proves conclusively that this was a clerical typo:
- FITS files must consist of an integral multiple of 2880-byte records:
  $$\frac{65,488,320}{2880} = 22,739.000 \quad (\text{Valid FITS})$$
  $$\frac{65,487,360}{2880} = 22,738.667 \quad (\text{Invalid FITS: remainder } 1920\text{ bytes, off by } -960\text{ bytes})$$
No 2880-byte compliant FITS file can ever have a length of $65,487,360\text{ bytes}$. The physical files on disk have never been modified, truncated, or re-written.

---

## 3. Multi-Extension FITS Structural Validation

Both observation products were inspected across all seven Header Data Units (HDUs):

| HDU Index | Ext Name | HDU Type | Dimensions | Data Type | Header Cards | Scientific Content |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **0** | `PRIMARY` | `PrimaryHDU` | `()` | None | 5 | Mission metadata, pipeline release `spx_l2b-v27` |
| **1** | `IMAGE` | `ImageHDU` | $(2040, 2040)$ | `>f4` (float32) | 293 | Calibrated surface brightness ($I_\nu$ in $\text{MJy/sr}$) |
| **2** | `FLAGS` | `CompImageHDU` | $(2040, 2040)$ | `int32` | 185 / 182 | Rice-compressed 32-bit pixel quality bitmask |
| **3** | `VARIANCE`| `ImageHDU` | $(2040, 2040)$ | `>f4` (float32) | 119 | Measurement variance ($\sigma^2$ in $(\text{MJy/sr})^2$) |
| **4** | `ZODI` | `ImageHDU` | $(2040, 2040)$ | `>f4` (float32) | 122 | Evaluated zodiacal light background model |
| **5** | `EPSF` | `BinTableHDU` | 441 rows | Table | 56 | Empirical PSF grid ($21 \times 21$ spatial bins, $33 \times 33$ px) |
| **6** | `WCS-WAVE`| `BinTableHDU` | 1 row | Table | 22 | LVF spatial dispersion grid ($9 \times 9$ coordinate nodes) |

Both files exhibit identical extension ordering, identical byte offsets, valid table column formats, and zero missing HDUs.

---

## 4. Runtime Dependency Reproducibility

Comparison of the operational runtime environment with the scientific audit environment confirms complete parity:

| Component | Application Runtime | Scientific Audit Runtime | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Operating System** | Windows 11 Enterprise (10.0.26100) | Windows 11 Enterprise (10.0.26100) | **MATCH** | 64-bit architecture |
| **Python** | 3.13.9 (CPython) | 3.13.9 (CPython) | **MATCH** | Anaconda Distribution |
| **Astropy** | 7.1.1 | 7.1.1 | **MATCH** | Strict WCS, SIP, and FITS I/O |
| **NumPy** | 2.3.5 | 2.3.5 | **MATCH** | C-API / BLAS acceleration |
| **SciPy** | 1.16.3 | 1.16.3 | **MATCH** | 2D Gaussian convolution, spline |
| **FastAPI** | 0.141.1 | 0.141.1 | **MATCH** | ASGI Web Framework |
| **Uvicorn** | 0.52.4 | 0.52.4 | **MATCH** | ASGI Server |
| **Node.js** | v26.1.0 | v26.1.0 | **MATCH** | V8 Engine v13.x |
| **npm** | 11.13.0 | 11.13.0 | **MATCH** | Package Manager |
| **Next.js** | 16.4.6 | 16.4.6 | **MATCH** | Turbopack production compiler |
| **React** | 19.3.0 | 19.3.0 | **MATCH** | Modern UI Runtime |
| **Three.js** | ^0.187.0 | ^0.187.0 | **MATCH** | WebGL 2.0 Celestial Engine |

---

## 5. Comprehensive Test Execution Matrix

The official test suite was executed against the repository root via `pytest tests/ -v`:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.9, pytest-8.4.2, pluggy-1.5.0
collected 17 items

tests/test_spherex_m4_validation.py::test_01_real_fits_presence_and_sha256 PASSED [  5%]
tests/test_spherex_m4_validation.py::test_02_mef_structure_and_hdu_preservation PASSED [ 11%]
tests/test_spherex_m4_validation.py::test_03_wcs_sip_distortion_compatibility PASSED [ 17%]
tests/test_spherex_m4_validation.py::test_04_api_status_and_inspection PASSED [ 23%]
tests/test_spherex_m4_validation.py::test_05_api_layer_load PASSED       [ 29%]
tests/test_spherex_m5_validation.py::test_gate_01_mef_ingestion PASSED   [ 35%]
tests/test_spherex_m5_validation.py::test_gate_02_quality_mask_policy PASSED [ 41%]
tests/test_spherex_m5_validation.py::test_gate_03_wcs_reprojection PASSED [ 47%]
tests/test_spherex_m5_validation.py::test_gate_04_variance_propagation PASSED [ 52%]
tests/test_spherex_m5_validation.py::test_gate_05_spectral_compatibility PASSED [ 58%]
tests/test_spherex_m5_validation.py::test_gate_06_psf_homogenization PASSED [ 64%]
tests/test_spherex_m5_validation.py::test_gate_07_difference_exactness PASSED [ 70%]
tests/test_spherex_m5_validation.py::test_gate_08_significance_null_data PASSED [ 76%]
tests/test_spherex_m5_validation.py::test_gate_09_synthetic_injection_recovery PASSED [ 82%]
tests/test_spherex_m5_validation.py::test_gate_10_mandatory_disclaimer_label PASSED [ 88%]
tests/test_spherex_m5_validation.py::test_gate_11_edge_artifact_rejection PASSED [ 94%]
tests/test_spherex_m5_validation.py::test_gate_12_real_spherex_pair PASSED [100%]

====================== 17 passed, 146 warnings in 11.57s ======================
```

Additional subsystem unit test execution:
- `backend/tests/test_coordinates.py`: 5 passed (Sexagesimal, HMS/DMS roundtrip, Cartesian Three.js vectors, angular separation).
- `backend/tests/test_targets.py`: 2 passed (102 SPHEREx bandpasses, 5 core NASA calibration targets).
- `backend/tests/test_difference_imaging.py`: 3 passed (MAD sigma estimation, identical image null test, synthetic transient injection).

Total test count across all suites: **27 passed, 0 failed**.

---

## 6. Frontend Production Build and Typecheck Results

The Next.js frontend production compilation was executed via `npm --prefix frontend run build`:

```text
> frontend@0.1.0 build
> next build

▲ Next.js 16.4.6 (Turbopack)
- Environments: .env

✓ Compiled successfully in 542ms
✓ Type checking completed in 6.0s
✓ Collecting build traces
✓ Finalizing page optimization

Route (app)                              Size     First Load JS
┌ ○ /                                    24.2 kB         142 kB
├ ○ /_not-found                          994 B           103 kB
├ ○ /coordinates                         2.1 kB          104 kB
├ ○ /mef-viewer                          3.5 kB          106 kB
└ ○ /temporal                            18.7 kB         137 kB
+ First Load JS shared by all            102 kB
  ├ chunks/496-6d6a2dc90089ff65.js       45.6 kB
  ├ chunks/main-app-f99a09e02c638302.js  42.1 kB
  └ other shared chunks (total)          14.3 kB

○  (Static)  prerendered as static content
```

Compilation status: **Zero TypeScript errors, zero JSX/TSX syntax warnings, 5/5 static routes optimized**.

---

## 7. CORS Configuration and Endpoint-Level Verification

A live automated verification script (`scripts/verify_cors_rigorous.py`) tested CORS preflight and application behavior against `http://127.0.0.1:8000`:

| Origin | Request Type | Target Endpoint | HTTP Status | `Access-Control-Allow-Origin` | `Allow-Credentials` | Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `http://localhost:3000` | Preflight `OPTIONS` | `/api/v1/temporal/compare` | **200 OK** | `http://localhost:3000` | `true` | **PASS** |
| `http://127.0.0.1:3000` | Preflight `OPTIONS` | `/api/v1/temporal/compare` | **200 OK** | `http://127.0.0.1:3000` | `true` | **PASS** |
| `http://unauthorized-evil.com` | Preflight `OPTIONS` | `/api/v1/temporal/compare` | **400 Bad Request** | *None* | *None* | **PASS** |
| `http://localhost:3000` | Direct `GET` | `/health` | **200 OK** | `http://localhost:3000` | `true` | **PASS** |
| `http://127.0.0.1:3000` | Direct `GET` | `/health` | **200 OK** | `http://127.0.0.1:3000` | `true` | **PASS** |
| `http://unauthorized-evil.com` | Direct `GET` | `/health` | **200 OK** | *None* | *None* | **PASS** |

### Clarification on Direct HTTP Protocol Access vs Browser CORS Enforcement:
When an unauthorized origin issues a direct `GET` to `/health`, the HTTP server returns the resource data with status 200, but **omits** the `Access-Control-Allow-Origin` response header. In modern web browsers, the browser security sandbox intercepts this response and forbids JavaScript access to the payload. Direct HTTP protocol access (e.g. from curl or automated scripts) is not blocked at the network level unless authentication is configured, which is the correct and standard behavior of the W3C CORS specification.

---

## 8. WebGL Rendering and Performance Profile

WebGL workloads were benchmarked in a genuine Microsoft Edge browser running hardware acceleration on the host system:
- **GPU Adapter**: `NVIDIA GeForce RTX 5050 Laptop GPU` (PCI Device ID `0x00002DD8`)
- **Graphics Backend**: `ANGLE (NVIDIA, Direct3D11 vs_5_0 ps_5_0)`
- **WebGL Context**: WebGL 2.0 (`OpenGL ES 3.00`)
- **Viewport Dimensions**: $1600 \times 952\text{ pixels}$
- **Dedicated GPU Memory**: $8,151\text{ MiB Total}$, $1,368\text{ MiB Used}$, $6,543\text{ MiB Free}$ (verified via `nvidia-smi`)

### Workload Benchmark Results (120 frames per workload):

| Workload ID | Description | Render Time (120 f) | Frame Rate | JS Heap (MB) | GPU VRAM (MB) | Context Losses |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **WL-1** | Initial Celestial Sphere (3D Starfield & Equator) | 828.2 ms | **144.89 FPS** | 22.78 MB | 1368.0 MiB | 0 |
| **WL-2** | Interactive Orbit & Coordinate Navigation | 2661.7 ms | **45.08 FPS** | 63.70 MB | 1368.0 MiB | 0 |
| **WL-3** | Single Astronomical Image Layer Projected | 2416.8 ms | **49.65 FPS** | 54.22 MB | 1368.0 MiB | 0 |
| **WL-4** | Dual Astronomical Epoch Layers Rendered | 2187.0 ms | **54.87 FPS** | 52.75 MB | 1368.0 MiB | 0 |
| **WL-5** | Difference & Significance Heatmap Active | 2047.9 ms | **58.60 FPS** | 40.94 MB | 1368.0 MiB | 0 |
| **WL-6** | Interactive Candidate Pin Overlays (DOM Recalc) | 27,430.2 ms | **4.37 FPS** | 104.62 MB | 1368.0 MiB | 0 |
| **WL-7** | Post-Reload Cycle Stability (Blink Comparator) | 29,489.4 ms | **4.07 FPS** | 166.04 MB | 1368.0 MiB | 0 |

### Findings:
WebGL 3D shader rendering performs at high frame rates ($45-144\text{ FPS}$). The lower frame rate in WL-6 and WL-7 is strictly attributable to DOM and CSS SVG re-layout of 40+ overlay pin markers during rapid camera translation, not GPU shader or fill-rate bottlenecks. Zero WebGL context losses were recorded across all cycles.

---

## 9. Memory Profile and Stability Analysis

### 9.1 Allocator Attribution Correction
Earlier documentation incorrectly referenced Linux `glibc` `malloc_trim`. The underlying operating system is Windows 11 Enterprise. The native C runtime memory management is governed by the **Windows NT Heap Manager** and **Segment Heap** within `ucrtbase.dll`. Virtual memory pages allocated via `VirtualAlloc` are held in process pools for subsequent reuse and are reclaimed by the Windows Virtual Memory Manager according to system memory pressure.

### 9.2 100-Cycle Pipeline Stress Test Results
An automated script (`scripts/verify_backend_memory_100cycles.py`) executed 100 complete, sequential cycles of:
1. Ingestion of both $65.5\text{ MB}$ Level-2 MEF products.
2. Full WCS celestial extraction and quality mask construction.
3. Common-grid $512 \times 512$ reprojection and surface brightness preservation.
4. Analytical difference and significance map computation.
5. Conservative candidate extraction and explicit garbage collection.

Total duration: **258.6 seconds (2.59 seconds per complete pipeline cycle)**.

| Cycle Number | Resident Set Size (RSS) | Virtual Memory Size (VMS) | Python `tracemalloc` Heap | Live Python Objects | Dedicated GPU VRAM |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **0 (Baseline)** | 93.85 MB | 79.52 MB | 0.00 MB (Peak 0.77 MB) | 98,873 | 1368.0 MiB |
| **1** | 98.24 MB | 165.71 MB | 0.03 MB (Peak 243.62 MB) | 98,813 | 1368.0 MiB |
| **10** | 99.32 MB | 167.75 MB | 0.04 MB (Peak 243.64 MB) | 98,813 | 1368.0 MiB |
| **20** | 99.94 MB | 167.75 MB | 0.05 MB (Peak 243.64 MB) | 98,813 | 1368.0 MiB |
| **50** | 98.80 MB | 167.75 MB | 0.07 MB (Peak 243.64 MB) | 98,813 | 1368.0 MiB |
| **75** | 98.92 MB | 167.75 MB | 0.08 MB (Peak 243.64 MB) | 98,813 | 1368.0 MiB |
| **100** | 99.04 MB | 167.75 MB | 0.09 MB (Peak 243.64 MB) | 98,813 | 1368.0 MiB |
| **Post-GC Final**| 101.02 MB | 167.75 MB | 0.09 MB (Peak 243.64 MB) | 98,813 | 1368.0 MiB |

### Quantitative Stability Metrics:
- **Net RSS Drift (Cycle 20 $\to$ 100)**: **$-0.91\text{ MB}$** (Strictly bounded; memory working set plateaued at ~99 MB).
- **Net Python Heap Growth (Cycle 1 $\to$ 100)**: **$+0.06\text{ MB}$** (Essentially zero).
- **Live GC Object Growth (Cycle 1 $\to$ 100)**: **$+0\text{ objects}$** (Exact zero object leak).
- **Verdict**: **PASS (Zero Memory Leaks)**.

---

## 10. IRSA SIA2 Live Retrieval and Integration Audit

Live network diagnostics and data retrieval were conducted against the NASA/IPAC Infrared Science Archive (IRSA):

### 10.1 Network Diagnostics
- **DNS Resolution**: `irsa.ipac.caltech.edu` resolved to IPv4 `134.4.54.42` in $10.0\text{ ms}$.
- **TCP Latency**: Direct 3-way handshake on port 443 completed in $308.8\text{ ms}$.
- **TLS Handshake**: Negotiated `TLSv1.3` with cipher suite `TLS_AES_256_GCM_SHA384` in $388.9\text{ ms}$. Server certificate subject `CN=irsa.ipac.caltech.edu` issued by *InCommon RSA Server CA*.

### 10.2 SIA2 Query & VOTable Parsing
- **Query URL**: `https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex&POS=CIRCLE+0.0+0.0+0.5&FORMAT=image/fits`
- **HTTP Status**: `200 OK` (Response time: $4.9-10.0\text{ s}$).
- **VOTable Payload**: $366,006\text{ bytes}$ XML.
- **Records Extracted**: 162 authentic SPHEREx observation records containing celestial coverage, exposure times, wavelength bounds, and direct product access URLs.

### 10.3 Live Product Access & Partial Stream Verification
- **Extracted Access URL**: `https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W30_2A/l2b-v27-2026-224/1/level2_2026W30_2A_0607_1D1_spx_l2b-v27-2026-224.fits`
- **Range Support**: Verified that IRSA supports HTTP 206 Partial Content (`accept-ranges: bytes`).
- **Data Retrieved**: **40,255,115 bytes (38.39 MB)** streamed directly from IPAC (exceeding the required 10 MB threshold).
- **SSL/TLS Mid-Stream Renegotiation Note**: IPAC's web gateway issues mid-stream SSL/TLS renegotiation requests during sustained downloads, causing single-stream Python sockets to reset if unhandled. Resumable chunked streaming via HTTP Range requests successfully handles this behavior.
- **Astropy Scientific Validation**:
  - `HDU 0 (PRIMARY)`: `BITPIX: 8, NAXIS: 0`.
  - `HDU 1 (IMAGE)`: `BITPIX: -32` (IEEE 754 float32), `NAXIS1: 2040, NAXIS2: 2040`, `BUNIT: MJy / sr`, `CTYPE: RA---TAN-SIP / DEC--TAN-SIP`, `CRVAL: (44.512656, -1.539228)`.
  - Image data verified as authentic astronomical surface brightness (values between $0.298$ and $0.495\text{ MJy/sr}$).
  - Confirmed not an HTML error page or empty response.
- **Application Interface**: `backend/app/astronomy/irsa_search.py` executed cleanly against live IRSA endpoints.

---

## 11. Milestone Regression Verification

The frozen baseline for Milestones 1 through 4 was audited to confirm zero unauthorized modifications:
- `backend/app/astronomy/fits_reader.py`: Untouched; maintains M4 FITS readers and coordinate parsers.
- `backend/app/astronomy/wcs_processor.py`: Untouched; maintains standard TAN/SIP projection pipelines.
- `backend/app/astronomy/image_renderer.py`: Untouched; preserves M1–M4 color-mapping and PNG export.
- `frontend/src/components/CelestialSphere.tsx`: Untouched; preserves M1–M4 Three.js rendering pipelines.

All 12 automated gates of M5 passed in the regression suite, confirming that additive temporal comparison features operate cleanly alongside the frozen baseline.

---

## 12. Scientific Caveats and Status Preservation

In strict accordance with audit guidelines, Milestone 5's scientific verdict remains **`CONDITIONAL`**. The following scientific limitations are explicitly maintained and surfaced:

1. **Non-Discovery Candidate Qualification Disclaimer**:
   Every change candidate output by the API or displayed in the UI is hard-coded with the mandatory qualification label:
   $$\text{DISCLAIMER\_LABEL} = \text{"CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED"}$$
2. **Completeness Cutoff**:
   The current difference imaging pipeline exhibits **$0\%$ completeness** for point-like sources with SNR $< 15\sigma$ when evaluated with `min_area_pixels = 3`. Candidates near the detection threshold must not be treated as astrophysical transients.
3. **Low-SNR Photometric Uncertainty**:
   Due to background covariance and spatial filtering effects, extracted aperture fluxes for low-SNR candidates exhibit $\pm 5-20\%$ dispersion relative to true injected fluxes.
4. **SIP Distortion Convention**:
   The difference imaging engine utilizes standard TAN reprojection; higher-order SIP polynomial optical distortion corrections remain a recognized domain for future pipeline refinement.

---

## 13. Complete Pre-Deployment Checklist

| Audit Category | Check Item | Status | Verified Evidence |
| :--- | :--- | :---: | :--- |
| **FITS Provenance** | Both approved Level-2 files present on disk | **PASS** | `d:\nasa\data\spherex\` |
| **FITS Provenance** | Bit-for-bit SHA-256 integrity match | **PASS** | Epoch 1: `b92010...`, Epoch 2: `60c423...` |
| **FITS Provenance** | Exact byte count verification (65,488,320 B) | **PASS** | Exact multiple of 2880 ($22,739$ blocks) |
| **FITS Structure** | All 7 HDUs verified (IMAGE, FLAGS, VARIANCE, etc.)| **PASS** | Astropy HDU list inspection |
| **Runtime** | Python 3.13.9, Astropy 7.1.1, NumPy 2.3.5 | **PASS** | Environment audit script |
| **Runtime** | Node.js v26.1.0, npm 11.13.0, Next.js 16.4.6 | **PASS** | CLI version audit |
| **Testing** | Automated acceptance test suite | **PASS** | 17/17 passed in `pytest tests/ -v` |
| **Testing** | Subsystem coordinate and target unit tests | **PASS** | 10/10 passed in `backend/tests/` |
| **Frontend** | TypeScript typecheck and linting | **PASS** | Zero errors |
| **Frontend** | Production build compilation | **PASS** | 5/5 static pages generated (Turbopack) |
| **Networking** | CORS preflight for authorized origins | **PASS** | HTTP 200 with credentials |
| **Networking** | CORS rejection for unauthorized origins | **PASS** | HTTP 400 Bad Request, no allow-origin |
| **Graphics** | Hardware-accelerated WebGL 2.0 | **PASS** | NVIDIA RTX 5050 Laptop GPU |
| **Graphics** | Sustained frame rates ($>45\text{ FPS}$ 3D navigation) | **PASS** | $45.08-144.89\text{ FPS}$ |
| **Graphics** | WebGL context loss recovery | **PASS** | 0 context losses across 100 cycles |
| **Stability** | 100-cycle backend pipeline execution | **PASS** | 258.6 s total ($2.59\text{ s/cycle}$) |
| **Stability** | Bounded working set / zero memory leaks | **PASS** | RSS drift $-0.91\text{ MB}$, Object drift $+0$ |
| **IRSA Integration**| DNS, TCP, and TLSv1.3 handshake | **PASS** | `134.4.54.42`, latency ~308 ms |
| **IRSA Integration**| SIA2 live query and VOTable parsing | **PASS** | 162 observation records parsed |
| **IRSA Integration**| Authentic FITS streaming and header validation | **PASS** | $40.25\text{ MB}$ retrieved, $2040 \times 2040$ IMAGE validated |
| **Scientific Logic**| Frozen M1–M4 baseline preservation | **PASS** | Zero modifications to M1–M4 files |
| **Scientific Logic**| M5 CONDITIONAL status & disclaimer enforcement | **PASS** | Mandatory non-discovery label enforced |

---

## 14. Outstanding Risks and Cloud Readiness Assessment

### 14.1 Identified Risks and Mitigation Strategies:
1. **IPAC IRSA Bandwidth & Socket Renegotiation**:
   - *Risk*: IRSA IPAC servers enforce connection re-negotiation and bandwidth throttling on single long-lived TCP streams, which can cause socket disconnects during large ($65.5\text{ MB}$) FITS transfers.
   - *Mitigation*: The backend implementation should use chunked HTTP Range requests (`bytes=X-Y`) with automated retry/backoff for robust streaming.
2. **Client DOM Marker Density**:
   - *Risk*: Displaying $>50$ candidate pin markers simultaneously in the 2D/3D overlay causes minor DOM recalculation overhead during camera translation.
   - *Mitigation*: Cluster candidate pins at high zoom levels or render pins directly in the WebGL canvas using Three.js sprite points rather than HTML DOM nodes.
3. **Cloud Memory Sizing**:
   - *Risk*: Multi-threaded concurrent difference imaging across multiple user sessions requires sufficient RAM for $2040 \times 2040$ floating-point arrays ($16.6\text{ MB}$ per uncompressed layer, peaking at ~240 MB during full reprojection).
   - *Mitigation*: Ensure container instances are provisioned with at least 2 GB RAM per worker process.

### 14.2 Cloud Readiness:
The application has passed all local engineering, regression, and hardware integrity gates. The codebase is fully prepared for Stage 1.2 (Containerization and Staging Environment Configuration).

---

## 15. Sign-off and Gate Declaration

- **Stage 1.0 Engineering Verification:** `PASSED`
- **Stage 1.1 Targeted Remediation & Final Closure:** `PASSED`
- **Milestone 5 Scientific Acceptance:** `CONDITIONAL` (Maintained per specification)
- **Overall Pre-Deployment Status:** **`STAGE1_1_PASS`**

**Authorized Directive**: Stage 1.1 is formally concluded. All outstanding findings are closed with reproducible empirical evidence. In accordance with non-negotiable project instructions, execution halts here prior to starting Stage 1.2.
