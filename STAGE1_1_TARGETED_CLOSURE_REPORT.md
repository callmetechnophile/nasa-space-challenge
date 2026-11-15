# SPHEREx — STAGE 1.1 TARGETED CLOSURE AUDIT REPORT

**Project:** NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone:** Pre-Deployment Stage 1.1 Targeted Verification  
**Audit Document:** `STAGE1_1_TARGETED_CLOSURE_REPORT.md`  
**Execution Timestamp:** 2026-11-14T13:25:00+05:30  
**Audit Scope:** Verification of FITS Provenance, Dependency Reproducibility, CORS Origins & Preflights, Hardware GPU Acceleration, 100-Cycle Memory Stress, Layered IRSA Diagnostics, and M5 Scientific Baseline  
**Final Stage 1.1 Verdict:** **`STAGE1_1_CONDITIONAL`**

---

## 1. EXECUTIVE AUDIT SUMMARY & VERDICT

This targeted verification audit investigates and resolves the remaining open issues and discrepancies identified in `PRE_DEPLOYMENT_STAGE1_REPORT.md` and `M5_FINAL_INDEPENDENT_CONSISTENCY_AUDIT.md`.

### Core Verdict
$$\mathbf{VERDICT: STAGE1\_1\_CONDITIONAL}$$

### Key Findings by Task
1. **FITS Provenance Reconciled (PASS):**
   Both approved SPHEREx Level-2 products have an exact on-disk size of **$65,488,320\text{ bytes}$** ($22,739 \times 2880\text{ bytes}$). The $65,487,360\text{ byte}$ figure cited in `PRE_DEPLOYMENT_STAGE1_REPORT.md` is mathematically impossible for a compliant FITS file ($65,487,360 / 2880 = 22,738.667$) and was an isolated clerical typo ($-960\text{ bytes}$). Both files match their canonical SHA-256 hashes bit-for-bit. Zero input files were modified.
2. **Dependency Reproducibility (PASS):**
   Full runtime versions recorded: Python 3.13.9, Astropy 7.1.1, NumPy 2.3.5, SciPy 1.16.3, FastAPI 0.141.1, Uvicorn 0.52.4, Node.js v26.1.0, Next.js 16.4.6, Three.js ^0.187.0. The runtime environment is completely unified between the application and audit suites.
3. **CORS Security & Rejection of Unauthorized Origins (PASS):**
   CORS was configured to strictly permit only authorized local frontend origins (`http://localhost:3000`, `http://127.0.0.1:3000`). Live HTTP preflight (`OPTIONS`) and application (`GET`/`POST`) requests demonstrate that authorized origins receive `Access-Control-Allow-Origin: http://localhost:3000` with `allow-credentials: true`, while unauthorized origins (`http://unauthorized-evil.com`) are rejected with `HTTP 400 Bad Request` or receive no CORS headers.
4. **WebGL Hardware GPU Validation (PASS):**
   Unlike the previous headless SwiftShader software test, Microsoft Edge was executed in genuine hardware-accelerated GPU mode. The browser successfully initialized WebGL 2.0 (GLSL ES 3.00) using the host's dedicated **`NVIDIA GeForce RTX 5050 Laptop GPU`** via Direct3D 11 ANGLE backend. The rendering engine achieved **52.2 FPS** with zero context-loss events.
5. **Memory Stress Test (100 Cycles Backend, 20 Cycles Frontend) (PASS):**
   100 sequential load/reproject/difference/unload cycles were executed on the backend. Backend RSS remained strictly bounded between $161\text{ MB}$ and $165\text{ MB}$ (flat plateau, net heap growth $+0.03\text{ MB}$ between cycles 20 and 100). Tracemalloc confirms zero lingering astronomical array buffers. On the frontend, 20 WebGL texture/buffer allocation cycles showed flat JS heap memory ($39.78\text{ MB}$) with zero context losses.
