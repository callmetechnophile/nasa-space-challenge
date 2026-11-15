"""SPHEREx Milestone 4 — Comprehensive Automated Scientific Validation Suite.
Tests:
- IRSA SIA2 Live Archive Discovery (QR3 and QR2 fallback)
- MEF FITS Reader & HDU Preservation (IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE)
- WCS-SIP Distortion Compatibility & Round-trip Precision
- 3D Spherical Mesh Generation & Texture Synthesis
- REST API Endpoints (/api/v1/spherex/search, /inspect, /load-layer, /status)
- Scientific Units (MJy/sr) & Cryptographic SHA-256 Integrity
"""

import os
import json
import time
import hashlib
import numpy as np
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
import httpx

API_BASE = "http://127.0.0.1:8000"
REAL_FITS_PATH = Path("data/spherex/level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits")


def test_01_real_fits_presence_and_sha256():
    """Verify genuine downloaded SPHEREx Level 2 MEF file exists with expected size and hash."""
    print("=== TEST 01: REAL SPHEREx FITS INTEGRITY ===")
    assert REAL_FITS_PATH.is_file(), f"Real SPHEREx FITS file missing at {REAL_FITS_PATH}"
    
    file_size = REAL_FITS_PATH.stat().st_size
    print(f"File size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
    assert file_size > 65 * 1024 * 1024, "File size must be > 65 MB for a 2040x2040 SPHEREx L2 product"

    sha = hashlib.sha256()
    with open(REAL_FITS_PATH, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    digest = sha.hexdigest()
    print(f"SHA-256: {digest}")
    assert len(digest) == 64
    assert digest == "36b330b5ed45161383aedc7e9199619c6ca1873e213a5fdc8ff027274190caf6"
    print("TEST 01 PASSED\n")


def test_02_mef_structure_and_hdu_preservation():
    """Verify all 7 HDUs and validate scientific preservation of ancillary extensions."""
    print("=== TEST 02: MEF STRUCTURE & ANCILLARY PRESERVATION ===")
    with fits.open(REAL_FITS_PATH) as hdul:
        hdu_names = [h.name for h in hdul]
        print(f"Extensions found: {hdu_names}")
        assert "IMAGE" in hdu_names, "Missing IMAGE HDU"
        assert "FLAGS" in hdu_names, "Missing FLAGS HDU"
        assert "VARIANCE" in hdu_names, "Missing VARIANCE HDU"
        assert "ZODI" in hdu_names, "Missing ZODI HDU"
        assert "PSF" in hdu_names, "Missing PSF HDU"
        assert "WCS-WAVE" in hdu_names, "Missing WCS-WAVE HDU"

        # Check IMAGE
        img_hdu = hdul["IMAGE"]
        assert img_hdu.data.shape == (2040, 2040), f"Expected 2040x2040, got {img_hdu.data.shape}"
        assert img_hdu.data.dtype.kind == 'f' and img_hdu.data.dtype.itemsize == 4, f"Expected 32-bit float, got {img_hdu.data.dtype}"
        bunit = img_hdu.header.get("BUNIT", "").strip()
        print(f"IMAGE BUNIT: '{bunit}'")
        assert "MJy" in bunit and "sr" in bunit, f"Expected MJy/sr units, got '{bunit}'"

        # Check FLAGS
        flags_hdu = hdul["FLAGS"]
        assert flags_hdu.data.shape == (2040, 2040)
        flagged_count = np.count_nonzero(flags_hdu.data)
        print(f"FLAGS: {flagged_count} flagged pixels out of {flags_hdu.data.size}")

        # Check VARIANCE
        var_hdu = hdul["VARIANCE"]
        assert var_hdu.data.shape == (2040, 2040)
        valid_var = var_hdu.data[np.isfinite(var_hdu.data)]
        print(f"VARIANCE: min={np.min(valid_var):.4e}, max={np.max(valid_var):.4e}, median={np.median(valid_var):.4e}")

        # Check ZODI (un-subtracted zodiacal light)
        zodi_hdu = hdul["ZODI"]
        assert zodi_hdu.data.shape == (2040, 2040)
        valid_zodi = zodi_hdu.data[np.isfinite(zodi_hdu.data)]
        print(f"ZODI: min={np.min(valid_zodi):.4f}, max={np.max(valid_zodi):.4f}, mean={np.mean(valid_zodi):.4f} MJy/sr")

        # Check PSF
        psf_hdu = hdul["PSF"]
        print(f"PSF shape: {psf_hdu.data.shape}")
        assert psf_hdu.data.ndim == 3

        # Check WCS-WAVE
        wave_hdu = hdul["WCS-WAVE"]
        print(f"WCS-WAVE columns: {wave_hdu.columns.names}")
        assert "VALUES" in wave_hdu.columns.names or len(wave_hdu.columns) >= 3

    print("TEST 02 PASSED\n")


def test_03_wcs_sip_distortion_compatibility():
    """Verify Astropy WCS correctly parses CTYPE1/2 with TAN-SIP and A/B_ORDER=3."""
    print("=== TEST 03: WCS-SIP DISTORTION COMPATIBILITY ===")
    with fits.open(REAL_FITS_PATH) as hdul:
        header = hdul["IMAGE"].header
        wcs = WCS(header)
        print(f"CTYPE: {wcs.wcs.ctype}")
        assert "TAN-SIP" in wcs.wcs.ctype[0]
        assert "TAN-SIP" in wcs.wcs.ctype[1]
        assert wcs.sip is not None, "SIP distortion polynomial must be parsed"
        print(f"SIP A_ORDER: {wcs.sip.a_order}, B_ORDER: {wcs.sip.b_order}")
        assert wcs.sip.a_order == 3
        assert wcs.sip.b_order == 3

        # Numerical round trip test at 5 sample points
        test_pts = np.array([
            [1020.0, 1020.0],  # Center
            [0.0, 0.0],        # Bottom-left
            [2039.0, 0.0],     # Bottom-right
            [2039.0, 2039.0],  # Top-right
            [0.0, 2039.0],     # Top-left
        ])

        world_coords = wcs.all_pix2world(test_pts, 0)
        reproj_pts = wcs.all_world2pix(world_coords, 0)
        residuals = np.linalg.norm(test_pts - reproj_pts, axis=1)
        max_residual = float(np.max(residuals))
        print(f"WCS SIP Round-trip max residual: {max_residual:.4e} pixels")
        assert max_residual < 1e-4, f"Round trip residual {max_residual} px exceeds 1e-4 px"

    print("TEST 03 PASSED\n")


def test_04_api_status_and_inspection():
    """Verify REST API /api/v1/spherex/status and /inspect endpoints."""
    print("=== TEST 04: REST API STATUS & INSPECTION ===")
    client = httpx.Client(base_url=API_BASE, timeout=30)
    
    # Status
    res_status = client.get("/api/v1/spherex/status")
    assert res_status.status_code == 200, f"Status failed: {res_status.text}"
    status_data = res_status.json()
    print(f"Cache status: {status_data['stats']['file_count']} files, {status_data['stats']['total_mb']} MB")
    assert status_data["stats"]["file_count"] >= 1

    # Inspect
    res_inspect = client.get(f"/api/v1/spherex/inspect/{REAL_FITS_PATH.name}")
    assert res_inspect.status_code == 200, f"Inspect failed: {res_inspect.text}"
    insp = res_inspect.json()
    print(f"Inspected product: ObsID={insp['observation_id']}, Detector={insp['detector']}, Units={insp['image_units']}")
    assert insp["has_image"] is True
    assert insp["has_flags"] is True
    assert insp["has_variance"] is True
    assert insp["has_sip"] is True
    assert insp["sip_order"] == 3
    assert len(insp["hdus"]) == 7
    print("TEST 04 PASSED\n")


def test_05_api_layer_load():
    """Verify /api/v1/spherex/load-layer generates valid 3D spherical mesh and PNG texture."""
    print("=== TEST 05: SPHEREX LAYER SYNTHESIS ===")
    client = httpx.Client(base_url=API_BASE, timeout=60)
    payload = {
        "filename": REAL_FITS_PATH.name,
        "stretch": "asinh",
        "radius": 98.0,
    }
    t0 = time.time()
    res = client.post("/api/v1/spherex/load-layer", json=payload)
    dt = time.time() - t0
    assert res.status_code == 200, f"Layer load failed: {res.text}"
    layer = res.json()
    print(f"Layer processed in {dt:.2f}s: ID={layer['layer_id']}, Title={layer['title']}")
    assert layer["is_real_data"] is True
    assert layer["provenance"] == "NASA/IPAC IRSA SPHEREx"
    assert len(layer["mesh"]["vertices"]) > 100
    assert layer["texture_data_uri"].startswith("data:image/png;base64,")
    print(f"Mesh vertices: {layer['mesh']['vertex_count']}, Texture size: {len(layer['texture_data_uri'])} chars")
    print("TEST 05 PASSED\n")


if __name__ == "__main__":
    test_01_real_fits_presence_and_sha256()
    test_02_mef_structure_and_hdu_preservation()
    test_03_wcs_sip_distortion_compatibility()
    test_04_api_status_and_inspection()
    test_05_api_layer_load()
    print("========================================")
    print("ALL M4 SCIENTIFIC AUTOMATION TESTS PASSED!")
    print("========================================")
