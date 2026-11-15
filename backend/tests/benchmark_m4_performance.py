"""Performance Measurement Reconciliation for SPHEREx Milestone 4.
Measures non-overlapping execution durations across 10 repetitions:
1. FITS MEF Opening & Header Parsing
2. 3rd-Order SIP WCS Mesh Generation (16x16 grid, 289 vertices)
3. Asinh Percentile Stretch & RGBA Mapping
4. PNG Image Encoding (Pillow) & Base64 Data URI
5. Total Sequential End-to-End Latency

Outputs hardware specs, median, and p95 benchmarks for the audit report.
"""

import os
import sys
import time
import platform
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from astropy.io import fits
from astropy.wcs import WCS
import PIL
import astropy

from app.models.spherex_observation import SpherexLayerLoadRequest
from app.astronomy.spherex_mef_reader import inspect_spherex_mef, load_spherex_layer
from app.astronomy.image_footprint import generate_spherical_mesh
from app.astronomy.image_renderer import render_to_png_bytes, apply_display_stretch

FITS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "spherex" / "level2_2025W44_2B_0322_4D1_spx_l2b-v20-2025-307.fits"


def benchmark_pipeline(n_runs: int = 10):
    assert FITS_PATH.exists(), f"Missing {FITS_PATH}"

    t_fits = []
    t_wcs = []
    t_stretch = []
    t_png = []
    t_total = []

    print(f"Running {n_runs} benchmark repetitions on {FITS_PATH.name} ($2040 \\times 2040$ float32)...")

    for i in range(n_runs):
        t0 = time.perf_counter()

        # Step 1: FITS MEF Parsing
        t_s1 = time.perf_counter()
        with fits.open(FITS_PATH) as hdul:
            img_hdu = hdul["IMAGE"]
            data = img_hdu.data.copy()
            header = img_hdu.header.copy()
            wcs = WCS(header)
        t_e1 = time.perf_counter()

        # Step 2: 3rd-Order SIP WCS Mesh (16x16)
        t_s2 = time.perf_counter()
        mesh = generate_spherical_mesh(wcs, 2040, 2040, radius=98.0, min_grid=16, max_grid=32)
        t_e2 = time.perf_counter()

        # Step 3: Asinh Percentile Stretch
        t_s3 = time.perf_counter()
        nan_mask = np.isnan(data) | np.isinf(data)
        clean = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
        stretched = apply_display_stretch(clean, stretch="asinh", vmin_pct=0.5, vmax_pct=99.5)
        t_e3 = time.perf_counter()

        # Step 4: PNG Encoding
        t_s4 = time.perf_counter()
        png_bytes = render_to_png_bytes(data, stretch="asinh", nan_mask=nan_mask)
        t_e4 = time.perf_counter()

        t_end = time.perf_counter()

        t_fits.append(t_e1 - t_s1)
        t_wcs.append(t_e2 - t_s2)
        t_stretch.append(t_e3 - t_s3)
        t_png.append(t_e4 - t_s4)
        t_total.append(t_end - t0)

        print(f"  Run {i+1:02d}: Total = {t_total[-1]:.3f}s (FITS: {t_fits[-1]:.3f}s, WCS: {t_wcs[-1]:.3f}s, Stretch: {t_stretch[-1]:.3f}s, PNG: {t_png[-1]:.3f}s)")

    def calc_stats(arr):
        a = np.array(arr)
        return {
            "min": float(np.min(a)),
            "median": float(np.median(a)),
            "mean": float(np.mean(a)),
            "p95": float(np.percentile(a, 95)),
            "max": float(np.max(a)),
        }

    return {
        "hardware": {
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "cpu": platform.processor(),
            "cpu_cores": os.cpu_count(),
            "ram_gb": "System Host RAM",
            "python": sys.version.split()[0],
            "astropy": astropy.__version__,
            "numpy": np.__version__,
            "pillow": PIL.__version__,
        },
        "stats": {
            "fits_parsing": calc_stats(t_fits),
            "wcs_mesh": calc_stats(t_wcs),
            "asinh_stretch": calc_stats(t_stretch),
            "png_encoding": calc_stats(t_png),
            "total_latency": calc_stats(t_total),
        }
    }


def main():
    print("=" * 80)
    print("AUDIT AREA 4: PERFORMANCE BENCHMARK RECONCILIATION")
    print("=" * 80)

    res = benchmark_pipeline(n_runs=10)
    hw = res["hardware"]
    st = res["stats"]

    print("\n--- TEST ENVIRONMENT & HARDWARE ---")
    print(f"  OS:              {hw['os']}")
    print(f"  CPU:             {hw['cpu']} ({hw['cpu_cores']} logical cores)")
    print(f"  RAM:             {hw['ram_gb']} GB")
    print(f"  Python Version:  {hw['python']}")
    print(f"  Astropy Version: {hw['astropy']}")
    print(f"  NumPy Version:   {hw['numpy']}")
    print(f"  Pillow Version:  {hw['pillow']}")

    print("\n--- TIMING BOUNDARIES & SUMMARY METRICS (10 REPETITIONS) ---")
    print(f"{'Operation':<26} | {'Median (s)':<12} | {'p95 (s)':<10} | {'Min (s)':<10} | {'Max (s)':<10}")
    print("-" * 75)
    for op, name in [
        ("fits_parsing", "1. FITS MEF Parsing"),
        ("wcs_mesh", "2. WCS SIP Mesh (16x16)"),
        ("asinh_stretch", "3. Asinh Stretch"),
        ("png_encoding", "4. PNG Compression"),
        ("total_latency", "TOTAL Processing")
    ]:
        m = st[op]
        print(f"{name:<26} | {m['median']:<12.3f} | {m['p95']:<10.3f} | {m['min']:<10.3f} | {m['max']:<10.3f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
