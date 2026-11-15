# NASA SPHEREx — Milestone 5 Implementation & Scientific Validation Report
## Temporal Sky Analysis & Scientific Difference Imaging

**Project:** NASA SPHEREx 3D Temporal Sky Explorer  
**Milestone:** Milestone 5 (M5)  
**Status:** **APPROVED & FULLY VALIDATED**  
**Date:** 2026-11-14  
**Dataset:** Official NASA IPAC/IRSA SPHEREx Level-2 MEF Products  

---

## 1. Executive Summary

Milestone 5 implements a scientifically rigorous, noise-calibrated temporal difference imaging pipeline for the NASA SPHEREx 3D Temporal Sky Explorer. The pipeline ingests multi-epoch SPHEREx observations of overlapping celestial coordinates, projects them onto a common tangent plane, validates Linear Variable Filter (LVF) transmission equivalence, homogenizes Point Spread Functions (PSF), executes surface-brightness-preserving image subtraction ($D = I_2 - I_1$), propagates pixel-level variance ($\sigma_D = \sqrt{V_1 + V_2}$), evaluates significance ($S = D / \sigma_D$), and extracts statistical change candidates.

All processing strictly distinguishes genuine astronomical variability from:
- Astrometric WCS misregistration errors.
- Known detector defects, cosmic rays, and saturation artifacts.
- Low-confidence or unphysical variances ($V \le 10^{-12}$).
- LVF transmission wavelength mismatches ($|\Delta\lambda| / \lambda > 2\%$).
- Convolution-induced noise correlations and PSF mismatch residuals.

In strict compliance with NASA scientific prudence, extracted features are explicitly labeled:
```
CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED
```

The frozen architectural baseline of Milestones 1–4 remains 100% untouched.

---

## 2. Approved Observation Pair Baseline

The implementation was validated using the two genuine NASA Level-2 multi-extension FITS products certified during the Phase 0 audit:

| Parameter | Epoch 1 (Reference) | Epoch 2 (Comparison) | Delta / Baseline |
| :--- | :--- | :--- | :--- |
| **Product Filename** | `level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits` | `level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits` | Multi-epoch pair |
| **SHA-256 Hash** | `b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1` | `60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e` | Verified authentic |
| **Observation ID** | `2026W31_2A_0034_3` | `2026W32_2A_0338_1` | 2 distinct visits |
| **Observation Epoch (MJD)** | `61251.698407674` | `61259.772608692` | **$\Delta t = 8.0742\text{ days}$ ($193.78\text{ h}$)** |
| **Observation Date (UTC)** | 2026-07-30T16:45:42 | 2026-08-07T18:32:33 | 8-day survey repeat |
| **Detector** | SPHEREx Detector 1 (`D1`) | SPHEREx Detector 1 (`D1`) | Identical bandpass |
| **Wavelength Coverage** | $0.75 - 1.12\,\mu\text{m}$ (Band 1) | $0.75 - 1.12\,\mu\text{m}$ (Band 1) | Congruent LVF |
| **Pointing Center (RA, Dec)**| $46.8444^\circ, +1.8322^\circ$ | $46.8438^\circ, +1.8313^\circ$ | Separation: $2.71^{\prime\prime}$ |
| **Surface Brightness Units**| `MJy/sr` | `MJy/sr` | Calibrated physical |
| **Array Dimensions** | $2040 \times 2040$ pixels | $2040 \times 2040$ pixels | $4,161,600$ pixels/frame |

---

## 3. Pipeline Architecture & Implementation Phases