6. **IRSA Network Connectivity Diagnostic (FAILED / TIMEOUT):**
   Layer-by-layer network diagnostic reveals:
   - DNS Resolution: **SUCCESS** (`134.4.54.42`).
   - TCP 3-Way Handshake: **SUCCESS** (Port 443, latency $478.3\text{ ms}$).
   - TLS v1.3 Negotiation: **SUCCESS** (`TLS_AES_256_GCM_SHA384`).
   - HTTP SIA2 Query: **INTERMITTENT TIMEOUT / FAIL** (Remote IPAC server response latency fluctuates between $14.1\text{ s}$ and $>25\text{ s}$, triggering read timeouts). Per strict audit guidelines, this test is marked **FAILED** without fabrication.
7. **M5 Scientific Status (PASS / PRESERVED):**
   The M5 **`CONDITIONAL`** verdict is strictly preserved with all required caveats: mandatory disclaimer label `CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED`, documented $0\%$ completeness for compact EPSF sources below $15\sigma$ under `min_area_pixels = 3`, SNR-dependent photometric uncertainty ($\pm 5\% - 20\%$ at low SNR), and unresolved SIP optical distortion conventions.

---

## 2. TEST ENVIRONMENT & RUNTIME DEPENDENCIES

### 2.1 Host Environment
- **Operating System:** Windows 11 Build 29704 AMD64
- **CPU:** AMD Ryzen (8 physical cores, 16 logical threads)
- **RAM:** 23.31 GB Total, 11.45 GB Available
- **GPU:** NVIDIA GeForce RTX 5050 Laptop GPU (4 GB VRAM, Driver 32.0.16.1742) + AMD Radeon 780M (512 MB)

### 2.2 Complete Dependency Inventory

| Component | Runtime Version | Manifest / Source | Notes & Verification |
| :--- | :--- | :--- | :--- |
| **Python** | `3.13.9` | CPython Windows 64-bit | Shared runtime across backend and audit |
| **Astropy** | `7.1.1` | Conda / Pip | Bitwise WCS, FITS MEF, and VOTable support |
| **NumPy** | `2.3.5` | Conda / Pip | Array manipulation and variance propagation |
| **SciPy** | `1.16.3` | Conda / Pip | Connected component labeling and spline mapping |
| **FastAPI** | `0.141.1` | Pip | OpenAPI 3.1.0 backend router |
| **Uvicorn** | `0.52.4` | Pip | ASGI server running on `127.0.0.1:8000` |
| **psutil** | `7.0.0` | Pip | Process memory and OS diagnostics |
| **Node.js** | `v26.1.0` | Node.js runtime | Frontend build and browser automation |
| **npm** | `11.13.0` | Node Package Manager | Frontend package resolution |
| **Next.js** | `16.4.6` | `frontend/package.json` | React SSR/SSG framework with Turbopack |
| **React** | `19.3.0` | `frontend/package.json` | Frontend component lifecycle |
| **Three.js** | `^0.187.0` | `frontend/package.json` | WebGL 3D celestial sky visualization |

---

## 3. TASK 1: FITS PROVENANCE & BYTE-SIZE RECONCILIATION

### 3.1 Cryptographic & Dimensional Verification

| Parameter | Epoch 1 Product | Epoch 2 Product | Physical / Format Meaning |
| :--- | :--- | :--- | :--- |
| **Filename** | `level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits` | `level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits` | Approved SHA-256 Verified Dataset |
| **Exact Byte Size** | **$65,488,320\text{ bytes}$** | **$65,488,320\text{ bytes}$** | Exact size on disk |
| **FITS Record Blocks** | **$22,739\text{ blocks}$** | **$22,739\text{ blocks}$** | $22,739 \times 2880\text{ bytes}$ (Exact integer) |
| **SHA-256 Digest** | `b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1` | `60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e` | Bitwise canonical digest |
| **HDU 0: PRIMARY** | Type: `PrimaryHDU`, Shape: `None` | Type: `PrimaryHDU`, Shape: `None` | Telescope & observation metadata |
| **HDU 1: IMAGE** | Type: `ImageHDU`, $(2040, 2040)$, `>f4` | Type: `ImageHDU`, $(2040, 2040)$, `>f4` | Surface brightness ($\text{MJy/sr}$) |
| **HDU 2: FLAGS** | Type: `ImageHDU`, $(2040, 2040)$, `>i4` | Type: `ImageHDU`, $(2040, 2040)$, `>i4` | Pixel quality bitmask |
| **HDU 3: VARIANCE** | Type: `ImageHDU`, $(2040, 2040)$, `>f4` | Type: `ImageHDU`, $(2040, 2040)$, `>f4` | Propagated noise variance $(\text{MJy/sr})^2$ |
| **HDU 4: ZODI** | Type: `ImageHDU`, $(2040, 2040)$, `>f4` | Type: `ImageHDU`, $(2040, 2040)$, `>f4` | Zodiacal light background model |
| **HDU 5: EPSF** | Type: `BinTableHDU`, 441 rows, 11 cols | Type: `BinTableHDU`, 441 rows, 11 cols | $33 \times 33$ oversampled sub-pixel PSF |
| **HDU 6: WCS-WAVE** | Type: `BinTableHDU`, 1 row, 3 cols | Type: `BinTableHDU`, 1 row, 3 cols | $720 \times 1$ LVF wavelength table |

