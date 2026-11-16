"""SPHEREx Milestone 5 Temporal Comparison API Routes.
Exposes endpoints for multi-epoch observation discovery, spectral-temporal
difference imaging, significance mapping, and change candidate inspection.
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.temporal_service import TemporalService, DATA_DIR
from app.services.spherex_discovery import SpherexDiscoveryService

router = APIRouter(prefix="/temporal", tags=["Temporal Analysis (Milestone 5 & 6)"])
service = TemporalService()
discovery_service = SpherexDiscoveryService()


@router.get("/discovery")
async def discover_time_series(
    ra: float = Query(..., ge=0.0, le=360.0, description="Right Ascension in decimal degrees"),
    dec: float = Query(..., ge=-90.0, le=90.0, description="Declination in decimal degrees"),
    fov: float = Query(0.5, ge=0.01, le=10.0, description="Field of View in degrees"),
    release: str = Query("all", description="Target release: dr1, qr3, both, or all"),
    detector: Optional[str] = Query(None, description="Optional detector filter: SPHEREx-D1 to D6"),
    use_cache: bool = Query(True, description="Whether to serve from local query cache"),
    force_refresh: bool = Query(False, description="Whether to force fresh archive query"),
):
    """Milestone 6: Discover chronological multi-epoch observations across DR1 and QR3 with WCS validation."""
    try:
        res = await discovery_service.discover_time_series(
            ra=ra,
            dec=dec,
            fov_deg=fov,
            release=release,
            detector=detector,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery error: {str(e)}")


class TemporalCompareRequest(BaseModel):
    file1: str = Field(..., description="Filename or path of Reference observation (Epoch 1)")
    file2: str = Field(..., description="Filename or path of Comparison observation (Epoch 2)")
    significance_threshold: float = Field(3.5, description="Significance SNR threshold (|S| >= threshold)")
    spectral_tolerance: float = Field(0.02, description="Maximum relative wavelength difference (|dlam/lam| <= tol)")
    grid_size: int = Field(512, description="Dimension of common reprojected WCS grid (default 512x512)")
    subtract_background: bool = Field(True, description="Whether to subtract median residual sky background")


@router.get("/observations")
async def get_observations():
    """List available SPHEREx observations in the local archive suitable for temporal comparison."""
    try:
        obs = service.list_available_observations()
        return {"count": len(obs), "observations": obs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_epochs(request: TemporalCompareRequest):
    """Execute complete scientific temporal comparison and difference imaging between two epochs."""
    p1 = service.resolve_or_fetch_observation_file(request.file1)
    if not p1:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Reference observation file not found or could not be retrieved from storage or archive: {request.file1}",
                "filename": request.file1,
                "stage": "FILE_INGESTION",
                "category": "MISSING_INPUT_FILE",
            },
        )

    p2 = service.resolve_or_fetch_observation_file(request.file2)
    if not p2:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Comparison observation file not found or could not be retrieved from storage or archive: {request.file2}",
                "filename": request.file2,
                "stage": "FILE_INGESTION",
                "category": "MISSING_INPUT_FILE",
            },
        )

    try:
        result = service.run_difference_pipeline(
            fits_path_1=p1,
            fits_path_2=p2,
            significance_threshold=request.significance_threshold,
            spectral_tolerance=request.spectral_tolerance,
            grid_size=request.grid_size,
            subtract_background=request.subtract_background,
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"Scientific validation failure: {str(ve)}",
                "stage": "SCIENTIFIC_VALIDATION",
                "category": "SCIENTIFIC_INCOMPATIBILITY",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Error running temporal comparison: {str(e)}",
                "stage": "PIPELINE_EXECUTION",
                "category": "INTERNAL_PROCESSING_ERROR",
            },
        )


@router.get("/benchmark-pairs")
async def get_benchmark_pairs():
    """Return pre-cataloged multi-epoch observation pairs identified during Phase 0 IRSA SIA2 analysis."""
    pairs = [
        {
            "pair_id": "PAIR-EQUATORIAL-D1-8D-APPROVED",
            "detector": "SPHEREx-D1",
            "band": "0.75 - 1.12 µm",
            "separation_arcsec": 2.88,
            "baseline_days": 8.074,
            "baseline_hours": 193.8,
            "epoch_1": {
                "obs_id": "2026W31_2A_0034_3",
                "file_name": "level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
                "mjd": 61251.6984,
                "ra": 46.8444,
                "dec": 1.8322,
                "url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W31_2A/l2b-v27-2026-224/1/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits",
            },
            "epoch_2": {
                "obs_id": "2026W32_2A_0338_1",
                "file_name": "level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits",
                "mjd": 61259.7726,
                "ra": 46.8438,
                "dec": 1.8313,
                "url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W32_2A/l2b-v27-2026-223/1/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits",
            },
        },
        {
            "pair_id": "PAIR-EQUATORIAL-D5-8D",
            "detector": "SPHEREx-D5",
            "band": "3.82 - 4.42 µm",
            "separation_arcsec": 2.88,
            "baseline_days": 8.074,
            "baseline_hours": 193.8,
            "epoch_1": {
                "obs_id": "2026W31_2A_0034_3",
                "mjd": 61251.6984,
                "ra": 43.156,
                "dec": 0.696,
                "url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W31_2A/l2b-v27-2026-224/5/level2_2026W31_2A_0034_3D5_spx_l2b-v27-2026-224.fits",
            },
            "epoch_2": {
                "obs_id": "2026W32_2A_0338_1",
                "mjd": 61259.7726,
                "ra": 43.155,
                "dec": 0.696,
                "url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W32_2A/l2b-v27-2026-223/5/level2_2026W32_2A_0338_1D5_spx_l2b-v27-2026-223.fits",
            },
        },
        {
            "pair_id": "PAIR-EQUATORIAL-D2-8D",
            "detector": "SPHEREx-D2",
            "band": "1.12 - 1.67 µm",
            "separation_arcsec": 2.88,
            "baseline_days": 8.074,
            "baseline_hours": 193.8,
            "epoch_1": {
                "obs_id": "2026W31_2A_0034_3",
                "mjd": 61251.6984,
                "ra": 43.157,
                "dec": 0.679,
                "url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W31_2A/l2b-v27-2026-224/2/level2_2026W31_2A_0034_3D2_spx_l2b-v27-2026-224.fits",
            },
            "epoch_2": {
                "obs_id": "2026W32_2A_0338_1",
                "mjd": 61259.7726,
                "ra": 43.157,
                "dec": 0.678,
                "url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W32_2A/l2b-v27-2026-223/2/level2_2026W32_2A_0338_1D2_spx_l2b-v27-2026-223.fits",
            },
        },
        {
            "pair_id": "PAIR-EQUATORIAL-D1-40D",
            "detector": "SPHEREx-D1",
            "band": "0.75 - 1.12 µm",
            "separation_arcsec": 19.08,
            "baseline_days": 40.453,
            "baseline_hours": 970.9,
            "epoch_1": {
                "obs_id": "2026W30_2A_0607_2",
                "mjd": 61247.3564,
                "ra": 44.450,
                "dec": -1.355,
                "url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W30_2A/l2b-v27-2026-224/1/level2_2026W30_2A_0607_2D1_spx_l2b-v27-2026-224.fits",
            },
            "epoch_2": {
                "obs_id": "2026W36_2A_0360_1",
                "mjd": 61287.8091,
                "ra": 44.444,
                "dec": -1.356,
                "url": "https://irsa.ipac.caltech.edu/ibe/data/spherex/qr3/level2/2026W36_2A/l2b-v27-2026-254/1/level2_2026W36_2A_0360_1D1_spx_l2b-v27-2026-254.fits",
            },
        },
    ]
    return {"count": len(pairs), "pairs": pairs}