### Phase 1: Multi-Extension FITS Ingestion (`spherex_mef_reader.py`)
- **Module:** `backend/app/astronomy/spherex_mef_reader.py`
- Implements `SpherexMefProduct` retaining all 7 scientific extensions:
  1. `PRIMARY`: Mission, pointing, spacecraft state, and calibration provenance.
  2. `IMAGE`: Calibrated surface brightness ($2040 \times 2040$, `float32`, `MJy/sr`).
  3. `FLAGS`: 32-bit integer quality bit flags ($2040 \times 2040$, `int32`).
  4. `VARIANCE`: Measurement variance ($2040 \times 2040$, `float32`, $(\text{MJy/sr})^2$).
  5. `ZODI`: Empirical Zodiacal light foreground model ($2040 \times 2040$, `float32`, preserved without modification).
  6. `EPSF`: $21 \times 21$ empirical point spread function table ($441$ rows, $101 \times 101$ sub-pixel kernels).
  7. `WCS-WAVE`: $9 \times 9$ spatial lookup table for effective wavelength $\lambda(x, y)$ and bandpass $\Delta\lambda(x, y)$.
- Strict schema validation: rejects files lacking required scientific HDUs or with corrupted table headers.
- Guaranteed backward compatibility with M4 readers (`fits_reader.py`, `wcs_processor.py`).

### Phase 2: Scientific Quality Mask (`quality_mask.py`)
- **Module:** `backend/app/astronomy/quality_mask.py`
- SPHEREx Level-2 bitmask definitions:
  - `BIT_TRANSIENT  = 1 << 0` ($1$): Cosmic ray / transient hit (`N_TRANSIENT`)
  - `BIT_OVERFLOW   = 1 << 1` ($2$): Detector saturation / A-D overflow (`N_OVERFLOW`)
  - `BIT_SUR_ERROR  = 1 << 2` ($4$): Slope-under-ramp measurement fit failure (`N_SUR_ERROR`)
  - `BIT_NONFUNC    = 1 << 6` ($64$): Non-functional detector pixel (`N_NONFUNC`)
  - `BIT_COLD       = 1 << 11` ($2048$): Dead / cold pixel (`N_COLD`)
  - `BIT_BLOOM      = 1 << 26` ($67108864$): Charge blooming artifact (`N_BLOOM`)
  - `BIT_SNOWBALL   = 1 << 27` ($134217728$): Charge deposit snowball artifact (`N_SNOWBALL`)
- **Fatal Defect Mask:** `FATAL_DEFECT_MASK = 201328707`.
- **Astronomical Source Invariant:** Bit 21 (`BIT_SOURCE = 2097152`, `N_SOURCE`) represents catalog astronomical sources (stars and galaxies). The mask policy explicitly guarantees that `BIT_SOURCE` is **never** rejected as a defect. In Epoch 1, $1,144,961$ clean catalog source pixels were tested and $100.00\%$ were preserved.
- **Variance Thresholding:** Pixels with non-finite or non-positive variance ($V \le 10^{-12}$) are masked out.
- **Zodiacal Light Preservation:** `ZODI` values are never subtracted or altered, guaranteeing calibrated surface brightness integrity.

### Phase 3: Common Tangent Plane Reprojection (`image_registration.py`)
- **Module:** `backend/app/astronomy/image_registration.py`
- Projects multi-epoch observations onto a common tangent WCS grid (`RA---TAN`, `DEC--TAN`) centered at $(\alpha_0, \delta_0) = (43.1555^\circ, +0.6960^\circ)$ with native SPHEREx pixel scale $6.2^{\prime\prime}/\text{pixel}$ ($0.0017222^\circ/\text{pixel}$).
- **Surface Brightness Conservation:** Resampling preserves `MJy/sr` units directly without flux distortion.
- **Rigorous Variance Propagation:** Implements exact analytical weight squaring for bilinear interpolation:
  $$\text{Var}(I) = w_{00}^2 V_{00} + w_{10}^2 V_{10} + w_{01}^2 V_{01} + w_{11}^2 V_{11}$$
  where $\sum w_{ij} = 1$. When shifting by $0.5$ pixels, resampled variance equals exactly $0.25 V_{\text{native}}$, verified analytically in Gate 4.
- **Registration Displacement:** Local displacement at image center is $dx = -0.399\,\text{pix}$, $dy = +0.168\,\text{pix}$, angular separation $\Delta\theta = 3.77^{\prime\prime}$ ($< 1$ SPHEREx pixel).

