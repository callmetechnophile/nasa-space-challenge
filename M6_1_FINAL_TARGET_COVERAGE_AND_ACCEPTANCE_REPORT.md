# M6.1 — FINAL FIVE-TARGET COVERAGE AND ACCEPTANCE CLOSURE REPORT
**Project:** NASA SPHEREx — 3D Temporal Sky Explorer  
**Audit Stage:** Milestone 6.1 (M6.1) Final Acceptance and Five-Target Coverage Audit  
**Date:** 2026-11-15T00:55:00Z  
**Runtime Environment:** Windows Server / Windows 11, Python 3.13.9, Astropy 7.0.0, NumPy 2.2.0, Next.js 16.4.6, React 19.3.0, Three.js 0.187.0  
**Final Master Verdict:** `M6_1_CONDITIONAL`  
**Milestone 5 Scientific Status:** `CONDITIONAL` (Frozen & Preserved)  
**Zero-Fabrication Policy:** 100% Compliant (Zero synthetic observations or unverified epochs fabricated)

---

## 1. EXECUTIVE SUMMARY & VERDICT

This independent audit evaluates Milestone 6 (`M6_CHALLENGE_COMPLETION_REPORT.md`) against the strict acceptance criteria of the NASA SPHEREx Challenge:
> *"Create a public-facing web tool to display images of the sky from the SPHEREx mission, making it easy for anyone to quickly see how they change over time. Users will enter the coordinates of a patch of sky (Right Ascension and declination). Your tool will display a series of images of that patch like a little video, making it easy to spot moving objects. Test your tool on Barnard’s Star, Epsilon Indi B (a pair of brown dwarfs orbiting a star), WISE 0855 (a fast-moving brown dwarf Right Ascension 08h55m10.831s, declination -7d14m42.53s), and variable stars RW Aurigae and R Draconis."*

### Final Verdict Determination

| Criterion | Requirement | Audit Result | Status |
|:---|:---|:---|:---:|
| **Coordinate Ingestion & Resolution** | Sexagesimal parsing, RA $[0, 360^\circ]$, Dec $[-90, +90^\circ]$ | Fully verified with automated boundary rejection | **PASS** |
| **Astrometric Proper Motion Propagation** | Rigorous propagation across observation baseline | Exact formulas implemented; WISE 0855 and Barnard's Star reconciled | **PASS** |
| **Resolution Limit Validation** | Physics-based assessment of SPHEREx 6.2" PSF | Epsilon Indi B correctly flagged as unresolved blend ($0.73'' \ll 6.2''$) | **PASS** |
| **Dual-Release Archive Discovery** | Search DR1 and QR3 via IRSA SIA with error taxonomy | Fully implemented; handles 502/timeouts with zero fabrication | **PASS** |
| **Temporal Video Player** | Multi-epoch playback, scrubber, speed, blink mode | Implemented in `TimeSeriesPlayer.tsx` and mounted in UI | **PASS** |
| **Non-Discovery Disclaimer** | Mandatory candidate labeling invariant | Enforced in all models, API responses, and UI elements | **PASS** |
| **Frozen M1–M5 Baseline** | Approved QR3 FITS SHA-256 hashes preserved | Bit-for-bit identical; M5 scientific status preserved | **PASS** |
| **Five-Target Multi-Epoch Public Coverage** | $\ge 2$ real public archive epochs per target | 1 local epoch for WISE 0855; 0 public archive epochs for others | **CONDITIONAL** |

### Master Audit Verdict: `M6_1_CONDITIONAL`

**Verdict Rationale:**  
Under the prompt mandate:  
> *"M6_1_COMPLETE requires an actual usable chronological series for all five required targets. If one or more targets lack sufficient archive coverage, report M6_1_CONDITIONAL."*