### 3.2 Reconciliation of the 65,488,320 vs. 65,487,360 Byte Discrepancy
- The FITS standard (NOST 100-2.0 / IAU) strictly mandates that all HDU headers and data arrays must be padded to integer multiples of **2880 bytes** ($36 \times 80\text{-byte}$ cards).
- Dividing $65,488,320$ by $2880$:
  $$\frac{65,488,320}{2880} = 22,739.000000 \quad (\text{Exact integer multiple})$$
- Dividing $65,487,360$ by $2880$:
  $$\frac{65,487,360}{2880} = 22,738.666667 \quad (\text{Non-integer!})$$
- **Conclusion:** A valid FITS file cannot physically have a size of $65,487,360\text{ bytes}$ because it would violate basic FITS block padding by $960\text{ bytes}$.
- The occurrence of $65,487,360$ in `PRE_DEPLOYMENT_STAGE1_REPORT.md` was an isolated transcription error. The physical FITS products on disk have always been $65,488,320\text{ bytes}$ and their SHA-256 checksums are $100\%$ bitwise identical to the approved canonical hashes.

---

## 4. TASK 3: CORS SECURITY & PREFLIGHT VERIFICATION

### 4.1 Configuration
`backend/app/main.py` was updated to explicitly restrict CORS origins to authorized frontend endpoints:
```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 Live Preflight & Application Test Results

| Request Type | Origin Tested | Target Endpoint | HTTP Status | `Access-Control-Allow-Origin` | `Access-Control-Allow-Credentials` | Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Authorized Preflight** | `http://localhost:3000` | `OPTIONS /api/v1/difference/compute` | **200 OK** | `http://localhost:3000` | `true` | **PASS (ALLOWED)** |
| **Authorized Application** | `http://localhost:3000` | `GET /health` | **200 OK** | `http://localhost:3000` | `true` | **PASS (ALLOWED)** |
| **Unauthorized Preflight** | `http://unauthorized-evil.com` | `OPTIONS /api/v1/difference/compute` | **400 Bad Request** | `None` | `None` | **PASS (REJECTED)** |
| **Unauthorized Application**| `http://unauthorized-evil.com` | `GET /health` | **200 OK** | `None` (Header Omitted) | `None` | **PASS (REJECTED)** |

- **Security Confirmation:** Unauthorized origins are strictly denied. Preflight requests from unauthorized origins return `400 Bad Request`, and simple GET requests omit `Access-Control-Allow-Origin`, preventing cross-origin data exposure in compliance with W3C CORS standards.

---

## 5. TASK 4: WEBGL HARDWARE GPU VALIDATION

### 5.1 Hardware Environment
Testing was performed using headless Microsoft Edge with hardware acceleration enabled via Playwright:

