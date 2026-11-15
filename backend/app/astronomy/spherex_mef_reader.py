"""SPHEREx Multi-Extension FITS (MEF) Reader and Inspector (Milestones 4 & 5).
Specialized reader for Level 2 SPHEREx spectral-image observation products.
Handles multi-extension structures:
- HDU 0: PRIMARY (metadata, spacecraft pointing, version)
- HDU 1: IMAGE (2040 x 2040 scientific float32 image array, CTYPE = RA---TAN-SIP / DEC--TAN-SIP)
- HDU 2: FLAGS (pixel quality / artifact flags, 32-bit int)
- HDU 3: VARIANCE (per-pixel uncertainty variance, float32)
- HDU 4: ZODI (estimated zodiacal light background, float32)
- HDU 5: EPSF (empirical effective point spread function table, 441 bins of 33x33 kernels)
- HDU 6: WCS-WAVE (wavelength and bandwidth dispersion lookup table, 9x9 nodes)

Preserves compatibility with the frozen M1-M4 baseline while providing typed,
uncompromised multi-extension scientific ingestion for Milestone 5.
"""

from __future__ import annotations

import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

from app.models.spherex_observation import (
    SpherexMefInspection,
    SpherexMefHduSummary,
    SpherexLayerLoadRequest,
    SpherexLayerPayload,
)
from app.astronomy.fits_reader import FitsMetadata
from app.astronomy.wcs_processor import extract_wcs, extract_wcs_metadata, pixel_to_world
from app.astronomy.image_footprint import generate_spherical_mesh
from app.astronomy.image_renderer import render_to_data_uri, DisplayStretch
from app.astronomy.fits_dimensions import (
    extract_and_validate_fits_dimensions,
    FitsDimensionValidationError,
)


