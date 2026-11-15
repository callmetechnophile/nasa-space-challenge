"""Unit tests for NASA validation targets and 102 spectral bands."""

import pytest
from app.providers import get_data_provider
from app.spectral.bands import SPHEREX_BANDS


def test_spherex_102_bands():
    assert len(SPHEREX_BANDS) == 102

    # Check wavelength coverage: Array 1 starts at 0.75 um, Array 6 ends near 5.0 um
    assert SPHEREX_BANDS[0].wavelength_um >= 0.75
    assert SPHEREX_BANDS[-1].wavelength_um <= 5.0

    # Check 6 arrays with 17 channels each
    for arr in range(1, 7):
        arr_bands = [b for b in SPHEREX_BANDS if b.array_index == arr]
        assert len(arr_bands) == 17


def test_five_nasa_targets():
    provider = get_data_provider("curated")
    expected_slugs = ["barnards-star", "wise-0855", "epsilon-indi-b", "rw-aurigae", "r-draconis"]

    for slug in expected_slugs:
        target = provider.get_target_by_id(slug)
        assert target is not None, f"Target {slug} must exist in validation suite"
        assert target.ra_deg >= 0.0 and target.ra_deg < 360.0
        assert -90.0 <= target.dec_deg <= 90.0
        assert len(target.available_epochs) == 4, f"Target {slug} must have 4 observation epochs"
        assert len(target.spectral_profile) == 102, f"Target {slug} must have 102 spectral channels"
        assert len(target.catalog_crossmatches) >= 1