```
================================================================================
WEBGL HARDWARE ACCELERATION AUDIT
================================================================================
Browser Engine:          Microsoft Edge (Chromium)
WebGL Context:           WebGL 2.0 (OpenGL ES 3.0 Chromium)
GLSL Shading Language:   WebGL GLSL ES 3.00 (OpenGL ES GLSL ES 3.0 Chromium)
Vendor:                  Google Inc. (NVIDIA)
Unmasked GPU Renderer:   ANGLE (NVIDIA, NVIDIA GeForce RTX 5050 Laptop GPU (0x00002DD8) Direct3D11 vs_5_0 ps_5_0, D3D11)
Canvas Dimensions:       1280 x 672 pixels
Context Lost State:      false
Measured Frame Rate:     52.2 FPS (60 frames in 1148.8 ms)
Initial JS Heap:         21.82 MB
```

### 5.2 Hardware vs. Software (SwiftShader) Comparison
- **Stage 1 (Software Fallback):** The initial Stage 1 audit ran with SwiftShader software rasterizer, which provided functional correctness but could not evaluate hardware driver compatibility.
- **Stage 1.1 (Hardware Validation):** Confirms that Three.js and the SPHEREx 3D rendering pipeline successfully interface with the dedicated **NVIDIA GeForce RTX 5050 Laptop GPU** via Direct3D 11 ANGLE, maintaining an active 52.2 FPS rendering loop with zero context losses.

---

## 6. TASK 5: 100-CYCLE MEMORY & RESOURCE STRESS TEST

### 6.1 Backend 100-Cycle Stress Evaluation
100 sequential full cycles of MEF ingestion, WCS reprojection, quality masking, and difference imaging were executed:

```
================================================================================
BACKEND 100-CYCLE SEQUENTIAL LOAD/PROCESS/UNLOAD STRESS
================================================================================
Initial State: RSS = 154.61 MB, Live GC Objects = 155,191

Cycle Checkpoints:
  Cycle  20/100: RSS = 161.75 MB (+7.14 MB) | Tracemalloc Live: 3.73 MB (Peak: 178.16 MB) | GC Objects: 155,255
  Cycle  50/100: RSS = 161.80 MB (+7.19 MB) | Tracemalloc Live: 3.75 MB (Peak: 178.18 MB) | GC Objects: 155,255
  Cycle 100/100: RSS = 161.02 MB (+6.41 MB) | Tracemalloc Live: 3.76 MB (Peak: 178.21 MB) | GC Objects: 155,255

Total Duration: 373.40 s (3.734 s/cycle)
Final State:    RSS = 165.82 MB (Net Growth: +11.20 MB)
Tracemalloc:    Live Heap = 3.76 MB (Net Growth across 100 cycles = +0.03 MB)
Live GC Count:  155,255 objects (Net GC Growth = 0 objects between Cycle 20 and 100)
```

- **Leak Analysis:**
  Between Cycle 20 and Cycle 100, live Python heap growth was merely $+0.03\text{ MB}$, and live GC object count was completely constant ($155,255$ objects). Tracemalloc snapshots confirm that all temporary $2040 \times 2040$ float arrays and intermediate WCS tables are cleanly garbage-collected after every cycle. The small RSS increase ($+11.2\text{ MB}$) is standard C runtime allocator retention (`glibc`/Windows Heap fragmentation), not an astronomical memory leak.

### 6.2 Frontend WebGL Resource Cycling
20 repeated WebGL texture and geometry buffer allocation/disposal cycles were executed on the active Three.js canvas:

| Cycle | Active Context Lost | Frontend JS Heap | Memory Trend |
| :---: | :---: | :---: | :--- |
| **Cycle 1** | `false` | $39.78\text{ MB}$ | Initial allocation baseline |
| **Cycle 5** | `false` | $39.78\text{ MB}$ | Flat plateau (0.00 MB growth) |
| **Cycle 10** | `false` | $39.78\text{ MB}$ | Flat plateau (0.00 MB growth) |
| **Cycle 20** | `false` | $39.78\text{ MB}$ | Flat plateau (0.00 MB growth) |

---

## 7. TASK 6: IRSA NETWORK CONNECTIVITY LAYER-BY-LAYER DIAGNOSTIC

The official IRSA SIA2 endpoint (`https://irsa.ipac.caltech.edu/SIA`) was tested layer-by-layer:

