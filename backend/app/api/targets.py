"""FastAPI endpoints for NASA Validation Targets."""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import AstronomicalTargetDetail
from app.providers import get_data_provider
from app.astronomy.m6_target_validation import TargetValidationSuite

router = APIRouter(prefix="/targets", tags=["targets"])
validation_suite = TargetValidationSuite()


@router.get("", response_model=List[AstronomicalTargetDetail])
def list_validation_targets() -> List[AstronomicalTargetDetail]:
    """Retrieve the five core NASA test targets with verified astrophysical parameters."""
    provider = get_data_provider("curated")
    # All five targets
    slugs = ["barnards-star", "wise-0855", "epsilon-indi-b", "rw-aurigae", "r-draconis"]
    targets = []
    for slug in slugs:
        t = provider.get_target_by_id(slug)
        if t:
            targets.append(t)
    return targets


@router.get("/m6-validation")
async def get_m6_validation_suite():
    """Execute complete Milestone 6 validation across all five required targets."""
    return await validation_suite.evaluate_all_targets()


@router.get("/m6-validation/{target_slug}")
async def get_m6_target_validation(target_slug: str):
    """Execute Milestone 6 validation for a single required target."""
    try:
        return await validation_suite.evaluate_target(target_slug)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{target_id}", response_model=AstronomicalTargetDetail)
def get_target_details(target_id: str) -> AstronomicalTargetDetail:
    """Retrieve details, multi-epoch observations, and 102-band spectra for a specific target."""
    provider = get_data_provider("curated")
    target = provider.get_target_by_id(target_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Target '{target_id}' not found in verification suite.")
    return target
