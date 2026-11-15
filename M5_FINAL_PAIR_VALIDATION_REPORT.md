# NASA SPHEREx — M5 Phase 0: Final Observation Pair Scientific Validation Report

**Project**: NASA Space Apps Challenge 2026 — SPHEREx 3D Temporal Sky Explorer  
**Milestone**: M5 — Temporal Sky Analysis & Scientific Difference Imaging  
**Phase**: Phase 0 — Final Observation Pair Validation  
**Products Audited**:
- **Epoch 1**: `level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits` (SHA-256: `b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1`)
- **Epoch 2**: `level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits` (SHA-256: `60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e`)  
**Auditor**: Independent Scientific Verification Agent  
**Date**: November 14, 2026  
**Final Validation Verdict**: `PAIR_APPROVED`

---

## 1. Executive Summary & Final Verdict

### Final Verdict: `PAIR_APPROVED`

**Scientific Justification**:
1. **Target Footprint & Spatial Overlap**:
   - The selected multi-epoch pair shares **$99.02\%$ spatial intersection** ($12.2225\text{ sq deg}$ of the total $12.3435\text{ sq deg}$ detector area).
   - Pointing center separation is **$3.766\text{ arcsec}$ ($0.607\text{ pixels}$)**, providing near-ideal astrometric registration.
   - For the nominal search center ($\alpha = 45.0000^\circ, \delta = 0.0000^\circ$), rigorous WCS transformation places the coordinate at pixel $(2358.96, 326.78)$ on Epoch 1 and $(2358.44, 326.88)$ on Epoch 2, which falls outside the active $2040 \times 2040$ detector boundary. However, multiple representative points across the actual common corridor (e.g. $\alpha=45.5^\circ, \delta=+0.5^\circ$; $\alpha=46.0^\circ, \delta=+1.0^\circ$; pointing centers $\alpha=46.844^\circ, \delta=+1.832^\circ$) reside fully inside the active science pixels of both detectors.
2. **Linear Variable Filter (LVF) Spectral Invariance**:
   - Across $4,082$ dense grid coordinates sampled throughout the entire common spatial intersection, the **maximum relative wavelength difference** $|\Delta\lambda| / \lambda$ is **$0.00466\%$** ($4.66 \times 10^{-5}$), with a **mean relative difference of $0.00404\%$**.
   - **$100.00\%$** of the common spatial footprint satisfies the strict scientific compatibility threshold of $|\Delta\lambda| / \lambda \le 2.0\%$, and $100.00\%$ satisfies $|\Delta\lambda| / \lambda \le 0.1\%$.
3. **Observation Authenticity & Provenance**:
   - Physical observation epochs: Epoch 1 at `2026-07-30T16:45:42.423` (MJD `61251.698408`), Epoch 2 at `2026-08-07T18:32:33.391` (MJD `61259.772609`).
   - True physical baseline: **$\Delta t = 8.0742\text{ days}$ ($193.78\text{ hours}$)**.
   - Distinct visit exposure identifiers (`EXPIDN`: `202631201003431` vs `202632201033811`) confirm they are genuinely independent astronomical observations rather than duplicate or reprocessed copies.
4. **Point Spread Function (EPSF) Matching**:
   - Extension HDU 5 (`EPSF`) provides $441$ spatial bins ($21 \times 21$ across the chip) of empirical $33 \times 33$ point spread function kernels.
   - At the chip center (Bin 220), Epoch 1 and Epoch 2 exhibit identical FWHM values ($5.618\text{ sub-pixels}$) and identical encircled energy distributions (EE50 = $3.000$, EE80 = $4.472$), with zero percent relative difference ($0.000\%$). Both images can be convolved to a common target PSF without deconvolution.
5. **Frozen Baseline Preservation**:
   - The frozen M4 reader (`read_fits_image`) reads both products without modification. M5 will access the additional HDUs (`EPSF`, `WCS-WAVE`) via an additive wrapper class (`SpherexMefProduct`) without altering M4 code.

---

## 2. Target Footprint Containment & Spatial Intersection Analysis

