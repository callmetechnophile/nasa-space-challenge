# SkyTrace
## Technical Architecture & Scientific Systems Specification
**NASA Space Apps Challenge 2026**

---

### 1. Executive Summary

**SkyTrace** is a full-stack scientific astronomy development environment developed for exploring and analyzing observations from NASA's Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices Explorer (SPHEREx) mission.

Unlike static dashboards or decorative simulations, this system implements an interactive 3D WebGL celestial sphere coupled with an Astropy-driven scientific image processing and difference imaging backend. It enables researchers, students, and astronomers to navigate the sky in verified celestial coordinates (ICRS), evaluate temporal infrared changes over 6-month survey passes, and inspect near-infrared spectroscopy across all 102 Linear Variable Filter (LVF) spectral channels spanning 0.75 to 5.00 µm.

---

### 2. System Architecture Overview

```
                                  +---------------------------------------------+
                                  |            CLIENT / WEB BROWSER             |
                                  |         (Next.js / React 19 / R3F)          |
                                  +----------------------+----------------------+
                                                         |
                   +-------------------------------------+-------------------------------------+
                   |                                     |                                     |
+------------------v------------------+  +---------------v------------------+  +---------------v------------------+
|      3D CELESTIAL ENGINE            |  |    TEMPORAL & SPECTRAL HUD       |  |     COORDINATE SEARCH BAR        |
|  - Three.js / React Three Fiber     |  |  - Chronological 4-pass player   |  |  - Decimal & Sexagesimal parser  |
|  - Instanced 5,000+ Star Catalog    |  |  - Blink comparator engine       |  |  - Camera flight slerp/lerp      |
|  - RA Hour Circles & Dec Parallels  |  |  - Side-by-side synchronized view|  |  - Dynamic URL parameter routing |
|  - Constellation Stick Figures      |  |  - SVG 102-band SED visualizer   |  |  - Galactic (l, b) & Ecliptic    |
|  - Galactic & Ecliptic Great Circles|  |  - Interactive feature markers   |  |  - 5 NASA benchmark presets      |
|  - WCS-oriented Cutout Projections  |  |  - Scientific asinh/log stretch  |  |                                  |
+-------------------------------------+  +----------------------------------+  +----------------------------------+
                                                         |
                                            JSON API & FITS / PNG Streams
                                                         |
                                  +----------------------v----------------------+
                                  |          SCIENTIFIC API BACKEND             |
                                  |            (FastAPI / Python)               |
                                  +----------------------+----------------------+
                                                         |
        +--------------------------------+---------------+-------------------------------+
        |                                |                               |               |
+-------v-------+              +---------v---------+           +---------v---------+     |
|  COORDINATE   |              | IMAGE PROCESSING  |           |     SPECTRAL      |     |
|    ENGINE     |              |    & WCS ENGINE   |           |    BAND ENGINE    |     |
| - Astropy ICRS|              | - Astropy WCS     |           | - 102 LVF Bands   |     |
| - SkyCoord    |              | - FITS generator  |           | - Arrays 1 to 6   |     |
| - Sexagesimal |              | - Difference D(xy)|           | - R ~ 35 - 130    |     |
| - Three.js Map|              | - MAD noise floor |           | - Ice signatures  |     |
+---------------+              | - Candidate finder|           +-------------------+     |
                               +-------------------+                                     |
                                                         +-------------------------------+
                                                         |
                                        +----------------v----------------+
                                        |    DATA PROVIDER SUBSYSTEM      |
                                        |  - Curated Sample Provider      |
                                        |  - NASA IRSA / IPAC Connector   |
                                        |  - Mission Simulator (explicit) |
                                        +---------------------------------+
```

---

### 3. Coordinate Transformation Engine

The celestial sphere represents an observer looking out into the celestial sphere in the International Celestial Reference System (ICRS):
- **Right Ascension ($\alpha$)**: Longitude measured eastward from the vernal equinox $[0^\circ, 360^\circ)$ or $[0^h, 24^h)$.
- **Declination ($\delta$)**: Latitude measured perpendicular to celestial equator $[-90^\circ, +90^\circ]$.

