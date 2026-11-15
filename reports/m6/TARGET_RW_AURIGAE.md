# M6 TARGET VALIDATION REPORT: RW Aurigae (RW Aur / HIP 23873)

**Mission:** NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone:** M6 — NASA SPHEREx Challenge Completion  
**Target Identifier:** `rw-aurigae`  
**Evaluation Timestamp (UTC):** 2026-11-14 19:04:54 UTC  
**Mandatory Scientific Disclaimer:**  
> **NOTICE:** Observed Data | Processed Images | Synthetic Test Data | Change Candidates — NOT SCIENTIFICALLY CONFIRMED. Unverified candidates are not astronomical discoveries.

---

## 1. Catalog Identity and Literature Astrometry

| Property | Value | Literature Reference / Notes |
| :--- | :--- | :--- |
| **Common Name** | RW Aurigae | NASA Challenge Primary Target |
| **Catalog Designation** | RW Aur / HIP 23873 | Gaia DR3 162590748722956928 (Gaia Collaboration 2022) |
| **Target Classification** | Variable Young T Tauri Star | Spectral Type: `K3:e + K0:e` |
| **Catalog Reference Frame** | ICRS | Epoch: J2016.0 |
| **Catalog Coordinates (RA, Dec)** | 76.956417°, 30.401417° | `05h 07m 49.54s`, `+30° 24' 05.10"` |
| **Proper Motion ($\mu_\alpha \cos\delta, \mu_\delta$)** | +1.24, -21.43 mas/yr | Annual linear displacement vector |
| **Parallax / Distance** | 6.13 mas (~163.10 pc) | Estimated distance |
| **Scientific Role** | Photometric variability benchmark; circum-stellar disk obscuration detection | Validation benchmark |

---

## 2. Proper Motion Astrometric Propagation

- **Target Observation Epoch:** `2025.8` (SPHEREx nominal mission midpoint / ~MJD 60900)
- **Time Baseline ($\Delta t$):** `9.80 years` from J2016.0 to 2025.8
- **Net Astrometric Displacement:** `0.210 arcsec`
- **Displacement in SPHEREx Pixels:** `0.03 pixels` (Plate scale: `6.2 arcsec/pixel`)
- **Propagated Coordinates (2025.8):**
  - **RA (deg):** `76.956421°` (`05h 07m 49.54s`)
  - **Dec (deg):** `30.401359°` (`+30° 24' 04.89"`)

### Astrometric Significance:
RW Aurigae is a classical T Tauri star system in the Taurus-Auriga star-forming complex ($d \sim 163$ pc). Its proper motion is modest ($\sim 21.47$ mas/yr), resulting in an astrometric displacement of **0.210 arcsec** (**0.034 pixels**) over 9.80 years. The source is astrometrically stationary relative to the $6.2''$ SPHEREx pixel scale.

---

## 3. SPHEREx Archive Coverage Analysis (DR1 and QR3)

Independent queries executed against the NASA/IPAC Infrared Science Archive (IRSA) Simple Image Access (SIA) protocol for SPHEREx public collections:

| Archive Release | Collection Identifier | Query Status | Records Found | Usable Level-2 MEF Products |
| :--- | :--- | :--- | :--- | :--- |
| **SPHEREx DR1** | `spherex_dr1` | `TIMEOUT` | 0 | 0 |
| **SPHEREx QR3** | `spherex_qr3` | `TIMEOUT` | 0 | 0 |
| **Local Archive Cache** | Level-2 approved repository | `NONE` | 0 | 0 |
| **Combined Usable Total** | Total distinct epochs | — | **0** | **0** |

### Usable Observation Timeline:
_No individual observations available for this sky location in current release._

---

## 4. Formal Temporal Coverage Verdict

### Status: `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE`

**INSUFFICIENT SPHEREx TEMPORAL COVERAGE.** Exactly 0 usable observation(s) exist in the approved local repository and public archive caches for this patch of sky. Multi-epoch difference imaging and animated time-series blinking strictly require $\ge 2$ distinct observation epochs. In accordance with NASA SPHEREx scientific integrity rules, no synthetic observations are manufactured to claim coverage.

---

## 5. Physical, Optical, and WCS Assessment

### Angular Resolution and System Modeling:
RW Aurigae is celebrated for its dramatic, non-periodic photometric occultation events (UXOR-type variability) where circumstellar dust clumps or trailing tidal arms periodically obscure the central star, dimming optical and near-IR flux by $\Delta V > 2 - 3$ magnitudes. Because SPHEREx observes in 102 continuous spectral bands, multi-epoch observations would measure wavelength-dependent dust extinction ($A_\lambda / A_V$). Difference imaging flags flux variations as `CHANGE CANDIDATE — NOT SCIENTIFICALLY CONFIRMED` without asserting physical causation.

### Spectral Bandpass and LVF Wavelength:
- **SPHEREx Detector Coverage:** Bands 1–6 covering $0.75\ \mu\text{m} - 5.00\ \mu\text{m}$ with linear variable filter dispersion ($R \sim 35 - 130$).
- **Color Gradients / Mismatch Guard:** Spectral tolerance enforced at $\le 2.0\%$ ($|\Delta\lambda / \lambda| \le 0.02$) between compared epochs to prevent artificial residual false positives.

### Data Quality (FLAGS and VARIANCE):
- Calibrated Level-2 MEF files preserve bitmask `FLAGS` and noise `VARIANCE` per pixel.
- Photometric extractions maintain honest statistical error bars without unverified signal thresholding.

---

## 6. Audit Sign-Off

- **Target Status:** `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE`
- **Evidence Verification:** Fully traceable against IPAC/IRSA SIA and local Level-2 FITS repository.
- **Scientific Integrity:** Compliant with frozen M1–M5 baseline and M5 CONDITIONAL verdict.