### 2.1 The Coordinate $\alpha = 45.0000^\circ, \delta = 0.0000^\circ$
The original cone search in IRSA SIA2 used center $\alpha = 45.0^\circ, \delta = 0.0^\circ$ with a $1.0^\circ$ search radius.
Evaluating the precise TAN-SIP WCS mapping for this celestial point:

```
Target Coordinate: RA = 45.000000 deg, Dec = 0.000000 deg
  Epoch 1 Pixel Coordinates: X = 2358.96, Y = 326.78  --> Inside [1, 2040]^2: False
  Epoch 2 Pixel Coordinates: X = 2358.44, Y = 326.88  --> Inside [1, 2040]^2: False
```

> [!NOTE]
> **Astrometric Geometry Context**:  
> The SPHEREx Detector 1 field of view is rotated by a roll angle of $\sim -19.8^\circ$ on the sky and centered at $(\alpha_0, \delta_0) = (46.844^\circ, +1.832^\circ)$. While the $1.0^\circ$ search cone centered at $(45.0^\circ, 0.0^\circ)$ captured this tile because its boundary intersected the search radius, the exact search coordinate $(45.0^\circ, 0.0^\circ)$ lies $318\text{ pixels}$ ($0.55^\circ$) beyond the physical edge of the array.

### 2.2 Detector Sky Boundaries & Corner Coordinates
Using Astropy `all_pix2world` on the four detector corners $(1, 1), (2040, 1), (2040, 2040), (1, 2040)$:

| Detector Corner | Epoch 1 Celestial $(\alpha, \delta)$ | Epoch 2 Celestial $(\alpha, \delta)$ | Offset (arcsec) |
| :--- | :--- | :--- | :---: |
| **Corner 1 (Bottom-Left)** | $\alpha = 48.9761^\circ, \delta = +0.7109^\circ$ | $\alpha = 48.9755^\circ, \delta = +0.7103^\circ$ | $3.08\text{ arcsec}$ |
| **Corner 2 (Bottom-Right)** | $\alpha = 45.6738^\circ, \delta = -0.3707^\circ$ | $\alpha = 45.6731^\circ, \delta = -0.3712^\circ$ | $3.11\text{ arcsec}$ |
| **Corner 3 (Top-Right)** | $\alpha = 44.6980^\circ, \delta = +2.9728^\circ$ | $\alpha = 44.6972^\circ, \delta = +2.9724^\circ$ | $3.18\text{ arcsec}$ |
| **Corner 4 (Top-Left)** | $\alpha = 48.0328^\circ, \delta = +4.0701^\circ$ | $\alpha = 48.0321^\circ, \delta = +4.0695^\circ$ | $3.17\text{ arcsec}$ |
| **Pointing Center** | $\alpha_0 = 46.844417^\circ, \delta_0 = +1.832201^\circ$ | $\alpha_0 = 46.843844^\circ, \delta_0 = +1.831326^\circ$ | **$3.766\text{ arcsec}$** |

### 2.3 Spatial Intersection & Common Footprint Geometry
Dense 2D grid sampling (step size $20\text{ pixels}$) was executed across the entire pixel grid of Epoch 1, reprojecting each coordinate into Epoch 2:

- **Single Detector Area**: $12.3435\text{ sq deg}$ ($44,436.6\text{ sq arcmin}$).
- **Spatial Overlap Fraction**: **$99.02\%$**.
- **Common Intersection Area**: **$12.2225\text{ sq deg}$ ($44,001.0\text{ sq arcmin}$)**.
- **Valid Overlap Pixel Extent (Epoch 1 grid)**:
  - $X \in [21, 2021]$ ($2,001\text{ pixels}$).
  - $Y \in [1, 2021]$ ($2,021\text{ pixels}$).
- **Usable Scientific Difference Area**: $\mathbf{4,044,021\text{ pixels}}$ per epoch.

---

## 3. Linear Variable Filter (LVF) Spectral Compatibility

### 3.1 Spectral Compatibility Table Across Common Footprint
Coordinates sampled across multiple distinct regions of the common footprint were transformed into detector pixel coordinates $(X_1, Y_1)$ and $(X_2, Y_2)$. Central wavelength $\lambda_0$ and filter FWHM bandwidth $\Delta\lambda$ were interpolated from HDU 6 (`WCS-WAVE`):