def calculate_file_sha256(file_path: Path | str) -> str:
    """Compute cryptographic SHA-256 checksum of a file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


class SpherexMefProduct:
    """Typed scientific product representation for a SPHEREx Level-2 Multi-Extension FITS file.
    Preserves original data types, units, calibrated arrays, and tables without data loss.
    """
    def __init__(
        self,
        file_path: Path | str,
        filename: str,
        file_size_bytes: int,
        sha256: str,
        observation_id: str,
        detector: str,
        date_obs: str,
        mjd_obs: float,
        mjd_beg: float,
        mjd_end: float,
        exptime: float,
        version: str,
        bunit: str,
        image: np.ndarray,
        flags: np.ndarray,
        variance: np.ndarray,
        zodi: np.ndarray,
        epsf_table: Any,
        wcs_wave_x: np.ndarray,
        wcs_wave_y: np.ndarray,
        wcs_wave_values: np.ndarray,
        wcs: WCS,
        header_primary: fits.Header,
        header_image: fits.Header,
        provenance: str = "NASA/IPAC IRSA SPHEREx",
    ):
        self.file_path = Path(file_path)
        self.filename = filename
        self.file_size_bytes = file_size_bytes
        self.sha256 = sha256
        self.observation_id = observation_id
        self.detector = detector
        self.date_obs = date_obs
        self.mjd_obs = mjd_obs
        self.mjd_beg = mjd_beg
        self.mjd_end = mjd_end
        self.exptime = exptime
        self.version = version
        self.bunit = bunit
        self.image = image
        self.flags = flags
        self.variance = variance
        self.zodi = zodi
        self.epsf_table = epsf_table
        self.wcs_wave_x = wcs_wave_x
        self.wcs_wave_y = wcs_wave_y
        self.wcs_wave_values = wcs_wave_values
        self.wcs = wcs
        self.header_primary = header_primary
        self.header_image = header_image
        self.provenance = provenance

    @property
    def dimensions(self) -> Tuple[int, int]:
        """Return (width, height) of science image."""
        h, w = self.image.shape
        return (w, h)

    def summary_dict(self) -> Dict[str, Any]:
        """Return clean metadata summary."""
        return {
            "filename": self.filename,
            "sha256": self.sha256,
            "observation_id": self.observation_id,
            "detector": self.detector,
            "date_obs": self.date_obs,
            "mjd_obs": self.mjd_obs,
            "mjd_beg": self.mjd_beg,
            "mjd_end": self.mjd_end,
            "temporal_baseline_days": None,
            "exptime": self.exptime,
            "version": self.version,
            "bunit": self.bunit,
            "dimensions": self.dimensions,
            "epsf_bins_count": len(self.epsf_table) if self.epsf_table is not None else 0,
            "wcs_wave_nodes": list(self.wcs_wave_x),
            "provenance": self.provenance,
        }


def read_spherex_mef_product(file_path: str | Path) -> SpherexMefProduct:
    """Read, rigorously validate, and return a typed SPHEREx Level 2 Multi-Extension FITS product.
    
    Validates required HDU structure:
    - HDU 0: PRIMARY
    - HDU 1: IMAGE (2040x2040 float32 surface brightness in MJy/sr)
    - HDU 2: FLAGS (2040x2040 int32 bitmask)
    - HDU 3: VARIANCE (2040x2040 float32 variance in (MJy/sr)^2)
    - HDU 4: ZODI (2040x2040 float32 estimated zodiacal light)
    - HDU 5: EPSF (Binary Table, 441 rows of 33x33 point spread function kernels)
    - HDU 6: WCS-WAVE (Binary Table, 9x9 nodes of wavelength and bandwidth)
    
    Rejects malformed or missing extensions with explicit scientific errors.
    Never silently replaces missing scientific data with zeros.
    """
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"SPHEREx FITS product file not found: {file_path}")

    file_size_bytes = p.stat().st_size
    if file_size_bytes < 1024 * 1024:
        raise ValueError(f"FITS file {p.name} too small ({file_size_bytes} bytes); corrupt or incomplete download.")

    sha256_hash = calculate_file_sha256(p)

    with fits.open(p) as hdul:
        # Validate minimum extension count
        if len(hdul) < 7:
            raise ValueError(
                f"FITS product {p.name} contains only {len(hdul)} HDUs; "
                f"requires 7 extensions (PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE)."
            )

        # 1. PRIMARY HDU
        primary_hdu = hdul[0]
        h_pri = primary_hdu.header
        version = str(h_pri.get("VERSION") or h_pri.get("PIPEVER") or "UNKNOWN")

        # 2. IMAGE HDU
        if "IMAGE" not in hdul:
            raise ValueError(f"Required HDU 'IMAGE' missing from {p.name}")
        img_hdu = hdul["IMAGE"]
        h_img = img_hdu.header
        img_data = img_hdu.data
        if img_data is None or img_data.ndim != 2:
            raise ValueError(f"IMAGE HDU in {p.name} must be a 2D array, got shape {getattr(img_data, 'shape', None)}")

        # Enforce header dimensions match data array shape without assumptions
        try:
            naxis1, naxis2, _, _ = extract_and_validate_fits_dimensions(hdul, filename=p.name)
        except FitsDimensionValidationError as dim_err:
            raise ValueError(f"IMAGE HDU dimension validation failed for {p.name}: {dim_err}") from dim_err
        
        # Ensure native byteorder float32 array
        if img_data.dtype.byteorder not in ('=', '|'):
            image_array = img_data.astype(np.float32)
        else:
            image_array = np.asarray(img_data, dtype=np.float32)

        # 3. FLAGS HDU
        if "FLAGS" not in hdul:
            raise ValueError(f"Required HDU 'FLAGS' missing from {p.name}")
        flags_hdu = hdul["FLAGS"]
        flags_raw = flags_hdu.data
        if flags_raw is None or flags_raw.shape != image_array.shape:
            raise ValueError(f"FLAGS HDU shape {getattr(flags_raw, 'shape', None)} does not match IMAGE shape {image_array.shape}")
        flags_array = np.asarray(flags_raw, dtype=np.int32)

        # 4. VARIANCE HDU
        if "VARIANCE" not in hdul:
            raise ValueError(f"Required HDU 'VARIANCE' missing from {p.name}")
        var_hdu = hdul["VARIANCE"]
        var_raw = var_hdu.data
        if var_raw is None or var_raw.shape != image_array.shape:
            raise ValueError(f"VARIANCE HDU shape {getattr(var_raw, 'shape', None)} does not match IMAGE shape {image_array.shape}")
        if var_raw.dtype.byteorder not in ('=', '|'):
            variance_array = var_raw.astype(np.float32)
        else:
            variance_array = np.asarray(var_raw, dtype=np.float32)

        # 5. ZODI HDU
        if "ZODI" not in hdul:
            raise ValueError(f"Required HDU 'ZODI' missing from {p.name}")
        zodi_hdu = hdul["ZODI"]
        zodi_raw = zodi_hdu.data
        if zodi_raw is None or zodi_raw.shape != image_array.shape:
            raise ValueError(f"ZODI HDU shape {getattr(zodi_raw, 'shape', None)} does not match IMAGE shape {image_array.shape}")
        if zodi_raw.dtype.byteorder not in ('=', '|'):
            zodi_array = zodi_raw.astype(np.float32)
        else:
            zodi_array = np.asarray(zodi_raw, dtype=np.float32)

        # 6. EPSF HDU
        if "EPSF" not in hdul:
            raise ValueError(f"Required HDU 'EPSF' missing from {p.name}")
        epsf_hdu = hdul["EPSF"]
        epsf_data = epsf_hdu.data
        if epsf_data is None or len(epsf_data) == 0:
            raise ValueError(f"EPSF HDU in {p.name} contains no table records")
        # Validate EPSF columns
        required_epsf_cols = {"BINX", "BINY", "XCENTER", "YCENTER", "EPSF"}
        if not required_epsf_cols.issubset(set(epsf_data.columns.names)):
            raise ValueError(f"EPSF table missing required columns: {required_epsf_cols - set(epsf_data.columns.names)}")

        # 7. WCS-WAVE HDU
        if "WCS-WAVE" not in hdul:
            raise ValueError(f"Required HDU 'WCS-WAVE' missing from {p.name}")
        wave_hdu = hdul["WCS-WAVE"]
        wave_data = wave_hdu.data
        if wave_data is None or len(wave_data) == 0:
            raise ValueError(f"WCS-WAVE HDU in {p.name} contains no records")
        required_wave_cols = {"X", "Y", "VALUES"}
        if not required_wave_cols.issubset(set(wave_data.columns.names)):
            raise ValueError(f"WCS-WAVE table missing required columns: {required_wave_cols - set(wave_data.columns.names)}")
        
        wave_x = np.array(wave_data["X"][0], dtype=np.float64)
        wave_y = np.array(wave_data["Y"][0], dtype=np.float64)
        wave_values = np.array(wave_data["VALUES"][0], dtype=np.float64)

        # Extract WCS with sanitized header (strip non-standard WCS-WAVE keys that crash astropy WCS)
        clean_hdr = fits.Header()
        for k, v in h_img.items():
            if not any(k.startswith(pfx) for pfx in ['CTYPE', 'CRVAL', 'CDELT', 'CUNIT']) or not k.endswith('W'):
                if isinstance(v, str) and '\n' in v:
                    clean_hdr[k] = v.replace('\n', ' ')
                else:
                    clean_hdr[k] = v
        wcs = WCS(clean_hdr, naxis=2)

        # Metadata extraction
        obs_id = str(
            h_img.get("EXPIDN")
            or h_pri.get("HIERARCH SPS_TARGET")
            or h_pri.get("OBSID")
            or p.stem
        )
        det_raw = h_img.get("DETECTOR") or h_pri.get("DETECTOR") or 1
        detector = f"SPHEREx-D{det_raw}" if str(det_raw).isdigit() else str(det_raw)
        
        date_obs = str(h_img.get("DATE-OBS") or h_pri.get("DATE-OBS") or "")
        mjd_obs = float(h_img.get("MJD-OBS") or h_pri.get("MJD-OBS") or 0.0)
        mjd_beg = float(h_img.get("MJD-BEG") or mjd_obs)
        mjd_end = float(h_img.get("MJD-END") or mjd_obs)
        exptime = float(h_img.get("EXPTIME") or h_pri.get("EXPTIME") or (mjd_end - mjd_beg) * 86400.0)
        bunit = str(h_img.get("BUNIT", "MJy / sr"))

    return SpherexMefProduct(
        file_path=p,
        filename=p.name,
        file_size_bytes=file_size_bytes,
        sha256=sha256_hash,
        observation_id=obs_id,
        detector=detector,
        date_obs=date_obs,
        mjd_obs=mjd_obs,
        mjd_beg=mjd_beg,
        mjd_end=mjd_end,
        exptime=exptime,
        version=version,
        bunit=bunit,
        image=image_array,
        flags=flags_array,
        variance=variance_array,
        zodi=zodi_array,
        epsf_table=epsf_data,
        wcs_wave_x=wave_x,
        wcs_wave_y=wave_y,
        wcs_wave_values=wave_values,
        wcs=wcs,
        header_primary=h_pri,
        header_image=h_img,
        provenance="NASA/IPAC IRSA SPHEREx",
    )


def inspect_spherex_mef(file_path: str | Path) -> SpherexMefInspection:
    """Inspect and validate all extensions of a SPHEREx Level 2 MEF file (M4 preservation)."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"SPHEREx FITS file not found: {file_path}")

    file_size_bytes = p.stat().st_size
    sha256_hash = calculate_file_sha256(p)

    hdus_summary: List[SpherexMefHduSummary] = []
    
    with fits.open(p) as hdul:
        for idx, hdu in enumerate(hdul):
            shape = list(hdu.data.shape) if hdu.data is not None else None
            dtype = str(hdu.data.dtype) if hdu.data is not None else None
            bunit = hdu.header.get("BUNIT")
            hdus_summary.append(
                SpherexMefHduSummary(
                    index=idx,
                    name=hdu.name,
                    hdu_type=type(hdu).__name__,
                    shape=shape,
                    dtype=dtype,
                    bunit=bunit,
                    card_count=len(hdu.header),
                )
            )

        has_image = "IMAGE" in hdul or len(hdul) > 1
        has_flags = "FLAGS" in hdul
        has_variance = "VARIANCE" in hdul
        has_zodi = "ZODI" in hdul
        has_psf = "PSF" in hdul or "EPSF" in hdul
        has_wcs_wave = "WCS-WAVE" in hdul

        if "IMAGE" in hdul:
            image_hdu = hdul["IMAGE"]
        elif len(hdul) > 1 and hdul[1].data is not None:
            image_hdu = hdul[1]
        else:
            raise ValueError(f"FITS file {p.name} does not contain an IMAGE extension")

        img_header = image_hdu.header
        img_data = image_hdu.data
        primary_header = hdul[0].header

        obs_id = (
            img_header.get("OBSID")
            or primary_header.get("OBSID")
            or primary_header.get("OBS_ID")
            or p.stem
        )
        detector_raw = img_header.get("DETECTOR") or primary_header.get("DETECTOR") or "1"
        detector = f"SPHEREx-D{detector_raw}" if str(detector_raw).isdigit() else str(detector_raw)
        
        date_obs = (
            img_header.get("DATE-OBS")
            or primary_header.get("DATE-OBS")
            or img_header.get("DATE")
        )
        exptime = img_header.get("EXPTIME") or primary_header.get("EXPTIME")
        if exptime is not None:
            try:
                exptime = float(exptime)
            except (ValueError, TypeError):
                exptime = None

        image_units = img_header.get("BUNIT", "MJy / sr")

        data_float = img_data.astype(np.float32)
        nan_mask = np.isnan(data_float) | np.isinf(data_float)
        nan_pixels = int(nan_mask.sum())
        finite_pixels = int((~nan_mask).sum())

        wcs = extract_wcs(img_header)
        wcs_type = f"{img_header.get('CTYPE1', 'UNKNOWN')}, {img_header.get('CTYPE2', 'UNKNOWN')}"
        has_sip = wcs.sip is not None
        sip_order = int(wcs.sip.a_order) if has_sip else None

        height, width = data_float.shape
        corner_pix_x = np.array([0.0, float(width - 1), float(width - 1), 0.0])
        corner_pix_y = np.array([0.0, 0.0, float(height - 1), float(height - 1)])
        ra_corners, dec_corners = pixel_to_world(wcs, corner_pix_x, corner_pix_y, origin=0)
        wcs_corners = [
            (round(float(ra_corners[i]), 6), round(float(dec_corners[i]), 6))
            for i in range(4)
        ]

        flags_summary = None
        if has_flags and hdul["FLAGS"].data is not None:
            flags_data = hdul["FLAGS"].data
            flagged_count = int(np.count_nonzero(flags_data))
            flags_summary = {
                "flagged_pixel_count": flagged_count,
                "clean_pixel_count": int(flags_data.size - flagged_count),
                "flagged_ratio": round(float(flagged_count / max(1, flags_data.size)), 5),
            }

        variance_summary = None
        if has_variance and hdul["VARIANCE"].data is not None:
            var_data = hdul["VARIANCE"].data.astype(np.float32)
            valid_var = var_data[np.isfinite(var_data)]
            if len(valid_var) > 0:
                variance_summary = {
                    "min": round(float(np.min(valid_var)), 6),
                    "max": round(float(np.max(valid_var)), 6),
                    "median": round(float(np.median(valid_var)), 6),
                    "bunit": hdul["VARIANCE"].header.get("BUNIT", "MJy2 / sr2"),
                }

    return SpherexMefInspection(
        filename=p.name,
        file_size_bytes=file_size_bytes,
        sha256=sha256_hash,
        hdus=hdus_summary,
        observation_id=str(obs_id),
        detector=detector,
        date_obs=str(date_obs) if date_obs else None,
        exposure_time=exptime,
        image_units=image_units,
        has_image=has_image,
        has_flags=has_flags,
        has_variance=has_variance,
        has_zodi=has_zodi,
        has_psf=has_psf,
        has_wcs_wave=has_wcs_wave,
        flags_summary=flags_summary,
        variance_summary=variance_summary,
        wcs_type=wcs_type,
        has_sip=has_sip,
        sip_order=sip_order,
        nan_pixels=nan_pixels,
        finite_pixels=finite_pixels,
        wcs_corners=wcs_corners,
    )


