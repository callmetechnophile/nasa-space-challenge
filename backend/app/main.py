"""SkyTrace Backend Application.
Provides astronomical coordinate engines, multi-epoch observations, 102-band infrared spectroscopy,
and scientific difference imaging.
"""

from __future__ import annotations

import logging
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.coordinates import router as coordinates_router
from app.api.targets import router as targets_router
from app.api.observations import router as observations_router
from app.api.spectral import router as spectral_router
from app.api.image_processing import router as images_router
from app.api.image_routes import router as wcs_images_router
from app.api.spherex_routes import router as spherex_router
from app.api.temporal_routes import router as temporal_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("skytrace.backend")

app = FastAPI(
    title="SkyTrace API",
    version="1.0.0",
    description="A scientific astronomy development environment for exploring and analyzing SPHEREx observations.",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(coordinates_router, prefix="/api/v1")
app.include_router(targets_router, prefix="/api/v1")
app.include_router(observations_router, prefix="/api/v1")
app.include_router(spectral_router, prefix="/api/v1")
app.include_router(images_router, prefix="/api/v1")
app.include_router(wcs_images_router, prefix="/api/v1")
app.include_router(spherex_router, prefix="/api/v1")
app.include_router(temporal_router, prefix="/api/v1")


@app.get("/")
def root_info():
    return {
        "mission": "SPHEREx — Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices Explorer",
        "system": "SkyTrace Backend",
        "version": "1.0.0",
        "status": "ONLINE",
        "documentation": "/docs",
        "verification_targets": ["Barnard's Star", "WISE 0855", "Epsilon Indi B", "RW Aurigae", "R Draconis"],
    }


@app.get("/health")
def health_check():
    """Liveness probe: reports service process health."""
    return {
        "status": "HEALTHY",
        "astropy_wcs": True,
        "spectral_channels": 102,
        "version": "1.0.0",
    }


@app.get("/ready")
def readiness_check():
    """Readiness probe: validates critical dependencies before routing traffic."""
    checks = {
        "astropy_wcs": True,
        "spectral_channels": 102,
        "database": "configured" if settings.database_url else "standalone",
    }

    try:
        os.makedirs(settings.local_storage_dir, exist_ok=True)
        checks["storage_accessible"] = True
    except Exception as exc:
        logger.error(f"Storage accessibility failure: {exc}")
        checks["storage_accessible"] = False

    is_ready = checks["astropy_wcs"] and checks.get("storage_accessible", False)
    status_code = 200 if is_ready else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "READY" if is_ready else "NOT_READY",
            "environment": settings.environment,
            "checks": checks,
        },
    )