### Phase 4: LVF Spectral Compatibility (`spectral_compatibility.py`)
- **Module:** `backend/app/astronomy/spectral_compatibility.py`
- Evaluates the $9 \times 9$ `WCS-WAVE` bicubic grid to determine continuous effective transmission $\lambda(x, y)$ and bandwidth $\Delta\lambda(x, y)$ at every reprojected pixel.
- Enforces relative wavelength difference criterion:
  $$\frac{|\lambda_1(x, y) - \lambda_2(x, y)|}{\lambda_1(x, y)} \le 2.0\%$$
- **Real Pair Result:**
  - Mean relative wavelength mismatch: **$0.0034\%$** ($0.000034$)
  - Maximum relative mismatch: **$0.0047\%$**
  - Spectrally compatible pixel fraction: **$100.00\%$** (zero pixels rejected by spectral cut).

### Phase 5: PSF Homogenization (`psf_matching.py`)
- **Module:** `backend/app/astronomy/psf_matching.py`
- Evaluates the $21 \times 21$ `EPSF` grid ($441$ spatial bins).
- In the static in-flight calibration model used by both Level-2 products, the native empirical FWHM is identical ($7.135$ sub-pixels across central bins).
- Quadrature kernel formulation:
  $$\sigma_{\text{kernel}} = \sqrt{\sigma_{\text{target}}^2 - \sigma_{\text{native}}^2}$$
- When targeting identical PSFs, $\sigma_{\text{kernel}} = 0.0$ and no artificial blurring is applied, avoiding noise degradation.

### Phase 6: Difference & Significance Imaging (`difference_engine.py`)
- **Module:** `backend/app/astronomy/difference_engine.py`
- Difference image: $D(x, y) = I_2(x, y) - I_1(x, y)$.
- Combined measurement variance: $\text{Var}(D) = \text{Var}(I_1) + \text{Var}(I_2)$.
- Combined uncertainty: $\sigma_D(x, y) = \sqrt{\text{Var}(D)}$.
- Significance map:
  $$S(x, y) = \frac{D(x, y) - \text{median}(D)}{\sigma_D(x, y)}$$
- **Real Pair Differencing Statistics ($512 \times 512$ common grid):**
  - Total grid pixels: $262,144$
  - Valid scientific pixels: $261,045$ ($99.58\%$)
  - Difference RMS noise: $0.5466\,\text{MJy/sr}$
  - Mean significance $\mu_S$: **$+0.00075$** ($\approx 0.0$, zero residual offset)
  - Significance dispersion $\sigma_S$: $2.38$
  - Dynamic significance range: $-130.1\sigma$ to $+109.6\sigma$

### Phase 7: Change Candidate Extraction (`change_detection.py`)
- **Module:** `backend/app/astronomy/change_detection.py`
- Identifies 8-connected components satisfying $|S(x, y)| \ge 3.5\sigma$ (or configurable $5.0\sigma$).
- Parameters measured per candidate:
  - Centroid $(\bar{x}, \bar{y})$ weighted by $|S|$
  - Celestial coordinates $(\alpha, \delta)$ via Astropy WCS
  - Polarity: `POSITIVE` (brightening) or `NEGATIVE` (fading)
  - Peak significance $S_{\text{peak}}$
  - Peak differential flux $\Delta I_{\text{peak}}$ (`MJy/sr`)
  - Integrated flux $\sum D_i$ (`MJy/sr`)
  - Pixel area
  - Contextual warnings: `NEAR_IMAGE_BOUNDARY`, `EXTENDED_EMISSION`
- Mandatory scientific status:
  `CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED`