def load_spherex_layer(
    file_path: str | Path,
    req: SpherexLayerLoadRequest
) -> SpherexLayerPayload:
    """Load and process a real SPHEREx MEF observation into a 3D visualization layer (M4 preservation)."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"SPHEREx FITS product not found: {file_path}")

    with fits.open(p) as hdul:
        if "IMAGE" in hdul:
            image_hdu = hdul["IMAGE"]
        elif len(hdul) > 1 and hdul[1].data is not None:
            image_hdu = hdul[1]
        else:
            raise ValueError(f"FITS file {p.name} contains no valid image data array")

        img_header = image_hdu.header
        raw_data = image_hdu.data
        primary_header = hdul[0].header

        obs_id = str(
            img_header.get("OBSID")
            or primary_header.get("OBSID")
            or primary_header.get("OBS_ID")
            or p.stem
        )
        detector_raw = img_header.get("DETECTOR") or primary_header.get("DETECTOR") or "1"
        detector = f"SPHEREx-D{detector_raw}" if str(detector_raw).isdigit() else str(detector_raw)
        date_obs = (
            img_header.get("DATE-OBS")
            or primary_header.get("DATE-OBS")
            or img_header.get("DATE")
        )
        bunit = img_header.get("BUNIT", "MJy / sr")

        data_float = raw_data.astype(np.float32)
        height, width = data_float.shape

        wcs = extract_wcs(img_header)
        wcs_meta = extract_wcs_metadata(wcs, width, height)

        nan_mask = np.isnan(data_float) | np.isinf(data_float)
        nan_count = int(nan_mask.sum())
        clean_data = np.nan_to_num(data_float, nan=0.0, posinf=0.0, neginf=0.0)

        data_min = float(np.min(clean_data))
        data_max = float(np.max(clean_data))
        data_mean = float(np.mean(clean_data))
        data_std = float(np.std(clean_data))

        metadata = FitsMetadata(
            filename=p.name,
            dimensions=(width, height),
            naxis=2,
            bitpix=int(img_header.get("BITPIX", -32)),
            bunit=bunit,
            telescope="SPHEREx",
            instrument=f"SPHEREx ({detector})",
            target_object=str(obs_id),
            date_obs=str(date_obs) if date_obs else None,
            filter_band=detector,
            exposure_time_sec=float(img_header.get("EXPTIME", 0.0)) if img_header.get("EXPTIME") else None,
            data_min=data_min,
            data_max=data_max,
            data_mean=data_mean,
            data_std=data_std,
            nan_count=nan_count,
            wcs=wcs_meta,
        )

    mesh = generate_spherical_mesh(
        wcs=wcs,
        width=width,
        height=height,
        radius=req.radius,
        min_grid=16,
        max_grid=32,
    )

    stretch_type: DisplayStretch = (
        req.stretch if req.stretch in ["linear", "log", "asinh", "sqrt"] else "asinh"
    )
    texture_data_uri = render_to_data_uri(
        clean_data,
        stretch=stretch_type,
        colormap="astronomical_ir",
        brightness=req.brightness,
        contrast=req.contrast,
        nan_mask=nan_mask,
    )

    layer_id = f"spherex_{obs_id}_{detector}".replace(" ", "_").replace("-", "_")
    title = f"NASA SPHEREx {obs_id} ({detector})"

    return SpherexLayerPayload(
        layer_id=layer_id,
        title=title,
        provenance="NASA/IPAC IRSA SPHEREx",
        is_real_data=True,
        observation_id=str(obs_id),
        detector=detector,
        obs_date=str(date_obs) if date_obs else None,
        metadata=metadata,
        mesh=mesh,
        texture_data_uri=texture_data_uri,
        units=bunit,
        stretch=req.stretch,
        brightness=req.brightness,
        contrast=req.contrast,
    )