#### 3D World Space Projection (Three.js)
To maintain astronomical handedness on the celestial sphere of radius $R$:
$$x = R \cdot \cos(\delta) \cdot \sin(\alpha)$$
$$y = R \cdot \sin(\delta)$$
$$z = -R \cdot \cos(\delta) \cdot \cos(\alpha)$$
where:
- $+Y$ points toward the North Celestial Pole ($\delta = +90^\circ$, Polaris).
- $-Y$ points toward the South Celestial Pole ($\delta = -90^\circ$).
- $-Z$ aligns with Right Ascension $0^h$ ($\alpha = 0^\circ$).
- $+X$ aligns with Right Ascension $6^h$ ($\alpha = 90^\circ$).

#### Sexagesimal Parser
Supports heterogeneous astronomical notations:
- `08h 55m 10.831s` $\rightarrow 133.795129^\circ$
- `-07° 14' 42.53"` $\rightarrow -7.245147^\circ$
- Colon-separated (`08:55:10.83`, `-07:14:42.53`)
- Decimal degrees (`133.7951`, `-7.2451`)

---

### 4. SPHEREx 102 Spectral Bands Architecture

SPHEREx scans the sky through 6 Linear Variable Filter (LVF) detector focal planes:

| Array Index | Wavelength Range ($\mu m$) | Number of Channels | Resolving Power ($R = \lambda/\Delta\lambda$) | Primary Astrophysical Signatures |
|---|---|---|---|---|
| **Array 1** | $0.75 - 1.11$ | 17 | $\sim 41$ | Paschen series, CN absorption, Na I, stellar continuum |
| **Array 2** | $1.11 - 1.64$ | 17 | $\sim 41$ | J/H continuum, FeH, $H_2O$ vapor, Paschen $\beta$ |
| **Array 3** | $1.64 - 2.42$ | 17 | $\sim 41$ | H/K continuum, CO overtone, $H_2$ 1-0 S(1), water vapor |
| **Array 4** | $2.42 - 3.82$ | 17 | $\sim 35$ | $H_2O$ ice ($3.05\,\mu m$), PAH emission ($3.3\,\mu m$), $CH_4$ methane |
| **Array 5** | $3.82 - 4.42$ | 17 | $\sim 110$ | High-res $CO_2$ ice ($4.27\,\mu m$), $^{13}CO_2$ ice, $SO_2$ |
| **Array 6** | $4.42 - 5.00$ | 17 | $\sim 130$ | High-res CO gas & ice ($4.67\,\mu m$), XCN ($4.62\,\mu m$), OCS |

---

### 5. Scientific Difference Imaging & Transient Detection

For two aligned observation epochs $I_1(x, y)$ and $I_2(x, y)$:

1. **Pixel-aligned Differential Flux**:
   $$D(x, y) = I_2(x, y) - I_1(x, y)$$
   $$D_{\text{abs}}(x, y) = |I_2(x, y) - I_1(x, y)|$$

2. **Robust Noise Estimation**:
   To avoid bias from outlier stars or transient brightening, noise $\sigma_{\text{MAD}}$ is calculated via Median Absolute Deviation:
   $$\sigma_{\text{MAD}} = 1.4826 \times \text{median}(|D(x, y) - \text{median}(D(x, y))|)$$

3. **Statistical Significance Thresholding**:
   $$\text{Mask}(x, y) = D_{\text{abs}}(x, y) > (\text{median}(D) + k \cdot \sigma_{\text{MAD}}), \quad k = 3.5$$

4. **Candidate Extraction & Quality Control**:
   Connected pixel clusters are labeled using `scipy.ndimage`. For each candidate:
   - Peak pixel coordinate $(x_p, y_p)$
   - Inverse WCS mapping to $(\alpha_{\text{cand}}, \delta_{\text{cand}})$
   - Differential Signal-to-Noise Ratio: $\text{SNR} = \frac{|D(x_p, y_p)|}{\sigma_{\text{MAD}}}$
   - Quality assessment flags: `EDGE_PROXIMITY`, `TARGET_CENTRAL_RESIDUAL`, `MARGINAL_DETECTION`, `CLEAN_CANDIDATE`.

---

### 6. The Five NASA Validation Targets