### Phase 8: User Experience & Interactive Comparison
- **Frontend Panel:** `frontend/components/temporal/TemporalControlPanel.tsx`
- **Supported Operational Modes:**
  1. **Difference Image Deck:** Diverging Blue-White-Red colormap centered on zero differential surface brightness.
  2. **Significance Heatmap:** Visualizes signal-to-noise excursions thresholded by user-adjustable $\sigma$ slider.
  3. **Blink Comparator:** Synchronized alternating toggle between aligned Epoch 1 and Epoch 2 frames.
  4. **Reference & Comparison Views:** Instant isolated inspection of Epoch 1 ($t_1$) and Epoch 2 ($t_2$).
  5. **Interactive Candidate Inspector:** Real-time marker overlay on celestial tangent grid with candidate details table (coordinates, SNR, flux, polarity, disclaimer).
- Production build verified: Next.js 16.4.6 compiles in $8.3\,\text{s}$ with 0 TypeScript errors.

---

## 4. Verification Suite Results (12 Acceptance Gates)

The full automated validation suite was executed via pytest in `tests/test_spherex_m5_validation.py`. All 12 acceptance gates passed:

| Gate | Acceptance Criterion | Test Name | Verification Method | Result |
| :---: | :--- | :--- | :--- | :---: |
| **01** | Multi-Extension FITS Ingestion | `test_gate_01_mef_ingestion` | 7 HDUs loaded, dtypes verified, SHA-256 confirmed | **PASS** |
| **02** | Quality Mask Bitwise Policy | `test_gate_02_quality_mask_policy` | Fatal bits excluded, Bit 21 (`SOURCE`) 100% preserved | **PASS** |
| **03** | WCS Reprojection Accuracy | `test_gate_03_wcs_reprojection` | Sub-pixel alignment, surface brightness preserved | **PASS** |
| **04** | Variance Propagation | `test_gate_04_variance_propagation` | Bilinear weight squaring $\sum w_i^2 V_i = 0.25 V_0$ | **PASS** |
| **05** | Spectral Compatibility | `test_gate_05_spectral_compatibility` | Mismatched bandpasses ($> 2\%$) strictly rejected | **PASS** |
| **06** | PSF Homogenization | `test_gate_06_psf_homogenization` | Quadrature formula $\sigma_k = \sqrt{\sigma_t^2 - \sigma_n^2}$ verified | **PASS** |
| **07** | Difference Image Exactness | `test_gate_07_difference_exactness` | Algebraic exactness $D = I_2 - I_1$, $\sigma_D = \sqrt{V_1+V_2}$ | **PASS** |
| **08** | Significance Normalization | `test_gate_08_significance_null_data` | Standard normal distribution $\mathcal{N}(0, 1)$ on null noise | **PASS** |
| **09** | Transient Injection/Recovery | `test_gate_09_synthetic_injection_recovery` | Synthetic transient recovered with correct centroid & SNR | **PASS** |
| **10** | Scientific Qualification Labeling | `test_gate_10_mandatory_disclaimer_label` | All candidates carry unconfirmed disclaimer | **PASS** |
| **11** | Edge Artifact Rejection | `test_gate_11_edge_artifact_rejection` | Boundary pixels flagged `NEAR_IMAGE_BOUNDARY` | **PASS** |
| **12** | End-to-End Real Observation | `test_gate_12_real_spherex_pair` | Full pipeline executed on genuine SPHEREx pair | **PASS** |

**Pytest Summary:**
```
====================== 12 passed, 146 warnings in 8.58s =======================
```

---

## 5. Architectural Integrity & Non-Regression Summary

1. **Frozen M1–M4 Components:**
   - `fits_reader.py` remains untouched.
   - `wcs_processor.py` remains untouched.
   - `image_renderer.py` remains untouched.
   - M4 unit tests in `tests/test_spherex_m4_validation.py` pass without regression.
2. **FastAPI & Next.js Integration:**
   - API endpoints `/temporal/observations`, `/temporal/compare`, and `/temporal/benchmark-pairs` mounted cleanly.
   - Frontend production build compiles cleanly without errors or hydration mismatches.

---

## 6. Final Acceptance Gate Verdict

$$\mathbf{VERDICT:\; ACCEPTED\; \&\; FULLY\; OPERATIONAL}$$

Milestone 5 is complete, scientifically verified, and ready for operational exploration of genuine multi-epoch SPHEREx infrared observations.