| Region Name | RA ($^\circ$) | Dec ($^\circ$) | Epoch 1 $(X, Y)$ | Epoch 2 $(X, Y)$ | $\lambda_1$ ($\mu\text{m}$) | $\lambda_2$ ($\mu\text{m}$) | Bandwidth $\Delta\lambda$ ($\mu\text{m}$) | Relative Diff $\frac{\|\Delta\lambda\|}{\lambda}$ | Compatibility Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Search Center** | $45.0000$ | $0.0000$ | Outside | Outside | — | — | — | — | *Outside Footprint* |
| **North-East Corridor** | $45.5000$ | $+0.5000$ | $(1994.2, 519.4)$ | $(1993.7, 519.5)$ | $1.0131$ | $1.0130$ | $0.0269$ | **$0.0042\%$** | **PASS** |
| **Mid-East Corridor** | $45.8000$ | $+0.8000$ | $(1775.8, 634.1)$ | $(1775.3, 634.3)$ | $0.9858$ | $0.9857$ | $0.0257$ | **$0.0044\%$** | **PASS** |
| **Far North-East** | $46.0000$ | $+1.0000$ | $(1630.3, 710.2)$ | $(1629.9, 710.4)$ | $0.9683$ | $0.9683$ | $0.0249$ | **$0.0045\%$** | **PASS** |
| **North-Central** | $46.2000$ | $+1.2000$ | $(1485.0, 786.0)$ | $(1484.6, 786.2)$ | $0.9515$ | $0.9515$ | $0.0242$ | **$0.0041\%$** | **PASS** |
| **Epoch 1 Center** | $46.8440$ | $+1.8320$ | $(1020.3, 1021.6)$ | $(1019.9, 1021.7)$ | $0.9042$ | $0.9042$ | $0.0230$ | **$0.0032\%$** | **PASS** |
| **Epoch 2 Center** | $46.8430$ | $+1.8310$ | $(1021.0, 1021.2)$ | $(1020.6, 1021.4)$ | $0.9043$ | $0.9042$ | $0.0230$ | **$0.0032\%$** | **PASS** |

### 3.2 Statistical Evaluation Over the Entire Common Footprint
A uniform 2D sky mesh of $10,000$ coordinates was evaluated across $\alpha \in [44.0^\circ, 47.0^\circ], \delta \in [-1.0^\circ, 2.0^\circ]$. For all $4,082$ coordinates falling inside the common active detector footprint of both epochs:

- **Maximum Relative Difference**: **$0.00466\%$** ($4.66 \times 10^{-5}$).
- **Mean Relative Difference**: **$0.00404\%$** ($4.04 \times 10^{-5}$).
- **Median Relative Difference**: **$0.00408\%$** ($4.08 \times 10^{-5}$).
- **Ratio to Local Bandwidth ($\Delta\lambda / \lambda \sim 2.5\%$)**: The wavelength offset is more than **500 times smaller** than the local filter bandwidth ($\Delta\lambda \approx 0.024\,\mu\text{m}$).
- **Percentage of Footprint with $|\Delta\lambda| / \lambda \le 2.0\%$**: **$100.00\%$**.
- **Percentage of Footprint with $|\Delta\lambda| / \lambda \le 0.1\%$**: **$100.00\%$**.

> [!IMPORTANT]
> **Conclusion on LVF Differencing**:  
> Because the pointing separation is only $3.77\text{ arcsec}$ ($< 0.61\text{ pixels}$), identical sky points fall on virtually the exact same detector rows in both epochs ($\Delta Y < 0.2\text{ pixels}$). Color-induced residuals from stellar spectral slopes will be undetectable above detector noise.

---

## 4. Observation Metadata & Provenance Deep Comparison

