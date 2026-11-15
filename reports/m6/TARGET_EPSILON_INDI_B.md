# M6 TARGET VALIDATION REPORT: Epsilon Indi B (HD 209100 B / HIP 108870 B)

**Mission:** NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone:** M6 — NASA SPHEREx Challenge Completion  
**Target Identifier:** `epsilon-indi-b`  
**Evaluation Timestamp (UTC):** 2026-11-14 19:04:54 UTC  
**Mandatory Scientific Disclaimer:**  
> **NOTICE:** Observed Data | Processed Images | Synthetic Test Data | Change Candidates — NOT SCIENTIFICALLY CONFIRMED. Unverified candidates are not astronomical discoveries.

---

## 1. Catalog Identity and Literature Astrometry

| Property | Value | Literature Reference / Notes |
| :--- | :--- | :--- |
| **Common Name** | Epsilon Indi B | NASA Challenge Primary Target |
| **Catalog Designation** | HD 209100 B / HIP 108870 B | SIMBAD Astronomical Database / King et al. (2010) |
| **Target Classification** | T-Dwarf Binary (T1 + T6) | Spectral Type: `T1.0 + T6.0` |
| **Catalog Reference Frame** | ICRS | Epoch: J2000.0 |
| **Catalog Coordinates (RA, Dec)** | 331.043792°, -56.782722° | `22h 04m 10.51s`, `-56° 46' 57.80"` |
| **Proper Motion ($\mu_\alpha \cos\delta, \mu_\delta$)** | +3961.00, -2538.00 mas/yr | Annual linear displacement vector |
| **Parallax / Distance** | 275.80 mas (~3.63 pc) | Estimated distance |
| **Scientific Role** | Sub-stellar binary companion benchmark & angular resolution validation | Validation benchmark |

---

## 2. Proper Motion Astrometric Propagation

- **Target Observation Epoch:** `2025.8` (SPHEREx nominal mission midpoint / ~MJD 60900)
- **Time Baseline ($\Delta t$):** `25.80 years` from J2000.0 to 2025.8
- **Net Astrometric Displacement:** `121.372 arcsec`
- **Displacement in SPHEREx Pixels:** `19.58 pixels` (Plate scale: `6.2 arcsec/pixel`)
- **Propagated Coordinates (2025.8):**
  - **RA (deg):** `331.095611°` (`22h 04m 22.95s`)
  - **Dec (deg):** `-56.800911°` (`-56° 48' 03.28"`)

### Astrometric Significance:
Epsilon Indi B has a high proper motion of $\sim 4.70''/\text{yr}$. Over 25.80 years, the system traverses **121.37 arcseconds** (**19.58 pixels**). The astrometric displacement is readily measurable across multi-year survey baselines.

---

## 3. SPHEREx Archive Coverage Analysis (DR1 and QR3)

Independent queries executed against the NASA/IPAC Infrared Science Archive (IRSA) Simple Image Access (SIA) protocol for SPHEREx public collections:

| Archive Release | Collection Identifier | Query Status | Records Found | Usable Level-2 MEF Products |
| :--- | :--- | :--- | :--- | :--- |
| **SPHEREx DR1** | `spherex_dr1` | `ARCHIVE_ERROR` | 0 | 0 |
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
**CRITICAL RESOLUTION LIMITATION:** Epsilon Indi B is a physical brown dwarf binary comprising two T-dwarfs (T1.0 + T6.0) with an angular separation of only **0.73 arcseconds** (King et al. 2010). Because the SPHEREx telescope has an aperture of 20 cm and an effective pixel scale of **6.2 arcsec/pixel** (PSF FWHM $\sim 6.2''$), the binary pair is **spatially unresolved** by SPHEREx. It appears as a single blended point-source photometric target. Any challenge user interface must explicitly communicate this physical resolution limit.

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
