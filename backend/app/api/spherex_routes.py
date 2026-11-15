"""SPHEREx Archive & Visualization API Endpoints (Milestone 4).
Exposes routes for:
- Querying NASA/IPAC IRSA SIA2 archive for real SPHEREx observations
- Controlled streaming download of genuine Level 2 MEF products
- Inspecting multi-extension structures and header metadata
- Converting real SPHEREx FITS into 3D celestial sphere visualization layers
- Monitoring local storage cache
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status

from app.models.spherex_observation import (
    SpherexSearchRequest,
    SpherexSearchResponse,
    SpherexDownloadRequest,
    SpherexDownloadResponse,
    SpherexMefInspection,
    SpherexLayerLoadRequest,
    SpherexLayerPayload,
)
from app.services.spherex_query import execute_spherex_search
from app.services.spherex_download import (
    download_spherex_fits,
    get_storage_stats,
    SPHEREx_STORAGE_DIR,
)
from app.astronomy.spherex_mef_reader import (
    inspect_spherex_mef,
    load_spherex_layer,
)

router = APIRouter(prefix="/spherex", tags=["SPHEREx Real Data Archive"])


def _validate_safe_filename(filename: str) -> Path:
    """Ensure filename is a single basename without directory traversal."""
    clean_name = os.path.basename(filename)
    if ".." in filename or "/" in filename or "\\" in filename:
        clean_name = os.path.basename(filename.replace("\\", "/"))
    
    file_path = Path(SPHEREx_STORAGE_DIR) / clean_name
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SPHEREx FITS product '{clean_name}' not found in cache. Download it first."
        )
    return file_path


@router.post(
    "/search",
    response_model=SpherexSearchResponse,
    summary="Search NASA/IPAC IRSA Archive for SPHEREx observations",
    description="Queries IRSA SIA2 catalog by celestial position (RA, Dec, Radius). Automatically falls back from QR3 to QR2 if no initial matches.",
)
async def search_spherex_observations(request: SpherexSearchRequest) -> SpherexSearchResponse:
    try:
        return await execute_spherex_search(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to query IRSA SIA2 archive: {str(e)}"
        )


@router.get(
    "/observations",
    response_model=SpherexSearchResponse,
    summary="GET search NASA/IPAC IRSA Archive",
)
async def get_spherex_observations(
    ra: float = Query(..., ge=0.0, le=360.0, description="Right Ascension in decimal degrees"),
    dec: float = Query(..., ge=-90.0, le=90.0, description="Declination in decimal degrees"),
    radius_deg: float = Query(0.05, ge=0.0001, le=2.0, description="Search radius in degrees"),
    collection: str = Query("spherex_qr3", description="Collection name"),
    allow_fallback: bool = Query(True, description="Fallback to QR2 if QR3 has no matches"),
    detector_filter: Optional[str] = Query(None, description="Optional filter (e.g. SPHEREx-D1)"),
) -> SpherexSearchResponse:
    req = SpherexSearchRequest(
        ra=ra,
        dec=dec,
        radius_deg=radius_deg,
        collection=collection,
        allow_fallback=allow_fallback,
        detector_filter=detector_filter,
    )
    try:
        return await execute_spherex_search(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to query IRSA SIA2 archive: {str(e)}"
        )


@router.post(
    "/download",
    response_model=SpherexDownloadResponse,
    summary="Download real SPHEREx FITS observation product",
    description="Streams FITS file from official IRSA URL to local storage with SHA-256 verification and size limit management.",
)
async def download_observation(request: SpherexDownloadRequest) -> SpherexDownloadResponse:
    try:
        return await download_spherex_fits(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Download failed: {str(e)}"
        )


@router.get(
    "/inspect/{filename}",
    response_model=SpherexMefInspection,
    summary="Inspect downloaded SPHEREx Multi-Extension FITS file",
    description="Returns detailed HDU breakdown, WCS distortion info, data units, and pixel flags.",
)
def inspect_product(filename: str) -> SpherexMefInspection:
    file_path = _validate_safe_filename(filename)
    try:
        return inspect_spherex_mef(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect SPHEREx MEF file: {str(e)}"
        )


@router.post(
    "/load-layer",
    response_model=SpherexLayerPayload,
    summary="Convert real SPHEREx FITS to Three.js celestial sphere layer",
    description="Computes WCS-SIP spherical geometry mesh and display texture Data URI.",
)
def load_layer(request: SpherexLayerLoadRequest) -> SpherexLayerPayload:
    file_path = _validate_safe_filename(request.filename)
    try:
        return load_spherex_layer(file_path, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process SPHEREx layer: {str(e)}"
        )


@router.get(
    "/status",
    summary="Get SPHEREx cache status and disk usage",
)
def get_cache_status():
    stats = get_storage_stats()
    cached_files = []
    if os.path.exists(SPHEREx_STORAGE_DIR):
        for f in os.listdir(SPHEREx_STORAGE_DIR):
            if f.endswith(".fits"):
                fp = os.path.join(SPHEREx_STORAGE_DIR, f)
                cached_files.append({
                    "filename": f,
                    "size_mb": round(os.path.getsize(fp) / (1024 * 1024), 2),
                    "modified": os.path.getmtime(fp),
                })
    return {
        "status": "ONLINE",
        "storage_dir": SPHEREx_STORAGE_DIR,
        "stats": stats,
        "cached_products": cached_files,
    }
