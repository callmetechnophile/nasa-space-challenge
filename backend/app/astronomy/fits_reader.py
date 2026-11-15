"""FITS Reader Module for SPHEREx 3D Sky Explorer.
Reads FITS files, validates 2D dimensionality, extracts primary HDU data,
header metadata, and observation attributes.
"""

from __future__ import annotations

import io
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from pydantic import BaseModel, Field

from astropy.io import fits
from astropy.wcs import WCS

from app.astronomy.wcs_processor import extract_wcs, extract_wcs_metadata, WcsMetadata


class FitsMetadata(BaseModel):
    """Metadata extracted from FITS primary header and data array."""
    filename: str = Field(..., description="Source filename or identifier")
    dimensions: Tuple[int, int] = Field(..., description="(width, height) in pixels")
    naxis: int = Field(2, description="Number of axes")
    bitpix: int = Field(..., description="FITS BITPIX data type indicator")
    bunit: str = Field("adu", description="Brightness units (e.g. adu, Jy/beam, MJy/sr)")
    telescope: Optional[str] = Field(None, description="TELESCOP header value")
    instrument: Optional[str] = Field(None, description="INSTRUME header value")
    target_object: Optional[str] = Field(None, description="OBJECT header value")
    date_obs: Optional[str] = Field(None, description="DATE-OBS header value")
    filter_band: Optional[str] = Field(None, description="FILTER header value")
    exposure_time_sec: Optional[float] = Field(None, description="EXPTIME header value")
    data_min: float = Field(..., description="Minimum pixel intensity value")
    data_max: float = Field(..., description="Maximum pixel intensity value")
    data_mean: float = Field(..., description="Mean pixel intensity value")
    data_std: float = Field(..., description="Standard deviation of pixel intensity values")
    nan_count: int = Field(0, description="Count of NaN/Inf invalid pixels detected")
    wcs: WcsMetadata = Field(..., description="Parsed WCS metadata")


class LoadedFitsProduct:
    """Holds parsed in-memory 2D numpy data array, Astropy WCS, metadata, and invalid pixel mask."""
    def __init__(
        self,
        data: np.ndarray,
        header: fits.Header,
        wcs: WCS,
        metadata: FitsMetadata,
        nan_mask: Optional[np.ndarray] = None
    ):
        self.data = data
        self.header = header
        self.wcs = wcs
        self.metadata = metadata
        self.nan_mask = nan_mask if nan_mask is not None else np.zeros(data.shape, dtype=bool)


def read_fits_image(
    source: str | bytes | io.BytesIO,
    filename: str = "astronomical_image.fits"
) -> LoadedFitsProduct:
    """Read and validate a FITS astronomical image product.
    Strictly verifies 2D dimensionality.
    """
    try:
        if isinstance(source, bytes):
            hdul = fits.open(io.BytesIO(source))
        elif isinstance(source, io.BytesIO):
            hdul = fits.open(source)
        else:
            hdul = fits.open(source)
    except Exception as e:
        raise ValueError(f"Failed to open FITS file: {e}")

    # Find the first HDU that contains image data
    image_hdu = None
    for idx, hdu in enumerate(hdul):
        if hdu.data is not None and isinstance(hdu.data, np.ndarray):
            image_hdu = hdu
            break

    if image_hdu is None:
        hdul.close()
        raise ValueError("FITS file contains no data array in any HDU")

    data = image_hdu.data
    header = image_hdu.header

    # Dimensionality validation
    ndim = data.ndim
    if ndim == 3 and data.shape[0] == 1:
        # Squeeze singleton dimension if present (1, H, W) -> (H, W)
        data = np.squeeze(data, axis=0)
        ndim = 2
    elif ndim != 2:
        hdul.close()
        raise ValueError(
            f"Unsupported FITS dimensionality: received {ndim}D data with shape {data.shape}. "
            "SPHEREx Image Renderer requires 2D astronomical image products."
        )

    # Cast to float32 and inspect NaNs/Infs
    data_float = data.astype(np.float32)
    nan_mask = np.isnan(data_float) | np.isinf(data_float)
    nan_count = int(np.isnan(data_float).sum())

    # Replace NaNs/Infs in clean array for numerical metric computations
    clean_data = np.nan_to_num(data_float, nan=0.0, posinf=0.0, neginf=0.0)
    height, width = clean_data.shape

    # Validate header dimensions match array shape
    hdr_naxis1 = header.get("NAXIS1")
    hdr_naxis2 = header.get("NAXIS2")
    if hdr_naxis1 is not None and hdr_naxis2 is not None:
        try:
            n1 = int(hdr_naxis1)
            n2 = int(hdr_naxis2)
            if n1 != width or n2 != height:
                hdul.close()
                raise ValueError(
                    f"FITS header dimensions (NAXIS1={n1}, NAXIS2={n2}) do not match data array shape ({height}, {width})"
                )
        except (ValueError, TypeError) as err:
            if "do not match data array shape" in str(err):
                raise

    # Extract WCS
    wcs = extract_wcs(header)
    wcs_meta = extract_wcs_metadata(wcs, width, height)

    # Observation metadata cards
    telescope = header.get("TELESCOP") or header.get("OBSERVAT")
    instrument = header.get("INSTRUME")
    target_object = header.get("OBJECT") or header.get("TARGET")
    date_obs = header.get("DATE-OBS")
    filter_band = header.get("FILTER") or header.get("BAND")
    bunit = header.get("BUNIT", "adu")
    exptime = header.get("EXPTIME")
    if exptime is not None:
        try:
            exptime = float(exptime)
        except (ValueError, TypeError):
            exptime = None

    bitpix = int(header.get("BITPIX", 32))

    data_min = float(np.min(clean_data))
    data_max = float(np.max(clean_data))
    data_mean = float(np.mean(clean_data))
    data_std = float(np.std(clean_data))

    metadata = FitsMetadata(
        filename=filename,
        dimensions=(width, height),
        naxis=2,
        bitpix=bitpix,
        bunit=str(bunit),
        telescope=str(telescope) if telescope else None,
        instrument=str(instrument) if instrument else None,
        target_object=str(target_object) if target_object else None,
        date_obs=str(date_obs) if date_obs else None,
        filter_band=str(filter_band) if filter_band else None,
        exposure_time_sec=exptime,
        data_min=round(data_min, 4),
        data_max=round(data_max, 4),
        data_mean=round(data_mean, 4),
        data_std=round(data_std, 4),
        nan_count=nan_count,
        wcs=wcs_meta,
    )

    hdul.close()

    return LoadedFitsProduct(
        data=clean_data,
        header=header,
        wcs=wcs,
        metadata=metadata,
        nan_mask=nan_mask
    )
