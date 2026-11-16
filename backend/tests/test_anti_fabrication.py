"""Comprehensive Anti-Fabrication & Scientific Data Provenance Test Suite.

Verifies the 6-state Data Provenance Registry invariants:
1. Archive failure / lack of spatial coverage never silently triggers synthetic fallback.
2. Production data provider never returns synthetic data disguised as real.
3. Sample / simulated providers strictly flag every epoch and channel with is_simulated=True and SYNTHETIC_DEMO.
4. Cutout and FITS generators inject mandatory PROVENAN headers.
5. Temporal difference service strictly classifies MOCK_TEST vs REAL_VERIFIED and tags candidate injections.
6. Checksums of authentic Level-2 SPHEREx products in data/spherex/ strictly match registry.
"""

import hashlib
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.provenance import (
    ProvenanceState,
    AUTHENTIC_FITS_REGISTRY,
    TEST_FIXTURE_REGISTRY,
    get_fits_file_provenance,
)
from app.providers.nasa_provider import NASADataConnector
from app.providers.sample_provider import SampleDataProvider
from app.providers.simulated_provider import SimulatedDataProvider
from app.services.temporal_service import TemporalService
from app.image_processing.cutout import create_synthetic_astronomical_cutout


@pytest.fixture
def client():
    return TestClient(app)


def test_provenance_registry_checksum_verification():
    """Verify that authentic Level-2 FITS baseline files have matching SHA256 checksums."""
    data_dir = Path("data/spherex")
    if not data_dir.exists():
        pytest.skip("data/spherex directory not present in current working environment")

    for filename, record in AUTHENTIC_FITS_REGISTRY.items():
        file_path = data_dir / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()
            assert sha256 == record["sha256"], f"Checksum mismatch for authentic FITS {filename}"
            assert record["validation_status"] == "VERIFIED"


def test_archive_failure_does_not_trigger_silent_synthetic_fallback():
    """Verify that querying coordinates outside real FITS coverage returns empty list, NOT fake data."""
    connector = NASADataConnector()

    # Coordinates with zero real FITS coverage in DR1 / QR3 (e.g. Barnard's Star or arbitrary coords)
    obs = connector.get_observations_for_region(ra_deg=269.452083, dec_deg=4.693333, allow_demo_fallback=False)
    assert obs == [], "NASADataConnector must return empty list when no authentic FITS coverage exists"

    # Explicit consent required for synthetic demonstration data
    demo_obs = connector.get_observations_for_region(ra_deg=269.452083, dec_deg=4.693333, allow_demo_fallback=True)
    assert len(demo_obs) > 0, "Demo observations returned when allow_demo_fallback=True"
    for epoch in demo_obs:
        assert epoch.is_simulated is True, "Demo epoch must have is_simulated=True"
        assert epoch.provenance is not None
        assert epoch.provenance.provenance_state == ProvenanceState.SYNTHETIC_DEMO


def test_synthetic_sample_epochs_strictly_flagged():
    """Verify SampleDataProvider strictly marks multi-epoch observations as simulated demonstration."""
    provider = SampleDataProvider()
    epochs = provider.get_observations_for_region(ra_deg=133.795, dec_deg=-7.245)
    assert len(epochs) > 0
    for epoch in epochs:
        assert epoch.is_simulated is True
        assert epoch.data_provider == "SYNTHETIC_DEMONSTRATION_SAMPLE"
        assert epoch.provenance is not None
        assert epoch.provenance.provenance_state == ProvenanceState.SYNTHETIC_DEMO


def test_spectral_models_carry_synthetic_provenance():
    """Verify spectral cube generation marks analytical models as synthetic."""
    provider = SampleDataProvider()
    measurements = provider.get_spectral_profile(ra_deg=133.795, dec_deg=-7.245)
    assert len(measurements) == 102
    for m in measurements:
        assert m.is_simulated is True
        assert m.provenance_state == ProvenanceState.SYNTHETIC_DEMO


def test_cutout_headers_contain_provenance_markers():
    """Verify synthetic FITS cutouts contain explicit PROVENAN and ORIGIN headers."""
    data, wcs, header = create_synthetic_astronomical_cutout(
        ra_deg=180.0,
        dec_deg=0.0,
        fov_arcmin=6.0,
        channel_index=1,
        epoch_id="TEST_EPOCH",
    )
    assert header["PROVENAN"] == "SYNTHETIC_DEMO"
    assert header["ORIGIN"] == "SkyTrace Synthetic Cutout Generator"
    assert "SYNTHETIC" in str(header.get("COMMENT", ""))


def test_temporal_difference_distinguishes_real_vs_mock_fixtures():
    """Verify TemporalService tags mock test fixtures with MOCK_TEST and simulated injections."""
    service = TemporalService()

    fixture_1 = str(Path("data/spherex/fixtures_m5/m5_synthetic_epoch1.fits").resolve())
    fixture_2 = str(Path("data/spherex/fixtures_m5/m5_synthetic_epoch2.fits").resolve())

    if not os.path.exists(fixture_1) or not os.path.exists(fixture_2):
        pytest.skip("Test fixtures not present")

    result = service.run_difference_pipeline(
        fits_path_1=fixture_1,
        fits_path_2=fixture_2,
        significance_threshold=3.5,
    )

    assert "provenance" in result
    prov = result["provenance"]
    assert prov["provenance_state"] == "MOCK_TEST"
    assert prov["is_synthetic"] is True

    # Check that any candidate extracted from mock fixture is labeled as simulated injection
    for cand in result["candidates"]:
        assert cand.get("is_simulated_injection") is True


def test_api_endpoints_anti_fabrication_defaults(client):
    """Verify HTTP API endpoints enforce anti-fabrication defaults (allow_demo=false)."""
    # 1. Observations endpoint default: unobserved coords return empty list, NOT fake data
    resp = client.get("/api/v1/observations", params={"ra": 0.0, "dec": 0.0})
    assert resp.status_code == 200
    assert resp.json() == [], "Default GET /api/v1/observations must return [] when no real data exists"

    # 2. Observations with allow_demo=true returns clearly flagged synthetic demo data
    resp_demo = client.get("/api/v1/observations", params={"ra": 0.0, "dec": 0.0, "allow_demo": True})
    assert resp_demo.status_code == 200
    data = resp_demo.json()
    assert len(data) > 0
    for ep in data:
        assert ep["is_simulated"] is True
        assert ep["provenance"]["provenance_state"] == "SYNTHETIC_DEMO"

    # 3. Spectral profile endpoint default: unobserved coords return NO_DATA
    resp_spec = client.get("/api/v1/spectral/profile", params={"ra": 0.0, "dec": 0.0})
    assert resp_spec.status_code == 200
    spec_data = resp_spec.json()
    assert len(spec_data) == 102
    # Verify channels report flux unavailable and NO_DATA
    for m in spec_data:
        assert m["flux_is_available"] is False
        assert m["provenance_state"] == "NO_DATA"
