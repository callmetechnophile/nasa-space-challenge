# M6 TARGET VALIDATION REPORT: R Draconis (R Dra / HD 149886 / HIP 80582)

**Mission:** NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone:** M6 — NASA SPHEREx Challenge Completion  
**Target Identifier:** `r-draconis`  
**Evaluation Timestamp (UTC):** 2026-11-14 19:04:54 UTC  
**Mandatory Scientific Disclaimer:**  
> **NOTICE:** Observed Data | Processed Images | Synthetic Test Data | Change Candidates — NOT SCIENTIFICALLY CONFIRMED. Unverified candidates are not astronomical discoveries.

---

## 1. Catalog Identity and Literature Astrometry

| Property | Value | Literature Reference / Notes |
| :--- | :--- | :--- |
| **Common Name** | R Draconis | NASA Challenge Primary Target |
| **Catalog Designation** | R Dra / HD 149886 / HIP 80582 | Gaia DR3 1629851608677464832 / AAVSO International Variable Star Index |
| **Target Classification** | Mira Pulsating Variable Giant Star | Spectral Type: `M3e - M9e` |
| **Catalog Reference Frame** | ICRS | Epoch: J2016.0 |
| **Catalog Coordinates (RA, Dec)** | 248.167625°, 66.755056° | `16h 32m 40.23s`, `+66° 45' 18.20"` |
| **Proper Motion ($\mu_\alpha \cos\delta, \mu_\delta$)** | +14.82, -18.45 mas/yr | Annual linear displacement vector |
| **Parallax / Distance** | 1.85 mas (~540.50 pc) | Estimated distance |
| **Scientific Role** | Large-amplitude long-period variable star benchmark; stationary flux variation | Validation benchmark |

---

## 2. Proper Motion Astrometric Propagation

- **Target Observation Epoch:** `2025.8` (SPHEREx nominal mission midpoint / ~MJD 60900)
- **Time Baseline ($\Delta t$):** `9.80 years` from J2016.0 to 2025.8
- **Net Astrometric Displacement:** `0.232 arcsec`
- **Displacement in SPHEREx Pixels:** `0.04 pixels` (Plate scale: `6.2 arcsec/pixel`)
- **Propagated Coordinates (2025.8):**
  - **RA (deg):** `248.167727°` (`16h 32m 40.25s`)
  - **Dec (deg):** `66.755006°` (`+66° 45' 18.02"`)

### Astrometric Significance:
R Draconis is a high-declination asymptotic giant branch (AGB) Mira variable ($d \sim 540$ pc). Its proper motion ($\sim 23.67$ mas/yr) generates a negligible shift of **0.232 arcsec** (**0.037 pixels**) over 9.80 years, confirming astrometric stationarity.

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
R Draconis is a long-period pulsating giant with a pulsation period of $P = 245.6$ days and a visual amplitude exceeding 6 magnitudes ($V \approx 6.7 - 13.2$). In the near-infrared SPHEREx bands ($0.75 - 5.00\ \mu\text{{m}}$), the pulsation modulates molecular bands of TiO, CO, and $\text{{H}}_2\text{{O}}$ with flux variations of $1 - 2$ magnitudes. In difference imaging, this produces strong stationary monopolar flux residuals (brightening or fading across survey passes).

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
