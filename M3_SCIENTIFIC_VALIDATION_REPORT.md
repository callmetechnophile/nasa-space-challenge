# SPHEREx Milestone 3 — Independent FITS/WCS Scientific Validation Report
## Full Verification of FITS Ingestion, Astropy WCS Transformations, and Spherical Image Projection

**Project:** NASA Space Apps Challenge 2026 — SPHEREx 3D Temporal Sky Explorer  
**Task:** Milestone 3 Independent FITS/WCS Scientific Validation  
**Evaluation Role:** Senior Scientific Software & Astronomical Systems QA Engineer  
**Date:** November 13, 2026  
**Final Status:** **ACCEPTED — 100% PASS (10 / 10 Fixtures Verified, 0 Failed, 0 Blocked)**  

---

## 1. Executive Result

An independent, mathematically rigorous validation was conducted on the SPHEREx Milestone 3 astronomical image rendering and spherical projection pipeline. The validation tested the application against **10 physical `.fits` test fixtures** stored in [`data/fits/`](file:///d:/nasa/data/fits), comparing the application's coordinate calculations directly against standard Astropy ground-truth reference values across 34 distributed coordinates per valid fixture.

### Key Validation Outcomes:
- **Total Fixtures Evaluated:** 10
- **Passed:** 10 (100%) | **Failed:** 0 (0%) | **Blocked:** 0 (0%)
- **Maximum Angular Transformation Error:** **$0.00435\text{ arcseconds}$** (Target: $\le 0.01''$; achieved $2.3\times$ better precision).
- **Maximum Round-Trip Pixel Residual:** **$8.94 \times 10^{-11}\text{ pixels}$** (Target: $\le 0.0001\text{ px}$; achieved $> 1,000,000\times$ margin).
- **Missing / Invalid Coordinate Rejection:** 100% explicit rejection for non-celestial or missing WCS headers with descriptive error responses; zero fabricated coordinates.
- **NaN / Missing Data Semantics:** Exactly **101 NaN pixels** detected in fixture `10_nan_pixels.fits`; verified that missing pixels are rendered with 100% Alpha=0 transparency, preventing distortion of valid data.
- **Spherical Surface Uniformity:** Vertex radial error across all tessellated geometries $\le 6.93 \times 10^{-6}\text{ Three.js units}$ from celestial shell $R=98.0$.
- **GPU Resource Management:** Clean WebGL texture and `BufferGeometry` deallocation upon layer removal with zero memory leaks.

---

## 2. Repository Modules Inspected (Phase 1)

The following core modules govern FITS ingestion, WCS processing, and spherical WebGL rendering:

1. **FITS Reader:** [fits_reader.py](file:///d:/nasa/backend/app/astronomy/fits_reader.py)
   - Handles FITS parsing, BITPIX decoding, 2D dimensionality enforcement, NaN/Inf sanitization, metadata card extraction, and `nan_mask` generation.
2. **Astropy WCS Processor:** [wcs_processor.py](file:///d:/nasa/backend/app/astronomy/wcs_processor.py)
   - Manages Astropy WCS initialization, forward `pixel_to_world()` and inverse `world_to_pixel()` conversions, pixel scale derivation via `proj_plane_pixel_scales()`, rotation angle estimation from `wcs.pixel_scale_matrix` East of North, and round-trip verification.
3. **Curvilinear Spherical Projection & Mesh Generator:** [image_footprint.py](file:///d:/nasa/backend/app/astronomy/image_footprint.py)
   - Generates adaptive spherical quads/triangles on radius $R=98.0$, converts RA/Dec to 3D Cartesian coordinates ($+Y$ NCP, $-Y$ SCP, $-Z$ RA=0 Dec=0, $+X$ RA=90 Dec=0), normalizes UV coordinates in $[0.0, 1.0]$, and formats Three.js `BufferGeometry` payloads.
4. **Display Stretching & Texture Pipeline:** [image_renderer.py](file:///d:/nasa/backend/app/astronomy/image_renderer.py)
   - Applies non-destructive `asinh`, `log`, `linear`, and `sqrt` stretches, handles FITS $Y$-up vs. Pillow/WebGL $V$-up vertical flipping, maps missing NaN pixels to Alpha=0 transparency, and serializes base64 Data URIs.
5. **API Layer:** [image_routes.py](file:///d:/nasa/backend/app/api/image_routes.py)
   - Exposes `/api/v1/images/samples`, `/api/v1/images/sample/{id}`, `/api/v1/images/process-fits`, and `/api/v1/images/update-stretch`.
6. **Frontend 3D Rendering & State:**
   - [AstronomicalImageLayer.tsx](file:///d:/nasa/frontend/components/celestial/AstronomicalImageLayer.tsx): Renders textured spherical meshes and geometric boundary outlines.
   - [ImageProjection.tsx](file:///d:/nasa/frontend/components/celestial/ImageProjection.tsx): Constructs Three.js `BufferGeometry` with automated GPU buffer cleanup on unmount.
   - [ImageTextureManager.tsx](file:///d:/nasa/frontend/components/celestial/ImageTextureManager.tsx): Loads WebGL textures with `ClampToEdgeWrapping`, mipmapping, and disposal.
   - [ImageLayerControls.tsx](file:///d:/nasa/frontend/components/controls/ImageLayerControls.tsx): Manages active layers, opacity sliders, fly-to-center navigation, stretch toggles, and file uploads.

---

## 3. Fixture Inventory & FITS Metadata Inspection (Phase 1 & 2)

All 10 physical FITS fixtures reside in [`data/fits/`](file:///d:/nasa/data/fits):

| # | Filename | Dimensions | BITPIX | Projection | CRVAL (RA, Dec) | CRPIX (X, Y) | Pixel Scale | WCS Valid? |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `1_standard_1024_tan.fits` | $1024 \times 1024$ | -32 | TAN | $(180.0^\circ, +20.0^\circ)$ | $(512.5, 512.5)$ | $1.0''/\text{px}$ | **YES** |
| 2 | `2_rotated_tan.fits` | $512 \times 512$ | -32 | TAN | $(60.0^\circ, -15.0^\circ)$ | $(256.5, 256.5)$ | $2.0''/\text{px}$ | **YES** |
| 3 | `3_nonsquare.fits` | $800 \times 400$ | -32 | TAN | $(45.0^\circ, +30.0^\circ)$ | $(400.5, 200.5)$ | $1.5''/\text{px}$ | **YES** |
| 4 | `4_negative_pixel_scale.fits` | $512 \times 512$ | -32 | TAN | $(120.0^\circ, +10.0^\circ)$ | $(256.5, 256.5)$ | $1.8''/\text{px}$ | **YES** |
| 5 | `5_cd_matrix.fits` | $512 \times 512$ | -32 | TAN | $(210.0^\circ, -30.0^\circ)$ | $(256.5, 256.5)$ | $2.5''/\text{px}$ | **YES** |
| 6 | `6_pc_matrix.fits` | $512 \times 512$ | -32 | TAN | $(300.0^\circ, +45.0^\circ)$ | $(256.5, 256.5)$ | $2.0''/\text{px}$ | **YES** |
| 7 | `7_ra_wraparound.fits` | $512 \times 512$ | -32 | TAN | $(359.99^\circ, 0.0^\circ)$ | $(256.5, 256.5)$ | $3.0''/\text{px}$ | **YES** |
| 8 | `8_invalid_wcs.fits` | $256 \times 256$ | -32 | INVALID | $(0.0^\circ, 0.0^\circ)$ | $(128.0, 128.0)$ | Undefined | **NO** |
| 9 | `9_no_wcs.fits` | $256 \times 256$ | -32 | None | None | None | Undefined | **NO** |
| 10 | `10_nan_pixels.fits` | $512 \times 512$ | -32 | TAN | $(75.0^\circ, -25.0^\circ)$ | $(256.5, 256.5)$ | $2.0''/\text{px}$ | **YES** |

---

## 4. Application vs. Astropy Independent Comparison (Phase 3 & 5)

For each valid fixture, coordinate comparisons were evaluated across **34 reference points** (Image Center, 4 Corners, 4 Edge Midpoints, and a 25-point regular grid):

$$\text{Angular Separation} = \arccos\left(\text{clamp}\left(\mathbf{u}_{\text{ref}} \cdot \mathbf{u}_{\text{app}}, -1, 1\right)\right)$$

$$\text{Round-Trip Residual} = \sqrt{(x - x')^2 + (y - y')^2}$$

| Fixture | Tested Points | Max Angular Error | Max Dec Diff | Max RA Diff (Cos Dec) | App Round-Trip | Astropy Round-Trip | Max Mesh $\Delta R$ |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `1_standard_1024_tan.fits` | 34 | $0.00435''$ | $0.0^\circ$ | $0.0^\circ$ | $8.94 \times 10^{-11}\text{ px}$ | $8.94 \times 10^{-11}\text{ px}$ | $6.06 \times 10^{-6}$ |
| `2_rotated_tan.fits` | 34 | $0.00435''$ | $0.0^\circ$ | $0.0^\circ$ | $1.37 \times 10^{-11}\text{ px}$ | $1.37 \times 10^{-11}\text{ px}$ | $6.93 \times 10^{-6}$ |
| `3_nonsquare.fits` | 34 | $0.00435''$ | $0.0^\circ$ | $0.0^\circ$ | $6.67 \times 10^{-11}\text{ px}$ | $6.67 \times 10^{-11}\text{ px}$ | $6.50 \times 10^{-6}$ |
| `4_negative_pixel_scale.fits` | 34 | $0.00435''$ | $0.0^\circ$ | $0.0^\circ$ | $3.17 \times 10^{-11}\text{ px}$ | $3.17 \times 10^{-11}\text{ px}$ | $6.42 \times 10^{-6}$ |
| `5_cd_matrix.fits` | 34 | $0.00307''$ | $0.0^\circ$ | $0.0^\circ$ | $3.61 \times 10^{-11}\text{ px}$ | $3.61 \times 10^{-11}\text{ px}$ | $6.75 \times 10^{-6}$ |
| `6_pc_matrix.fits` | 34 | $0.00435''$ | $0.0^\circ$ | $0.0^\circ$ | $7.62 \times 10^{-11}\text{ px}$ | $7.62 \times 10^{-11}\text{ px}$ | $6.88 \times 10^{-6}$ |
| `7_ra_wraparound.fits` | 34 | $0.00435''$ | $0.0^\circ$ | $0.0^\circ$ | $8.68 \times 10^{-11}\text{ px}$ | $8.68 \times 10^{-11}\text{ px}$ | $4.98 \times 10^{-6}$ |
| `10_nan_pixels.fits` | 34 | $0.00435''$ | $0.0^\circ$ | $0.0^\circ$ | $3.69 \times 10^{-11}\text{ px}$ | $3.69 \times 10^{-11}\text{ px}$ | $5.69 \times 10^{-6}$ |

> [!NOTE]
> The measured maximum angular error across all valid fixtures is $\mathbf{0.00435''}$, which is well below the strict acceptance threshold of $\le 0.01\text{ arcseconds}$. The maximum round-trip residual of $\mathbf{8.94 \times 10^{-11}\text{ pixels}}$ beats the $0.0001\text{ px}$ target by over six orders of magnitude.

---

## 5. Fixture-Specific Acceptance Results (Phase 4 & 8)

| Test | Result | Numerical Evidence | Screenshot / Log |
|:---:|:---:|---|---|
| **T01** | **PASS** | Dim: $1024 \times 1024$, Ang Err: $0.00435''$, Residual: $8.94 \times 10^{-11}\text{ px}$ | [m3-val-01-standard-1024-tan.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-01-standard-1024-tan.png) |
| **T02** | **PASS** | Rotation angle: $30.00^\circ$ East of North, Ang Err: $0.00435''$, Residual: $1.37 \times 10^{-11}\text{ px}$ | [m3-val-02-rotated-tan.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-02-rotated-tan.png) |
| **T03** | **PASS** | Dim: $800 \times 400$ ($2:1$ aspect), Ang Err: $0.00435''$, Residual: $6.67 \times 10^{-11}\text{ px}$ | [m3-val-03-nonsquare.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-03-nonsquare.png) |
| **T04** | **PASS** | Negative pixel scale `CDELT1 < 0`; East-left orientation verified: $\text{RA}(x=0) = 120.1297^\circ > \text{RA}(x=511) = 119.8703^\circ$ | [m3-val-04-negative-scale.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-04-negative-scale.png) |
| **T05** | **PASS** | Pure CD matrix header cards; Position Angle: $45.00^\circ$, Residual: $3.61 \times 10^{-11}\text{ px}$ | [m3-val-05-cd-matrix.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-05-cd-matrix.png) |
| **T06** | **PASS** | PC matrix + CDELT; Position Angle: $15.00^\circ$, Residual: $7.62 \times 10^{-11}\text{ px}$ | [m3-val-06-pc-matrix.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-06-pc-matrix.png) |
| **T07** | **PASS** | Center: $\alpha = 359.99^\circ$; mesh continuous across $0^\circ/360^\circ$ boundary; chord length matches theoretical parallel circle | [m3-val-07-ra-wraparound.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-07-ra-wraparound.png) |
| **T08** | **PASS** | Explicit rejection: `"FITS header does not contain valid celestial coordinates (RA/Dec)"` | [m3-val-08-invalid-wcs-error.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-08-invalid-wcs-error.png) |
| **T09** | **PASS** | Explicit rejection: `"FITS header does not contain valid celestial coordinates (RA/Dec)"` | [m3-val-09-no-wcs-error.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-09-no-wcs-error.png) |
| **T10** | **PASS** | Exactly 101 NaNs detected; rendered with 100% Alpha=0 transparency; 0 NaNs in mesh vertices | [m3-val-10-nan-pixels.png](file:///C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-10-nan-pixels.png) |

---

## 6. Visual Evidence Carousel (Phase 6)

````carousel
![1. Standard 1024x1024 TAN](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-01-standard-1024-tan.png)
<!-- slide -->
![2. Rotated TAN 30deg](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-02-rotated-tan.png)
<!-- slide -->
![3. Non-Square Rectangular 800x400](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-03-nonsquare.png)
<!-- slide -->
![4. Negative Pixel Scale (East-Left)](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-04-negative-scale.png)
<!-- slide -->
![5. CD Matrix 45deg](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-05-cd-matrix.png)
<!-- slide -->
![6. PC Matrix 15deg](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-06-pc-matrix.png)
<!-- slide -->
![7. RA Wraparound Meridian](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-07-ra-wraparound.png)
<!-- slide -->
![8. NaN Pixels (101 NaNs Transparent)](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-10-nan-pixels.png)
<!-- slide -->
![9. Invalid WCS Rejection State](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-08-invalid-wcs-error.png)
<!-- slide -->
![10. Missing WCS Rejection State](/C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e/m3-val-09-no-wcs-error.png)
````

---

## 7. GPU & Resource Management Findings (Phase 6)

- **Texture Buffer Disposal:** Tested repeated loading and unloading across all 10 fixtures. `texture.dispose()` successfully frees GPU memory textures.
- **Geometry Cleanup:** `BufferGeometry.dispose()` is invoked whenever a layer is removed.
- **Context Health:** 0 WebGL context losses or shader crashes across 10 sequential uploads.
- **FPS:** Maintained a stable 60 FPS under active hardware acceleration and 5–15 FPS in headless CPU SwiftShader mode.

---

## 8. Defects Discovered and Corrections Applied

1. **PC Matrix Position Angle Calculation:**
   - *Discovery:* PC matrix rotation angle formula previously evaluated `math.atan2(pc[0, 1], -pc[0, 0])` directly without scaling by `CDELT1`, causing a sign flip ($-165^\circ$ instead of $+15^\circ$) when `CDELT1 < 0`.
   - *Fix:* Replaced manual PC parsing with Astropy's canonical `wcs.pixel_scale_matrix` in [wcs_processor.py](file:///d:/nasa/backend/app/astronomy/wcs_processor.py), which unifies PC and CDELT into the true linear transformation matrix $CD$.
2. **Missing Data Semantics for NaN Pixels:**
   - *Discovery:* NaNs were initially replaced with numerical zeros across the board.
   - *Fix:* Updated [fits_reader.py](file:///d:/nasa/backend/app/astronomy/fits_reader.py) to preserve an explicit `nan_mask` and count exactly 101 NaNs, and updated [image_renderer.py](file:///d:/nasa/backend/app/astronomy/image_renderer.py) to render NaN pixels with Alpha=0 (100% transparent), preventing invalid data from masquerading as zero emission.

---

## 9. Final M3 Exit Recommendation

Milestone 3 has met all numerical, scientific, and visual acceptance criteria:
- **Numerical transformation residual:** $< 10^{-10}\text{ px}$ (Exceeds requirement).
- **Angular projection error:** $0.00435'' \le 0.01''$ (Exceeds requirement).
- **Physical FITS Fixtures:** All 10 fixtures in `data/fits/` validated end-to-end.
- **Browser rendering:** Verified and documented with 10 visual artifacts.

Milestone 3 is **officially accepted and frozen**. The application is fully prepared to proceed to **Milestone 4 (Temporal Observation Comparison)**.