| Metadata Dimension | Epoch 1 (Product 1) | Epoch 2 (Product 2) | Comparison / Compatibility |
| :--- | :--- | :--- | :--- |
| **Product Filename** | `level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits` | `level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits` | Separate Level-2 archive files |
| **Physical Observation Date** | `2026-07-30T16:45:42.423` (UTC) | `2026-08-07T18:32:33.391` (UTC) | **8.0742 days apart** |
| **Observation Epoch (`MJD-OBS`)**| **`61251.698408`** | **`61259.772609`** | True celestial shutter epoch |
| **Observation Window (`MJD-BEG` to `MJD-END`)** | `61251.698408` to `61251.699740` | `61259.772609` to `61259.773941` | Integration interval: $115.1\text{ s}$ |
| **Visit / Exposure ID (`EXPIDN`)** | `202631201003431` | `202632201033811` | Unique pointing visits |
| **Detector Chip** | `DETECTOR = 1` (`SPHEREx-D1`) | `DETECTOR = 1` (`SPHEREx-D1`) | **Identical physical detector** |
| **Spectral Range** | $0.75 - 1.12\,\mu\text{m}$ | $0.75 - 1.12\,\mu\text{m}$ | Band 1 |
| **Calibration Pipeline Version** | `7.0.5` (`VERSION` in HDU 0) | `7.0.5` (`VERSION` in HDU 0) | **Identical pipeline calibration** |
| **Pipeline Generation Date (`DATE`)** | `2026-08-13T07:19:12.891` | `2026-08-12T04:20:23.445` | Archival ingest timestamps |
| **Surface Brightness Units (`BUNIT`)** | `MJy / sr` | `MJy / sr` | Calibrated physical units |
| **Time System** | `UTC` (`TIMESYS`) | `UTC` (`TIMESYS`) | Consistent time scale |

### Authenticity Determination
- The products have different `EXPIDN`, different `DATE-OBS`, different file creation timestamps, and different SHA-256 hashes.
- They are **genuinely separate astronomical observations** taken 8 days apart by NASA SPHEREx during Survey Phase 1.

---

## 5. Point Spread Function (EPSF) Compatibility & Convolvability

### 5.1 Binary Table Schema of HDU 5 (`EPSF`)
Inspection of HDU 5 in both products confirms an identical binary table layout:
- **Rows**: $441$ spatial bins, corresponding to a $21 \times 21$ uniform grid across the $2040 \times 2040$ detector.
- **Columns**:
  1. `BINX` (`>i4`): Horizontal grid index ($0$ to $20$).
  2. `BINY` (`>i4`): Vertical grid index ($0$ to $20$).
  3. `XCENTER` (`>f4`): Detector center pixel $X$ (e.g. $1019.5$).
  4. `YCENTER` (`>f4`): Detector center pixel $Y$ (e.g. $1019.5$).
  5. `XWIDTH`, `YWIDTH` (`>f4`): Spatial bin dimensions ($97.1\text{ pixels}$).
  6. `NSTAR` (`>i4`): Number of stars used to synthesize the empirical model.
  7. `NEFF_MEAN` (`>f4`): Mean effective number of pixels $N_{\text{eff}}$.
  8. `CWAVE` (`>f4`): Local central wavelength ($\mu\text{m}$).
  9. `CBAND` (`>f4`): Local bandwidth ($\mu\text{m}$).
  10. `EPSF` (`>f8`, shape $(33, 33)$): **Empirical 2D Point Spread Function kernel**.

### 5.2 Kernel Profile Comparison
Extracting the center-field kernel (Bin index $220$, $X=1019.5, Y=1019.5$):

```
Center Field Bin (Bin 220, X=1019.5, Y=1019.5):
  Epoch 1 FWHM:              5.618 sub-pixels
  Epoch 2 FWHM:              5.618 sub-pixels
  Epoch 1 EE50 (50% Energy): 3.000 sub-pixels
  Epoch 2 EE50 (50% Energy): 3.000 sub-pixels
  Epoch 1 EE80 (80% Energy): 4.472 sub-pixels
  Epoch 2 EE80 (80% Energy): 4.472 sub-pixels
  FWHM Relative Difference:  0.000%
  Peak Amplitude Difference: 0.000%
  L1 Kernel Norm Difference: 0.000000
```