| Target | Designation | Class | RA (HMS) | Dec (DMS) | Proper Motion ($\mu_\alpha, \mu_\delta$) | Scientific Verification Role |
|---|---|---|---|---|---|---|
| **Barnard's Star** | GJ 699 | M4.0V | `17h 57m 48.50s` | `+04° 41' 36.00"` | $(-798.6, +10328.1)$ mas/yr | Highest proper motion star (10.3"/yr); astrometric stability verification across multi-epoch surveys |
| **WISE 0855** | WISE J0855-0714 | Y2.0 | `08h 55m 10.83s` | `-07° 14' 42.50"` | $(-8118.0, +715.0)$ mas/yr | Coldest brown dwarf (~250 K); extreme 4.5–5.0 µm atmospheric flux window verification |
| **Epsilon Indi B** | HD 209100B | T1+T6 | `22h 04m 10.51s` | `-56° 46' 57.80"` | $(+3961.0, -2538.0)$ mas/yr | T-dwarf binary; methane ($CH_4$) and water vapor absorption benchmark |
| **RW Aurigae** | RW Aur | K3e | `05h 07m 49.54s` | `+30° 24' 05.10"` | $(+1.2, -21.4)$ mas/yr | Classical young T Tauri star with episodic circumstellar dust occultations and multi-magnitude dimming |
| **R Draconis** | R Dra | M5e-M9e | `16h 32m 40.23s` | `+66° 45' 18.20"` | $(+14.8, -18.5)$ mas/yr | Pulsating Mira variable AGB star (~245.5d period) with massive infrared flux variations |

---

### 7. Milestone 6: Multi-Epoch Sky Explorer & Challenge Completion

Milestone 6 delivers the final challenge-facing public application for NASA's SPHEREx mission:
"Create a public-facing web tool to display images of the sky from the SPHEREx mission, making it easy for anyone to quickly see how they change over time. Users enter RA and Dec coordinates. The application displays a chronological series of images of that sky patch, allowing users to identify moving objects and investigate variable sources."

#### 7.1 Component Architecture:
1. **Frontend Time-Series Player (`frontend/components/temporal/TimeSeriesPlayer.tsx`)**:
   - Interactive playback engine: Play/Pause, Step Forward/Back, timeline scrubber, speed multipliers (0.5x, 1x, 2x, 4x), loop toggle.
   - Dual-mode comparator: Supports continuous animation across survey passes and 500 ms reference-to-current blinking.
   - Active frame telemetry card: Observation ID, UTC timestamp, MJD, Detector Array / Release, effective LVF wavelength $\lambda_{\text{eff}}$, and data quality status.
   - 1-click preset shortcuts for all 5 required NASA validation targets.
   - Metadata export: "Download Observation Metadata" button generates structured JSON observation series.

2. **Archive Discovery & Time-Series Engine (`backend/app/services/spherex_discovery.py`)**:
   - Multi-release discovery querying DR1 (`spherex_dr1`) and QR3 (`spherex_qr3`) independently via IPAC Simple Image Access (SIA).
   - Disk query caching in `data/spherex/cache/queries/` with SHA-256 spatial query keys to guarantee rapid, deterministic responses.
   - Accurate WCS footprint intersection validation with SIP divergence guards (pre-filtering by angular distance $\le 3.0^\circ$ from pointing center).
   - Exact per-pixel linear variable filter wavelength evaluation ($\lambda_{\text{eff}}$ in microns) using `LVFWavelengthModel`.

3. **Five-Target Scientific Validation Suite (`backend/app/astronomy/m6_target_validation.py`)**:
   - Astrometric proper motion propagation: Propagates catalog coordinates from literature epoch (Gaia DR3 J2016.0, Luhman J2010.0, SIMBAD J2000.0) to SPHEREx nominal mission midpoint (2025.8).
   - Target physical modeling:
     - **Barnard's Star:** Highest proper motion star (10.37"/yr, displacement 101.5" = 16.4 SPHEREx pixels over 9.8 yr).
     - **Epsilon Indi B:** T-dwarf binary (separation 0.73"); explicitly flagged as spatially unresolved by SPHEREx's 6.2" PSF.
     - **WISE 0855:** Coldest known brown dwarf (~250 K); identified in local Level-2 MEF FITS `level2_2025W44` at pixel (176.16, 266.04).
     - **RW Aurigae:** Classical T Tauri variable; dust occultation analysis.
     - **R Draconis:** Mira pulsating giant ($P = 245.6$ d); stationary flux variability.
   - Honest scientific reporting: Regions with $<2$ usable observations are strictly classified as `INSUFFICIENT_SPHEREx_TEMPORAL_COVERAGE` without artificial data fabrication.

4. **Mandatory Non-Discovery Disclaimer Preservation**:
   All candidates, time-series views, and export files enforce the scientific non-discovery disclaimer:
   > **NOTICE:** Observed Data | Processed Images | Synthetic Test Data | Change Candidates — NOT SCIENTIFICALLY CONFIRMED. Unverified candidates are not astronomical discoveries.

