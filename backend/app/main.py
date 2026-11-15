"""SPHEREx — 3D Temporal Sky Explorer Backend Application.
Provides astronomical coordinate engines, multi-epoch observations, 102-band infrared spectroscopy,
and scientific difference imaging.
"""

from __future__ import annotations

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.coordinates import router as coordinates_router
from app.api.targets import router as targets_router
from app.api.observations import router as observations_router
from app.api.spectral import router as spectral_router
from app.api.image_processing import router as images_router
from app.api.image_routes import router as wcs_images_router
from app.api.spherex_routes import router as spherex_router
from app.api.temporal_routes import router as temporal_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="SPHEREx 3D Temporal Sky Explorer API",
    version="1.0.0",
    description="Scientific astronomical backend for NASA's SPHEREx mission data exploration.",
)

# CORS configuration
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_env_origins = os.getenv("ALLOWED_ORIGINS")
if _env_origins:
    ALLOWED_ORIGINS.extend([origin.strip() for origin in _env_origins.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
        "system": "3D Temporal Sky Explorer Backend",
        "version": "1.0.0",
        "status": "ONLINE",
        "documentation": "/docs",
        "verification_targets": ["Barnard's Star", "WISE 0855", "Epsilon Indi B", "RW Aurigae", "R Draconis"],
    }


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "astropy_wcs": True, "spectral_channels": 102}