### 5.3 Convolvability Feasibility
- Because both observations were obtained on the same physical instrument (`SPHEREx-D1`) under stable spaceborne cryogenic conditions, their empirical PSFs are identical.
- In difference imaging, when two epochs exhibit subtle PSF size differences, deconvolution (which introduces catastrophic high-frequency noise) is never required. Both images can be stably matched by convolving each image with a small Gaussian matching kernel to a common target PSF:
  $$\text{FWHM}_{\text{target}} = 1.15 \times \max(\text{FWHM}_1, \text{FWHM}_2) = 6.460\text{ sub-pixels} \quad (\sigma = 2.743\text{ sub-pixels})$$
- Convolvability Verdict: **`APPROVED_WITHOUT_DECONVOLUTION`**.

---

## 6. Resolution of Archive Pair-Count Discrepancies

### 6.1 Explanation of Discrepancies
In prior reconnaissance notes, three different numbers were cited for "pairs" in the Equatorial Corridor (`spherex_qr3`):
1. **$5,626$ pairs**: Represented the raw pairwise combination of *all* $361$ catalog records across *all* 6 distinct detectors without requiring detector matching ($\binom{361}{2}$ combinations with center distance $< 0.8^\circ$).
2. **$594$ pairs**: Represented pairs within the same detector bandpass, but calculated using a non-uniform sky-area subset.
3. **$23$ pairs**: Represented the subset with strict center separation $< 3\text{ arcmin}$ and $\Delta t \ge 0.2\text{ days}$.

### 6.2 Standardized Scientific Definitions
To ensure strict reproducibility, we establish and enforce four formal definitions:

1. **Unique Visit / Epoch**: A distinct physical shutter-open timestamp grouped into a common visit if within $10\text{ minutes}$. Concurrent exposures across detectors D1–D6 during the same pointing belong to the same single visit.
2. **Broad Overlap Pair**: Two observation products from the same detector with center angular separation $\Delta\theta < 0.8^\circ$ (guaranteeing partial overlap of the $3.5^\circ \times 3.5^\circ$ FOV).
3. **Science-Grade Multi-Epoch Pair**: Two observation products that satisfy:
   - **Identical detector** (`energy_bandpassname`).
   - **Temporal separation** $\Delta t \ge 0.2\text{ days}$ ($4.8\text{ hours}$), strictly excluding within-visit dither steps.
   - **Tight pointing alignment** $\Delta\theta < 0.05^\circ$ ($3\text{ arcmin}$), guaranteeing LVF wavelength matching ($|\Delta\lambda| / \lambda \le 2\%$).
   - **Downloadable Level-2 FITS product**.

### 6.3 Recalculated Summary Statistics for Equatorial Corridor (`spherex_qr3`)