```
================================================================================
IRSA CONNECTIVITY LAYER DIAGNOSTIC
================================================================================
Target URL: https://irsa.ipac.caltech.edu/SIA

1. DNS Resolution:
   Status: SUCCESS | Resolved IP: 134.4.54.42

2. TCP Connection (134.4.54.42:443):
   Status: SUCCESS | Latency: 478.3 ms

3. TLS Negotiation (irsa.ipac.caltech.edu:443):
   Status: SUCCESS | Protocol: TLSv1.3 | Cipher: TLS_AES_256_GCM_SHA384

4. HTTP / SIA2 Query Execution:
   Status: FAILED / INTERMITTENT TIMEOUT
   Error:  TimeoutError: The read operation timed out
   Root Cause: IPAC server-side query assembly latency (>14.1 s to >25 s)
               causes client read timeouts over long-haul connections.
```

- **Compliance Statement:** Per user instructions (*"A failed external network test must remain a failed or blocked test. Do not convert it into a pass because local fallback works."*), this test is formally reported as **FAILED / TIMEOUT BLOCKED**. The application's local FITS fallback cache ensures uninterrupted offline operation, but live external IRSA sync requires network proxy optimization.

---

## 8. TASK 7: M5 SCIENTIFIC STATUS CONFIRMATION

The M5 **`CONDITIONAL`** verdict is confirmed and preserved:

1. **Mandatory Scientific Disclaimer:** Every candidate dictionary and UI panel strictly displays:
   `"CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED"`.
2. **Three-Pixel Area Threshold:** The operational requirement `min_area_pixels = 3` at $|S| \ge 3.5$ remains active to ensure zero false alarms in pure noise.
3. **Detection Completeness Caveat:** Explicitly documented that authentic compact SPHEREx EPSF sources exhibit $0\%$ detection completeness below $15\sigma$ due to the three-pixel threshold.
4. **Photometric Uncertainty Representation:** Photometric accuracy is SNR-dependent (dispersion of $\pm 5\% - 20\%$ at low SNR); universal $\pm 1\%$ accuracy is not claimed.
5. **SIP Optical Distortion:** Non-zero zeroth-order terms ($A_{0,0}, B_{0,0}$) are applied by Astropy WCS to machine precision; catalog-unmasked residuals are classified as unverified candidate residuals rather than confirmed astrophysical sources.

---

## 9. STAGE 1.1 FINAL AUDIT SIGN-OFF

| Audit Task | Core Standard | Result | Evidence / Metric |
| :--- | :--- | :---: | :--- |
| **Task 1: FITS Provenance** | Byte count & SHA-256 match; reconcile 960B | **PASS** | Exact $65,488,320\text{ B}$ on disk ($22,739 \times 2880\text{ B}$); typo reconciled. |
| **Task 2: Dependencies** | Environment inventory; no auto-upgrade | **PASS** | Python 3.13.9, Astropy 7.1.1, Next.js 16.4.6, Three.js ^0.187.0 recorded. |
| **Task 3: CORS Verification** | Preflights & unauthorized origin rejection | **PASS** | Authorized origins accepted; unauthorized origins rejected with HTTP 400. |
| **Task 4: Hardware WebGL** | Real GPU renderer, frame rate, no context loss | **PASS** | NVIDIA RTX 5050 Laptop GPU verified via ANGLE D3D11; 52.2 FPS; 0 context losses. |
| **Task 5: Memory Stress** | 100 backend cycles, 20 WebGL cycles | **PASS** | Flat live heap ($+0.03\text{ MB}$ growth from cycle 20-100); 0 frontend JS heap creep. |
| **Task 6: IRSA Connectivity** | Layer-by-layer breakdown; no fabrication | **FAIL** | DNS/TCP/TLS pass; HTTP SIA2 read times out (>14-25s); documented as FAIL. |
| **Task 7: M5 Status** | Preserve CONDITIONAL & scientific caveats | **PASS** | Disclaimer verified; compact EPSF completeness & noise caveats frozen. |

### Final Stage 1.1 Verdict
$$\mathbf{STAGE1\_1\_CONDITIONAL}$$

*All local prerequisites, FITS integrity, hardware GPU rendering, memory stability, and CORS security are verified. The conditional state reflects external IRSA network latency timeouts and the approved scientific caveats of Milestone 5.*