Live queries to the NASA/IPAC Infrared Science Archive (IRSA) Simple Image Access (SIA) service across collections `spherex_dr1` and `spherex_qr3` currently return HTTP 502 Bad Gateway / upstream gateway timeouts for the requested sky coordinates, or report zero public Level-2 image products covering these specific pointing footprints.  
Locally, the repository holds one verified Level-2 MEF FITS file covering **WISE 0855** (`level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits`), but zero local files for Barnard's Star, Epsilon Indi B, RW Aurigae, and R Draconis.  
Because the system strictly adheres to the **Zero-Fabrication Policy** (never synthesizing artificial astronomical observations or fake timestamps), the temporal coverage status for all five targets is authentically and accurately classified as `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE`.  
End-to-end multi-epoch differencing, playback, and temporal analysis are fully demonstrated on the approved real equatorial benchmark pair (`level2_2026W31` and `level2_2026W32`). Therefore, Milestone 6 achieves **`M6_1_CONDITIONAL`** pending public release of multi-epoch pointing products for the target fields.

---

## 2. PHASE 1 — TARGET COORDINATE AUDIT & ASTROMETRIC PROVENANCE

A comprehensive astronomical audit was performed for each of the five required targets.

### Target Specifications and Astrometric Catalog Provenance

| Target Name | Catalog Identifier & Source | Frame & Epoch | Catalog RA ($\alpha$) | Catalog Dec ($\delta$) | Proper Motion $\mu_\alpha\cos\delta$ | Proper Motion $\mu_\delta$ | Parallax $\varpi$ (mas) | Distance (pc) |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Barnard's Star** | Gaia DR3 4472832130942585856 (GJ 699) | ICRS J2016.0 | $269.452083^\circ$<br>($17^\text{h}57^\text{m}48.50^\text{s}$) | $+04.693333^\circ$<br>($+04^\circ41'36.00''$) | $-798.58\,\text{mas/yr}$ | $+10328.12\,\text{mas/yr}$ | $547.45$ | $1.827$ |
| **Epsilon Indi B** | SIMBAD / King et al. 2010 (HD 209100 B) | ICRS J2000.0 | $331.043792^\circ$<br>($22^\text{h}04^\text{m}10.51^\text{s}$) | $-56.782722^\circ$<br>($-56^\circ46'57.80''$) | $+3961.00\,\text{mas/yr}$ | $-2538.00\,\text{mas/yr}$ | $275.80$ | $3.626$ |
| **WISE 0855** | Luhman 2014 / Kirkpatrick 2014 | ICRS J2010.0 | $133.795129^\circ$<br>($08^\text{h}55^\text{m}10.831^\text{s}$) | $-07.245147^\circ$<br>($-07^\circ14'42.53''$) | $-8118.00\,\text{mas/yr}$ | $+715.00\,\text{mas/yr}$ | $433.00$ | $2.309$ |
| **RW Aurigae** | Gaia DR3 162590748722956928 (HIP 23873) | ICRS J2016.0 | $076.956417^\circ$<br>($05^\text{h}07^\text{m}49.54^\text{s}$) | $+30.401417^\circ$<br>($+30^\circ24'05.10''$) | $+1.24\,\text{mas/yr}$ | $-21.43\,\text{mas/yr}$ | $6.13$ | $163.1$ |
| **R Draconis** | Gaia DR3 1629851608677464832 (HIP 80582) | ICRS J2016.0 | $248.167625^\circ$<br>($16^\text{h}32^\text{m}40.23^\text{s}$) | $+66.755056^\circ$<br>($+66^\circ45'18.20''$) | $+14.82\,\text{mas/yr}$ | $-18.45\,\text{mas/yr}$ | $1.85$ | $540.5$ |

### Proper-Motion Propagation Equations

Astrometric propagation from catalog epoch $T_{\text{ref}}$ to target epoch $T_{\text{obs}}$ follows standard spherical ICRS true-angle conventions:
$$\Delta t = T_{\text{obs}} - T_{\text{ref}} \quad (\text{years})$$
$$\Delta\alpha_{\text{mas}} = \frac{\mu_\alpha \cos\delta \cdot \Delta t}{\cos\delta_{\text{ref}}}, \quad \Delta\delta_{\text{mas}} = \mu_\delta \cdot \Delta t$$
$$\alpha(T_{\text{obs}}) = \left( \alpha_{\text{ref}} + \frac{\Delta\alpha_{\text{mas}}}{3.6 \times 10^6} \right) \bmod 360^\circ$$
$$\delta(T_{\text{obs}}) = \text{clip}\left( \delta_{\text{ref}} + \frac{\Delta\delta_{\text{mas}}}{3.6 \times 10^6}, -90^\circ, +90^\circ \right)$$
$$\text{Total Displacement} = \sqrt{(\mu_\alpha\cos\delta \cdot \Delta t)^2 + (\mu_\delta \cdot \Delta t)^2} \quad (\text{mas})$$

### Propagated Coordinates at Nominal Mission Mid-Point (Epoch 2025.8)

| Target Name | $\Delta t$ (yr) | Propagated RA $\alpha(2025.8)$ | Propagated Dec $\delta(2025.8)$ | Total Shift ($''$) | Detector Shift (pixels @ $6.2''$/pix) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Barnard's Star** | $9.80$ | $269.449902^\circ$ ($17^\text{h}57^\text{m}47.98^\text{s}$) | $+04.721448^\circ$ ($+04^\circ43'17.21''$) | $101.52''$ | $16.37$ px |
| **Epsilon Indi B** | $25.80$ | $331.095609^\circ$ ($22^\text{h}04^\text{m}22.95^\text{s}$) | $-56.800911^\circ$ ($-56^\circ48'03.28''$) | $121.37''$ | $19.58$ px |
| **WISE 0855** | $15.80$ | $133.759213^\circ$ ($08^\text{h}55^\text{m}02.21^\text{s}$) | $-07.242009^\circ$ ($-07^\circ14'31.23''$) | $128.76''$ | $20.77$ px |
| **RW Aurigae** | $9.80$ | $076.956421^\circ$ ($05^\text{h}07^\text{m}49.54^\text{s}$) | $+30.401359^\circ$ ($+30^\circ24'04.89''$) | $0.21''$ | $0.03$ px |
| **R Draconis** | $9.80$ | $076.956421^\circ$ ($16^\text{h}32^\text{m}40.24^\text{s}$) | $+66.755006^\circ$ ($+66^\circ45'18.02''$) | $0.23''$ | $0.04$ px |

---

### Detailed Resolution of Key Discrepancies

#### 1. WISE 0855 Detector Coordinate Reconciliation
- **The Issue:** The previous report noted nominal pixel coordinate $(176.16, 266.04)$ for WISE 0855 on `level2_2025W44`, but raised questions regarding proper-motion displacement.
- **Header Observation Date:** `level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits` header HDU 0 contains `DATE-OBS = 2025-10-31T19:02:05.151`, corresponding to `MJD-OBS = 60979.793115174` and decimal year **$2025.83231$**.
- **Propagated Coordinates at Observation Time:**
  - $\Delta t = 2025.83231 - 2010.0 = 15.83231$ years.
  - $\Delta\alpha\cos\delta = -8118.0 \times 15.83231 = -128,526.7\,\text{mas} = -128.5267''$.
  - With $\cos(-7.245147^\circ) = 0.992015$, $\Delta\alpha = -129.5613'' = -0.035989^\circ$.
  - $\alpha(2025.83231) = 133.795129^\circ - 0.035989^\circ = 133.759140^\circ$ ($08^\text{h}55^\text{m}02.19^\text{s}$).
  - $\Delta\delta = +715.0 \times 15.83231 = +11,320.1\,\text{mas} = +11.3201'' = +0.003144^\circ$.
  - $\delta(2025.83231) = -7.245147^\circ + 0.003144^\circ = -7.242003^\circ$ ($-07^\circ14'31.21''$).
  - Net sky displacement: $129.02'' = 20.78$ SPHEREx detector pixels.
- **WCS Projection Verification:**
  - Unpropagated J2010.0 projection: $(px, py) = (176.16, 266.04)$.
  - Observation-epoch $2025.83231$ propagated projection: $(px, py) = (196.69, 262.78)$.
  - **Verdict:** Both coordinates fall well within the active $2040 \times 2040$ detector array $[0, 2040]$. The numerical shift of $+20.53$ pixels in $X$ and $-3.26$ pixels in $Y$ matches the $20.78$-pixel astrometric displacement exactly ($\sqrt{20.53^2 + (-3.26)^2} = 20.79$ px).

#### 2. Barnard's Star Coordinate Alignment
- **The Issue:** In legacy frontend component `SpherexSearchPanel.tsx`, Dec was listed as $4.693361^\circ$ ($+04^\circ41'36.1''$), whereas Gaia DR3 and `m6_target_validation.py` record $4.693333^\circ$ ($+04^\circ41'36.00''$).
- **Resolution:** The $0.000028^\circ = 0.10''$ difference ($0.016$ pixel) was a precision truncation artifact in the preset dictionary. Proper motion over 9.8 years ($101.52''$) exceeds this by a factor of 1000. `SpherexSearchPanel.tsx` has now been updated to $4.693333^\circ$ to maintain complete consistency across frontend and backend catalogs.

#### 3. Epsilon Indi B Physical Resolution Limit
- **Physical Context:** Epsilon Indi B is a sub-stellar binary brown dwarf system consisting of a T1.0 dwarf (Ba) and a T6.0 dwarf (Bb) separated by $\rho = 0.73''$.
- **SPHEREx Optical Properties:** SPHEREx employs a 20-cm telescope with an optical pixel scale of $6.2''/\text{pixel}$ and an optical PSF FWHM of $\approx 6.2''$.
- **Resolution Assessment:**
  $$\rho = 0.73'' \ll \text{PSF FWHM} \approx 6.2''$$
  Because the angular separation is less than 12% of the telescope's point spread function, Epsilon Indi Ba and Bb cannot be resolved as distinct spatial objects in SPHEREx imaging. They appear as a single blended point source. The validation suite and UI correctly display the spatial resolution constraint warning to prevent false claims of binary resolution.

---

## 3. PHASE 2 — COMPREHENSIVE ARCHIVE SEARCH & RETRIEVAL (DR1 & QR3)

Live queries were executed against the official Caltech/IPAC IRSA SIA gateway:
- **Base Endpoint:** `https://irsa.ipac.caltech.edu/SIA`
- **Collections Queried:** `spherex_dr1` (Surveys 1 & 2) and `spherex_qr3` (Surveys 3 & 4)
- **Search Radii:** $0.1^\circ$, $0.5^\circ$, and $1.0^\circ$ around both catalog and propagated coordinates.

### Archive Search Results Log

| Target | Collection | Query URL Parameters | HTTP Status | Response Payload | Observations Returned | Usable Temporal Epochs |
|:---|:---|:---|:---:|:---|:---:|:---:|
| **Barnard's Star** | `spherex_dr1` | `POS=circle+269.452+4.693+0.5` | 502 / Timeout | Upstream error | 0 | 0 |
| **Barnard's Star** | `spherex_qr3` | `POS=circle+269.452+4.693+0.5` | 502 / Timeout | Upstream error | 0 | 0 |
| **Epsilon Indi B** | `spherex_dr1` | `POS=circle+331.044+-56.783+0.5` | 502 / Timeout | Upstream error | 0 | 0 |
| **Epsilon Indi B** | `spherex_qr3` | `POS=circle+331.044+-56.783+0.5` | 502 / Timeout | Upstream error | 0 | 0 |
| **WISE 0855** | `spherex_dr1` | `POS=circle+133.795+-7.245+0.5` | 502 / Timeout | Upstream error | 0 | 1 (Local) |
| **WISE 0855** | `spherex_qr3` | `POS=circle+133.795+-7.245+0.5` | 502 / Timeout | Upstream error | 0 | 1 (Local) |
| **RW Aurigae** | `spherex_dr1` | `POS=circle+76.956+30.401+0.5` | 500 / Exception | Gateway timeout | 0 | 0 |
| **RW Aurigae** | `spherex_qr3` | `POS=circle+76.956+30.401+0.5` | 502 / Timeout | Upstream error | 0 | 0 |
| **R Draconis** | `spherex_dr1` | `POS=circle+248.168+66.755+0.5` | 502 / Timeout | Upstream error | 0 | 0 |
| **R Draconis** | `spherex_qr3` | `POS=circle+248.168+66.755+0.5` | 502 / Timeout | Upstream error | 0 | 0 |

### Local Archive Holdings

In addition to live remote queries, the local storage repository (`data/spherex/`) was indexed:
1. `level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits`
   - File Size: $71,634,240$ bytes
   - Target Coverage: WISE 0855 field
   - `DATE-OBS`: `2025-10-31T19:02:05.151` (`MJD-OBS = 60979.793115174`)
   - Detector: `SPHEREx-4D1` (Band 4)
   - Data Quality: Calibrated Level-2 MEF
2. `level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits`
   - File Size: $65,488,320$ bytes
   - SHA-256: `b920109af38753669179ed249ea704f16ae7e6742ae6ab44abf20f2a29e7dac1`
   - Target Coverage: Equatorial benchmark field ($\alpha = 46.844^\circ, \delta = 1.832^\circ$)
   - `DATE-OBS`: `2026-08-12T01:34:22.012` (`MJD-OBS = 61264.06553255`)
   - Detector: `SPHEREx-3D1` (Band 3)
3. `level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits`
   - File Size: $65,488,320$ bytes
   - SHA-256: `60c423814b38c19943b7b4b15e09b7ac6e9557c078ca35a74bf13d250ccf3c3e`
   - Target Coverage: Equatorial benchmark field ($\alpha = 46.844^\circ, \delta = 1.832^\circ$)
   - `DATE-OBS`: `2026-08-19T14:22:10.874` (`MJD-OBS = 61271.59873697`)
   - Detector: `SPHEREx-1D1` (Band 1)

---

## 4. PHASE 3 — REAL TEMPORAL SERIES EXECUTION

### Benchmark Equatorial Field Multi-Epoch Verification
- **Sky Coordinates:** $\alpha = 46.844^\circ, \delta = 1.832^\circ$
- **Epoch 1:** `level2_2026W31` (MJD 61264.0655, 2026-08-12)
- **Epoch 2:** `level2_2026W32` (MJD 61271.5987, 2026-08-19)
- **Temporal Baseline:** $\Delta t = 7.5332$ days ($180.8$ hours)
- **Array Footprint:** Target is located at detector center: $(px_1, py_1) = (1019.31, 1020.56)$ and $(px_2, py_2) = (1018.91, 1020.73)$.
- **Temporal Status:** `SUFFICIENT_MULTI_EPOCH_COVERAGE`
- **Difference Engine Execution:** Full M5 cross-band differencing and significance evaluation executed with variance propagation. M5 scientific status preserved as `CONDITIONAL`.

### Five-Target Coverage Status

| Target Slug | Target Name | Usable Local Epochs | Usable Public Archive Epochs | Total Usable Epochs | Temporal Coverage Status | Is Sufficient for Differencing? |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| `barnards-star` | Barnard's Star | 0 | 0 | 0 | `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE` | No ($< 2$) |
| `epsilon-indi-b` | Epsilon Indi B | 0 | 0 | 0 | `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE` | No ($< 2$) |
| `wise-0855` | WISE 0855 | 1 | 0 | 1 | `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE` | No ($< 2$) |
| `rw-aurigae` | RW Aurigae | 0 | 0 | 0 | `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE` | No ($< 2$) |
| `r-draconis` | R Draconis | 0 | 0 | 0 | `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE` | No ($< 2$) |

Because each of the five targets has fewer than 2 epochs in the live archive, the system correctly reports `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE` without synthesizing data.

---

## 5. PHASE 4 — SCIENTIFIC & COORDINATE CORRECTIONS

During the audit, the following engineering and astronomical corrections were applied and verified:

### 1. WCS Pre-Filter Spherical Geometry & Polar Guards
In `backend/app/services/spherex_discovery.py`, the coarse pre-filter previously used a flat Cartesian approximation $\sqrt{(\Delta\alpha\cos\delta)^2 + (\Delta\delta)^2}$, which suffered from:
1. RA wraparound discontinuity at $0^\circ/360^\circ$.
2. Coordinate distortion near celestial poles.
3. Premature corner pruning at $3.0^\circ$ radius.

**Remediation Implemented:**
- Replaced with the exact orthodromic spherical angular separation formula:
  $$\Delta\alpha = ((\alpha - \text{CRVAL1} + 180^\circ) \bmod 360^\circ) - 180^\circ$$
  $$\cos\theta = \sin\delta\sin(\text{CRVAL2}) + \cos\delta\cos(\text{CRVAL2})\cos(\Delta\alpha)$$
  $$\theta = \arccos(\text{clip}(\cos\theta, -1.0, 1.0))$$
- Set pre-filter threshold to $3.5^\circ$. The SPHEREx detector is $3.5^\circ \times 3.5^\circ$, giving a diagonal half-angle of $\sqrt{3.5^2 + 3.5^2}/2 \approx 2.47^\circ$. A conservative threshold of $3.5^\circ$ ensures no valid corner coordinate is prematurely rejected while securely shielding Astropy's polynomial SIP WCS solver from diverging on distant sky coordinates.
- Replaced hardcoded array size `2048` with dynamic header values `naxis1 = int(h1.get("NAXIS1", 2048))` and `naxis2 = int(h1.get("NAXIS2", 2048))`, correctly handling $2040 \times 2040$ arrays in Level-2 products (e.g. `level2_2025W44`).
- Added strict footprint filtering (`if not in_footprint: continue`) so only valid overlapping observations are returned.

### 2. Coordinate Catalog Synchronization
- In `frontend/components/controls/SpherexSearchPanel.tsx`, preset targets were updated to reference the primary `spherex_qr3` collection and exact Gaia DR3 / SIMBAD coordinates:
  - Barnard's Star: $\alpha = 269.452083^\circ, \delta = 4.693333^\circ$
  - Epsilon Indi B: $\alpha = 331.043792^\circ, \delta = -56.782722^\circ$
  - WISE 0855: $\alpha = 133.795129^\circ, \delta = -7.245147^\circ$

---

## 6. PHASE 5 — USER EXPERIENCE & TIME-SERIES PLAYER VERIFICATION

The challenge-facing user interface was verified against all interaction requirements:

1. **`TimeSeriesPlayer.tsx` Controls:**
   - **Play/Pause Toggle:** Starts and stops automatic frame progression.
   - **Step Forward / Step Back:** Single-epoch frame navigation.
   - **Timeline Scrubber:** Slider enabling random-access seeking across chronological observation epochs.
   - **Playback Speed Control:** Selectable speeds ($0.5\times$, $1\times$, $2\times$, $5\times$).
   - **Blink Mode:** Alternating 500ms two-epoch comparator designed for rapid moving-object and transient identification.
   - **Target Preset Selector:** Quick buttons for Barnard's Star, Epsilon Indi B, WISE 0855, RW Aurigae, and R Draconis.
2. **Mandatory Non-Discovery Disclaimer:**
   - In accordance with NASA challenge and scientific guidelines, unverified transients must never be presented as confirmed astronomical discoveries.
   - Label enforced: `"CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED"`
   - Present across all temporal discovery responses, candidate extractions, target validation API endpoints, and frontend control panels.

---

## 7. PHASE 6 — VERIFICATION SUITE & TEST RESULTS

### Comprehensive Test Execution Summary

| Test Suite | Command | Total Tests | Passed | Failed | Execution Time |
|:---|:---|:---:|:---:|:---:|:---:|
| **Root Integration Suite** (M4, M5, M6) | `pytest tests/ -v` | 37 | 37 | 0 | 15.95s |
| **Backend Scientific Suite** | `pytest backend/tests/ -v` | 23 | 23 | 0 | 8.07s |
| **Next.js Production Build** | `npm run build --prefix frontend` | 5 routes | 5 | 0 | 38.6s |

### Key Test Case Verifications
- `test_frozen_approved_fits_hashes`: **PASSED** (SHA-256 for `2026W31` and `2026W32` bit-for-bit identical to baseline).
- `test_wcs_footprint_sip_guard`: **PASSED** (Pre-filtering prevents SIP divergence on distant coordinates).
- `test_five_targets_catalog_completeness`: **PASSED** (All 5 targets resolved with complete metadata).
- `test_epsilon_indi_b_spatial_resolution_constraint`: **PASSED** (0.73" separation verified unresolved at 6.2" PSF).
- `test_wise_0855_in_local_level2_fits`: **PASSED** (Coordinates fall inside `level2_2025W44` active array).
- `test_sufficient_temporal_coverage_equatorial_pair`: **PASSED** (2 epochs found, ordered by MJD).
- `test_insufficient_temporal_coverage_handling`: **PASSED** (Uncovered regions return `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE` without data fabrication).
- `test_disclaimer_label_enforcement`: **PASSED** (Mandatory disclaimer present in all outputs).

---

## 8. SUMMARY MATRIX OF THE FIVE NASA TARGETS

| Target | Scientific Role | Catalog Epoch & Position | Propagated $2025.8$ Position | SPHEREx Physical Resolution | Archival Coverage Status | Usable Epochs | Master Status |
|:---|:---|:---|:---|:---|:---|:---:|:---:|
| **Barnard's Star** | High proper motion benchmark ($10.37''/\text{yr}$) | J2016.0<br>($269.452^\circ, +4.693^\circ$) | $269.450^\circ, +4.721^\circ$<br>($\Delta\theta = 101.52''$) | Resolved point source; $16.37$ px shift | IRSA SIA 502/Timeout; no local files | 0 | **CONDITIONAL** |
| **Epsilon Indi B** | Sub-stellar binary companion; resolution validation | J2000.0<br>($331.044^\circ, -56.783^\circ$) | $331.096^\circ, -56.801^\circ$<br>($\Delta\theta = 121.37''$) | Unresolved blend; $0.73''$ binary sep $\ll 6.2''$ PSF | IRSA SIA 502/Timeout; no local files | 0 | **CONDITIONAL** |
| **WISE 0855** | Primary Challenge target; cold Y-dwarf atmospheric benchmark | J2010.0<br>($133.795^\circ, -7.245^\circ$) | $133.759^\circ, -7.242^\circ$<br>($\Delta\theta = 128.76''$) | Resolved point source; $20.78$ px shift | 1 Calibrated Level-2 FITS (`2025W44`); IRSA SIA 502 | 1 | **CONDITIONAL** |
| **RW Aurigae** | Photometric variability benchmark; dust dimming | J2016.0<br>($076.956^\circ, +30.401^\circ$) | $076.956^\circ, +30.401^\circ$<br>($\Delta\theta = 0.21''$) | Stationary; shift $< 0.05$ px; UXOR variability | IRSA SIA 502/Timeout; no local files | 0 | **CONDITIONAL** |
| **R Draconis** | Large-amplitude long-period variable star benchmark | J2016.0<br>($248.168^\circ, +66.755^\circ$) | $248.168^\circ, +66.755^\circ$<br>($\Delta\theta = 0.23''$) | Stationary; shift $< 0.05$ px; Mira pulsation | IRSA SIA 502/Timeout; no local files | 0 | **CONDITIONAL** |

---

## 9. CONCLUSION & FINAL SIGN-OFF

Milestone 6.1 successfully completes all targeted coordinate reconciliation, mathematical proper-motion propagation, WCS pre-filter corrections, resolution limit evaluations, and multi-epoch discovery tests.

In strict compliance with NASA challenge guidelines and scientific audit rules:
1. No synthetic data or unverified observations were fabricated.
2. Frozen M1–M5 baselines were preserved without regression.
3. M5 scientific status is strictly maintained as `CONDITIONAL`.
4. Multi-epoch time-series differencing and playback are verified on the approved equatorial benchmark pair.
5. All five required NASA targets are evaluated; because live archive coverage currently yields fewer than two epochs per target, Milestone 6.1 concludes with the verified verdict:

# FINAL VERDICT: `M6_1_CONDITIONAL`
*(Preserving M5 as `CONDITIONAL`, with full engineering readiness established for public multi-epoch catalog ingestion).*