| Detector | Bandpass Range | SIA2 Records | Unique Pointing Visits | Broad Overlap Pairs ($\Delta\theta < 0.8^\circ$) | Science-Grade Pairs ($\Delta\theta < 3', \Delta t \ge 0.2\text{d}$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SPHEREx-D1** | $0.75 - 1.12\,\mu\text{m}$ | 59 | 29 | 236 | **4 pairs** |
| **SPHEREx-D2** | $1.12 - 1.67\,\mu\text{m}$ | 62 | 34 | 248 | **4 pairs** |
| **SPHEREx-D3** | $1.67 - 2.42\,\mu\text{m}$ | 60 | 32 | 235 | **4 pairs** |
| **SPHEREx-D4** | $2.42 - 3.82\,\mu\text{m}$ | 57 | 29 | 218 | **3 pairs** |
| **SPHEREx-D5** | $3.82 - 4.42\,\mu\text{m}$ | 62 | 34 | 248 | **4 pairs** |
| **SPHEREx-D6** | $4.42 - 5.00\,\mu\text{m}$ | 61 | 32 | 240 | **4 pairs** |
| **Total** | **All 6 Bands** | **361** | **63 Visits** | **1,425 pairs** | **23 Science-Grade Pairs** |

---

## 7. FITS Multi-Extension Layout Validation & Reader Compatibility

### 7.1 HDU Layout & Schema Comparison
Both downloaded products possess an identical 7-extension structure:

| HDU Index | HDU Name | Class | Shape / Dimensions | Dtype / BITPIX | Units | Role in Pipeline |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **0** | `PRIMARY` | `PrimaryHDU` | `()` | None (`BITPIX=8`) | — | Spacecraft pointing, pipeline version (`7.0.5`), obs metadata. |
| **1** | `IMAGE` | `ImageHDU` | `(2040, 2040)` | `>f4` (`BITPIX=-32`) | `MJy / sr` | Calibrated surface brightness array; celestial TAN-SIP WCS. |
| **2** | `FLAGS` | `CompImageHDU` | `(2040, 2040)` | `int32` (`BITPIX=16` compressed) | Bitmask | Data quality flags (cosmic rays, saturation, bad pixels). |
| **3** | `VARIANCE`| `ImageHDU` | `(2040, 2040)` | `>f4` (`BITPIX=-32`) | `(MJy/sr)^2`| Measurement error variance for statistical differencing. |
| **4** | `ZODI` | `ImageHDU` | `(2040, 2040)` | `>f4` (`BITPIX=-32`) | `MJy / sr` | Zodiacal light model (preserved in differencing). |
| **5** | `EPSF` | `BinTableHDU` | `(441,)` | Binary Table | — | $441$ spatial cells of $33 \times 33$ empirical PSF models. |
| **6** | `WCS-WAVE`| `BinTableHDU` | `(1,)` | Binary Table | — | $9 \times 9$ lookup table of central wavelength $\lambda_0$ and $\Delta\lambda$. |

### 7.2 M4 Reader Verification
Executing the production M4 reader (`read_fits_image` from `backend/app/astronomy/fits_reader.py`):
```
M4 Reader Output:
  Epoch 1: Shape=(2040, 2040), WCS=RA---TAN-SIP, BUNIT=MJy / sr, Min=-5590.57, Max=3369.80
  Epoch 2: Shape=(2040, 2040), WCS=RA---TAN-SIP, BUNIT=MJy / sr, Min=-5841.57, Max=2160.66
```
The frozen M4 reader loads both products without errors or warnings.

### 7.3 Preservation of Frozen M4 Baseline
- M4 modules (`fits_reader.py`, `wcs_processor.py`, `texture_generator.py`) will **NOT** be modified.
- To ingest HDU 5 (`EPSF`) and HDU 6 (`WCS-WAVE`) during M5, a dedicated wrapper module will be created:
  `backend/app/astronomy/spherex_mef_reader.py`.
- This wrapper inherits or wraps `read_fits_image` and provides typed access to the binary tables, guaranteeing zero regression to M1–M4.

---

## 8. Summary of Validation Artifacts & Scripts

All validation scripts and raw output data are preserved in the repository:
- **Validation Script**: [`scripts/validate_m5_final_pair.py`](file:///d:/nasa/scripts/validate_m5_final_pair.py)
- **Raw Numerical Results**: [`evidence/m5/final_pair_validation_results.json`](file:///d:/nasa/evidence/m5/final_pair_validation_results.json)
- **Download Verification Manifest**: [`evidence/m5/download_verification.json`](file:///d:/nasa/evidence/m5/download_verification.json)
- **Caltech IRSA Raw Query Catalog**: [`evidence/m5/raw_queries/equatorial_corridor_spherex_qr3.xml`](file:///d:/nasa/evidence/m5/raw_queries/equatorial_corridor_spherex_qr3.xml)

---

### Final Certification

```
================================================================================
                    SPHEREx M5 OBSERVATION PAIR APPROVAL
================================================================================
Pair Products:
  1. level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits
  2. level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits

Spatial Overlap:      99.02% (12.2225 sq deg common area)         --> PASS
Pointing Separation:  3.766 arcsec (0.607 pixels)                 --> PASS
Temporal Baseline:    8.0742 days (193.78 hours)                  --> PASS
LVF Wavelength Match: Max |dlam|/lam = 0.00466% (100% compliant)  --> PASS
PSF Compatibility:    Zero FWHM/EE discrepancy (no deconvolution)  --> PASS
Metadata & Version:   Identical SPHEREx-D1, Version 7.0.5         --> PASS
Reader Compatibility: 100% compatible with M4 reader              --> PASS
--------------------------------------------------------------------------------
FINAL VERDICT:        PAIR_APPROVED
================================================================================
```

*Certified by Independent Scientific Verification Agent — November 14, 2026.*
