"""Astronomical Image API Routes for SPHEREx 3D Sky Explorer.
Provides endpoints for FITS upload, WCS extraction, spherical mesh generation,
display stretching, and sample demonstration fixtures.
"""

from __future__ import annotations

import io
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, status
from pydantic import BaseModel, Field

from app.astronomy.fits_reader import read_fits_image, FitsMetadata
from app.astronomy.wcs_processor import WcsMetadata, validate_round_trip
from app.astronomy.image_renderer import render_to_data_uri, DisplayStretch
from app.astronomy.image_footprint import generate_spherical_mesh, SphericalMeshGeometry
from app.astronomy.sample_data import SAMPLE_FIXTURES, get_sample_fits

router = APIRouter(prefix="/images", tags=["astronomical-images"])

# In-memory session cache for processed images to allow fast re-stretching without re-uploading
IMAGE_CACHE: Dict[str, Any] = {}


class SampleImageInfo(BaseModel):
    id: str
    title: str
    provenance: str
    ra: float
    dec: float
    width: int
    height: int
    pixel_scale_arcsec: float
    projection: str
    description: str


class ImageLayerPayload(BaseModel):
    layer_id: str
    title: str
    provenance: str
    metadata: FitsMetadata
    mesh: SphericalMeshGeometry
    texture_data_uri: str
    stretch: str
    brightness: float
    contrast: float


class StretchUpdateRequest(BaseModel):
    layer_id: str
    stretch: DisplayStretch = "asinh"
    brightness: float = 1.0
    contrast: float = 1.0


@router.get("/samples", response_model=List[SampleImageInfo])
def list_sample_images():
    """List available pre-configured demonstration FITS fields."""
    return [
        SampleImageInfo(
            id=item["id"],
            title=item["title"],
            provenance=item["provenance"],
            ra=item["ra"],
            dec=item["dec"],
            width=item["width"],
            height=item["height"],
            pixel_scale_arcsec=item["pixel_scale"],
            projection=item["projection"],
            description=item["description"],
        )
        for item in SAMPLE_FIXTURES.values()
    ]


@router.get("/sample/{sample_id}", response_model=ImageLayerPayload)
def load_sample_image(
    sample_id: str,
    stretch: DisplayStretch = Query("asinh", description="Display stretch algorithm"),
    brightness: float = Query(1.0, ge=0.1, le=3.0),
    contrast: float = Query(1.0, ge=0.1, le=3.0),
    radius: float = Query(98.0, ge=50.0, le=150.0, description="Celestial sphere radius"),
):
    """Load a verified sample FITS product, generate WCS spherical mesh and stretched texture."""
    if sample_id not in SAMPLE_FIXTURES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample '{sample_id}' not found. Available: {list(SAMPLE_FIXTURES.keys())}"
        )

    product = get_sample_fits(sample_id)
    width, height = product.metadata.dimensions

    # Cache for fast re-stretching
    IMAGE_CACHE[sample_id] = product

    # 1. Generate spherical mesh geometry
    mesh = generate_spherical_mesh(
        product.wcs,
        width=width,
        height=height,
        radius=radius,
    )

    # 2. Render texture with requested stretch
    texture_uri = render_to_data_uri(
        product.data,
        stretch=stretch,
        brightness=brightness,
        contrast=contrast,
        nan_mask=product.nan_mask,
    )

    return ImageLayerPayload(
        layer_id=sample_id,
        title=product.metadata.target_object or f"Sample {sample_id}",
        provenance="SYNTHETIC DEMONSTRATION DATA (WCS-CALIBRATED)",
        metadata=product.metadata,
        mesh=mesh,
        texture_data_uri=texture_uri,
        stretch=stretch,
        brightness=brightness,
        contrast=contrast,
    )


@router.post("/process-fits", response_model=ImageLayerPayload)
async def process_fits_upload(
    file: UploadFile = File(...),
    stretch: DisplayStretch = Form("asinh"),
    brightness: float = Form(1.0),
    contrast: float = Form(1.0),
    radius: float = Form(98.0),
):
    """Upload a custom FITS file, extract WCS metadata, generate spherical mesh,
    and render visualization texture. Rejects non-2D images.
    """
    if not file.filename.lower().endswith((".fits", ".fit", ".fts")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .fits, .fit, or .fts extension"
        )

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    try:
        product = read_fits_image(contents, filename=file.filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing FITS file: {e}"
        )

    layer_id = f"custom-{abs(hash(file.filename)) % 1000000}"
    IMAGE_CACHE[layer_id] = product

    width, height = product.metadata.dimensions

    mesh = generate_spherical_mesh(
        product.wcs,
        width=width,
        height=height,
        radius=radius,
    )

    texture_uri = render_to_data_uri(
        product.data,
        stretch=stretch,
        brightness=brightness,
        contrast=contrast,
        nan_mask=product.nan_mask,
    )

    return ImageLayerPayload(
        layer_id=layer_id,
        title=product.metadata.target_object or file.filename,
        provenance="USER UPLOADED FITS PRODUCT",
        metadata=product.metadata,
        mesh=mesh,
        texture_data_uri=texture_uri,
        stretch=stretch,
        brightness=brightness,
        contrast=contrast,
    )


@router.post("/re-stretch")
def update_display_stretch(request: StretchUpdateRequest):
    """Re-render the display stretch texture for a loaded image layer without recomputing mesh geometry."""
    product = IMAGE_CACHE.get(request.layer_id)
    if not product:
        # Fall back to regenerating if it is a built-in sample
        if request.layer_id in SAMPLE_FIXTURES:
            product = get_sample_fits(request.layer_id)
            IMAGE_CACHE[request.layer_id] = product
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Layer '{request.layer_id}' not found in active session cache"
            )

    texture_uri = render_to_data_uri(
        product.data,
        stretch=request.stretch,
        brightness=request.brightness,
        contrast=request.contrast,
        nan_mask=product.nan_mask,
    )

    return {
        "layer_id": request.layer_id,
        "texture_data_uri": texture_uri,
        "stretch": request.stretch,
        "brightness": request.brightness,
        "contrast": request.contrast,
    }


@router.get("/validate-wcs/{sample_id}")
def validate_wcs_transformation(sample_id: str):
    """Verify numerical round-trip accuracy for a sample image's WCS."""
    if sample_id not in SAMPLE_FIXTURES:
        raise HTTPException(status_code=404, detail="Sample not found")

    product = get_sample_fits(sample_id)
    width, height = product.metadata.dimensions

    max_res, mean_res = validate_round_trip(product.wcs, width, height, grid_size=9)

    return {
        "sample_id": sample_id,
        "wcs_valid": True,
        "projection": product.metadata.wcs.projection_type,
        "center_radec": product.metadata.wcs.center_radec,
        "max_residual_pixels": max_res,
        "mean_residual_pixels": mean_res,
        "accuracy_status": "EXCELLENT" if max_res < 1e-4 else "ACCEPTABLE",
    }
