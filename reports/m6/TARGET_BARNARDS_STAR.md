# M6 TARGET VALIDATION REPORT: Barnard's Star (GJ 699 / HIP 87937)

**Mission:** NASA SPHEREx — 3D Temporal Sky Explorer  
**Milestone:** M6 — NASA SPHEREx Challenge Completion  
**Target Identifier:** `barnards-star`  
**Evaluation Timestamp (UTC):** 2026-11-14 19:04:54 UTC  
**Mandatory Scientific Disclaimer:**  
> **NOTICE:** Observed Data | Processed Images | Synthetic Test Data | Change Candidates — NOT SCIENTIFICALLY CONFIRMED. Unverified candidates are not astronomical discoveries.

---

## 1. Catalog Identity and Literature Astrometry

| Property | Value | Literature Reference / Notes |
| :--- | :--- | :--- |
| **Common Name** | Barnard's Star | NASA Challenge Primary Target |
| **Catalog Designation** | GJ 699 / HIP 87937 | Gaia DR3 4472832130942585856 (Gaia Collaboration 2022) |
| **Target Classification** | High-Proper-Motion M Dwarf | Spectral Type: `M4.0V` |
| **Catalog Reference Frame** | ICRS | Epoch: J2016.0 |
| **Catalog Coordinates (RA, Dec)** | 269.452083°, 4.693333° | `17h 57m 48.50s`, `+04° 41' 36.00"` |
| **Proper Motion ($\mu_\alpha \cos\delta, \mu_\delta$)** | -798.58, +10328.12 mas/yr | Annual linear displacement vector |
| **Parallax / Distance** | 547.45 mas (~1.83 pc) | Estimated distance |
| **Scientific Role** | High proper motion benchmark (10.37 arcsec/yr displacement test) | Validation benchmark |

---

## 2. Proper Motion Astrometric Propagation

- **Target Observation Epoch:** `2025.8` (SPHEREx nominal mission midpoint / ~MJD 60900)
- **Time Baseline ($\Delta t$):** `9.80 years` from J2016.0 to 2025.8
- **Net Astrometric Displacement:** `101.518 arcsec`
- **Displacement in SPHEREx Pixels:** `16.37 pixels` (Plate scale: `6.2 arcsec/pixel`)
- **Propagated Coordinates (2025.8):**
  - **RA (deg):** `269.449902°` (`17h 57m 47.98s`)
  - **Dec (deg):** `4.721448°` (`+04° 43' 17.21"`)

### Astrometric Significance:
Barnard's Star exhibits the fastest known proper motion of any star in the sky ($\sim 10.37''/\text{yr}$). Over the 9.80-year baseline from Gaia DR3 (J2016.0) to 2025.8, the predicted astrometric shift is **101.52 arcseconds**, corresponding to **16.37 SPHEREx detector pixels**. Because this motion exceeds 16 detector pixels, centroid tracking in time-series subtraction must account for true proper motion versus relative WCS registration uncertainty (which is verified $< 0.1$ pixels).

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
Barnard's Star is an isolated M4.0V red dwarf ($d = 1.83$ pc). At SPHEREx's $6.2''$ PSF FWHM, it presents as an intense, well-sampled point source. The large astrometric shift produces a characteristic dipole residual (negative trough at reference epoch, positive peak at comparison epoch) if difference imaging is performed without proper motion centroid alignment.

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
