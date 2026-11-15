import os
import gc
import sys
import time
import psutil
import warnings
import tracemalloc
import subprocess
import numpy as np

warnings.filterwarnings("ignore")

from app.astronomy.spherex_mef_reader import read_spherex_mef_product
from app.astronomy.quality_mask import create_quality_mask, DEFAULT_FATAL_MASK
from app.astronomy.image_registration import create_common_wcs, reproject_to_common_grid
from app.astronomy.difference_engine import compute_difference_and_significance
from app.astronomy.change_detection import extract_change_candidates

REAL_FITS_1 = os.path.abspath("data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits")
REAL_FITS_2 = os.path.abspath("data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits")

def get_gpu_vram():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        )
        return float(out.strip().split("\n")[0])
    except Exception:
        return 0.0

def run_memory_audit(total_cycles=100):
    print("="*80, flush=True)
    print(f"TASK E: BACKEND MEMORY AUDIT CORRECTION ({total_cycles} SEQUENTIAL CYCLES)", flush=True)
    print("="*80, flush=True)
    print("Operating System: Windows 11 Build 29704 (AMD64)", flush=True)
    print("Memory Allocator: Windows NT Heap / Segment Heap via MSVCRT (not glibc)", flush=True)

    proc = psutil.Process()
    gc.collect()
    tracemalloc.start()

    init_rss = proc.memory_info().rss / (1024 * 1024)
    init_vms = proc.memory_info().vms / (1024 * 1024)
    init_gpu = get_gpu_vram()
    init_objs = len(gc.get_objects())
    tm_curr, tm_peak = tracemalloc.get_traced_memory()

    print(f"\n[Baseline / Cycle 0]", flush=True)
    print(f"  Process RSS:            {init_rss:.2f} MB", flush=True)
    print(f"  Committed Memory (VMS): {init_vms:.2f} MB", flush=True)
    print(f"  Tracemalloc Current:    {tm_curr / (1024*1024):.2f} MB (Peak: {tm_peak / (1024*1024):.2f} MB)", flush=True)
    print(f"  Live GC Objects:        {init_objs:,}", flush=True)
    print(f"  Dedicated GPU VRAM:     {init_gpu:.1f} MiB", flush=True)

    milestone_cycles = [1, 10, 20, 50, 100]
    cycle_records = []

    target_wcs = create_common_wcs(ra_center=45.0, dec_center=0.0, npix_x=512, npix_y=512)

    t_start = time.time()
    for cycle in range(1, total_cycles + 1):
        # 1. FITS Ingestion & MEF Parsing
        prod1 = read_spherex_mef_product(REAL_FITS_1)
        prod2 = read_spherex_mef_product(REAL_FITS_2)

        # 2. Quality Masking
        mask_res1 = create_quality_mask(prod1.image, prod1.flags, prod1.variance, fatal_bitmask=DEFAULT_FATAL_MASK)
        mask_res2 = create_quality_mask(prod2.image, prod2.flags, prod2.variance, fatal_bitmask=DEFAULT_FATAL_MASK)
        bad1 = mask_res1["bad_mask"]
        bad2 = mask_res2["bad_mask"]

        # 3. WCS Reprojection
        reproj1_dict = reproject_to_common_grid(prod1.image, prod1.variance, prod1.wcs, target_wcs, target_shape=(512, 512))
        reproj2_dict = reproject_to_common_grid(prod2.image, prod2.variance, prod2.wcs, target_wcs, target_shape=(512, 512))

        reproj1 = reproj1_dict["image"]
        var_grid1 = reproj1_dict["variance"]
        reproj2 = reproj2_dict["image"]
        var_grid2 = reproj2_dict["variance"]

        grid_bad1 = ~reproj1_dict["valid_mask"]
        grid_bad2 = ~reproj2_dict["valid_mask"]

        # 4. Difference & Significance Calculation
        diff_res = compute_difference_and_significance(
            image1=reproj1,
            variance1=var_grid1,
            image2=reproj2,
            variance2=var_grid2,
            bad_mask1=grid_bad1,
            bad_mask2=grid_bad2,
            subtract_residual_background=True,
        )
        diff = diff_res["difference_image"]
        sig = diff_res["significance_map"]

        # 5. Candidate Extraction
        cand_res = extract_change_candidates(
            sig, diff, significance_threshold=5.0
        )
        candidates = cand_res["candidates"]

        # 6. Explicit Cleanup
        del prod1, prod2, mask_res1, mask_res2, bad1, bad2, reproj1_dict, reproj2_dict
        del reproj1, reproj2, var_grid1, var_grid2, grid_bad1, grid_bad2, diff_res, diff, sig, cand_res, candidates
        gc.collect()

        if cycle in milestone_cycles:
            cur_rss = proc.memory_info().rss / (1024 * 1024)
            cur_vms = proc.memory_info().vms / (1024 * 1024)
            tm_c, tm_p = tracemalloc.get_traced_memory()
            cur_objs = len(gc.get_objects())
            cur_gpu = get_gpu_vram()
            cycle_time = (time.time() - t_start) / cycle

            record = {
                "cycle": cycle,
                "rss": cur_rss,
                "vms": cur_vms,
                "tm_curr": tm_c / (1024 * 1024),
                "tm_peak": tm_p / (1024 * 1024),
                "objs": cur_objs,
                "gpu": cur_gpu,
                "avg_sec": cycle_time
            }
            cycle_records.append(record)
            print(f"\n[Milestone Cycle {cycle:>3}]", flush=True)
            print(f"  Process RSS:            {cur_rss:.2f} MB (Delta from Init: {cur_rss - init_rss:+.2f} MB)", flush=True)
            print(f"  Committed Memory (VMS): {cur_vms:.2f} MB", flush=True)
            print(f"  Tracemalloc Current:    {record['tm_curr']:.2f} MB (Peak: {record['tm_peak']:.2f} MB)", flush=True)
            print(f"  Live GC Objects:        {cur_objs:,} (Delta from Init: {cur_objs - init_objs:+d})", flush=True)
            print(f"  Dedicated GPU VRAM:     {cur_gpu:.1f} MiB", flush=True)
            print(f"  Mean Pace:              {cycle_time:.2f} s/cycle", flush=True)

    # Final post-100 cycle garbage collection
    gc.collect()
    final_rss = proc.memory_info().rss / (1024 * 1024)
    final_tm_c, final_tm_p = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_duration = time.time() - t_start
    print("\n" + "="*80, flush=True)
    print("BACKEND MEMORY AUDIT RESULTS SUMMARY", flush=True)
    print("="*80, flush=True)
    print(f"Total Processing Duration:   {total_duration:.1f} s ({total_duration/total_cycles:.2f} s/cycle)", flush=True)
    print(f"Initial Baseline RSS:        {init_rss:.2f} MB", flush=True)
    print(f"Cycle 1 RSS:                 {cycle_records[0]['rss']:.2f} MB", flush=True)
    print(f"Cycle 10 RSS:                {cycle_records[1]['rss']:.2f} MB", flush=True)
    print(f"Cycle 20 RSS:                {cycle_records[2]['rss']:.2f} MB", flush=True)
    print(f"Cycle 50 RSS:                {cycle_records[3]['rss']:.2f} MB", flush=True)
    print(f"Cycle 100 RSS:               {cycle_records[4]['rss']:.2f} MB", flush=True)
    print(f"Final RSS Post-GC:           {final_rss:.2f} MB", flush=True)
    print(f"Net RSS Growth (20 -> 100):  {cycle_records[4]['rss'] - cycle_records[2]['rss']:+.2f} MB", flush=True)
    print(f"Net Python Heap Growth:      {final_tm_c/(1024*1024) - cycle_records[0]['tm_curr']:+.2f} MB", flush=True)
    print(f"Live GC Object Drift (1->100):{cycle_records[4]['objs'] - cycle_records[0]['objs']:+d} objects", flush=True)
    print("="*80, flush=True)

if __name__ == "__main__":
    run_memory_audit(100)
