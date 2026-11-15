"""Pre-Deployment Stage 1: Memory & Resource Baseline Audit.
Measures:
1. Backend memory at startup.
2. Memory after loading an observation.
3. Memory after unloading an observation.
4. Memory after 20 repeated load/unload cycles.
5. GPU memory baseline.
6. Leaks and memory growth analysis.
"""

import sys
import os
import gc
import psutil
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("backend"))

print("================================================================================")
print("STAGE 1 — MEMORY & RESOURCE BASELINE AUDIT")
print("================================================================================")

process = psutil.Process(os.getpid())
gc.collect()

mem_startup_mb = process.memory_info().rss / (1024 * 1024)
print(f"1. Backend Memory at Startup: {mem_startup_mb:.2f} MB")

from app.astronomy.spherex_mef_reader import read_spherex_mef_product

f1 = "data/spherex/level2_2026W31_2A_0034_3D1_spx_l2b-v27-2026-224.fits"
f2 = "data/spherex/level2_2026W32_2A_0338_1D1_spx_l2b-v27-2026-223.fits"

# 2. Memory after loading an observation
obs1 = read_spherex_mef_product(f1)
mem_loaded_mb = process.memory_info().rss / (1024 * 1024)
print(f"2. Memory After Loading Single Observation (62.45 MB FITS): {mem_loaded_mb:.2f} MB (Delta: +{mem_loaded_mb - mem_startup_mb:.2f} MB)")

# 3. Memory after unloading
del obs1
gc.collect()
mem_unloaded_mb = process.memory_info().rss / (1024 * 1024)
print(f"3. Memory After Unloading & Garbage Collection: {mem_unloaded_mb:.2f} MB (Delta from startup: +{mem_unloaded_mb - mem_startup_mb:.2f} MB)")

# 4. Memory after 20 repeated load/unload cycles
print("\n4. Executing 20 Repeated Load/Unload Cycles...")
print("-" * 65)
print(f"{'Cycle':<8} | {'RSS Memory (MB)':<18} | {'Delta from Baseline (MB)':<25}")
print("-" * 65)

cycle_memories = []
for cycle in range(1, 21):
    target_f = f1 if cycle % 2 == 1 else f2
    obs = read_spherex_mef_product(target_f)
    # Perform realistic scientific operation (e.g. read mean of image)
    _ = np.nanmean(obs.image)
    del obs
    gc.collect()
    
    current_rss = process.memory_info().rss / (1024 * 1024)
    cycle_memories.append(current_rss)
    if cycle in [1, 2, 5, 10, 15, 20]:
        print(f"Cycle {cycle:<2d} | {current_rss:<18.2f} | {current_rss - mem_unloaded_mb:+24.2f}")

mem_after_20 = cycle_memories[-1]
mem_growth_20 = mem_after_20 - mem_unloaded_mb

print("-" * 65)
print(f"Initial Baseline after 1st Unload: {mem_unloaded_mb:.2f} MB")
print(f"Final Memory after 20 Cycles:      {mem_after_20:.2f} MB")
print(f"Net Growth across 20 Cycles:       {mem_growth_20:+.2f} MB")
leak_detected = abs(mem_growth_20) > 15.0 # Tolerance threshold for memory leak

# 5. GPU Memory Baseline
gpu_desc = "Not Allocated (CPU/NumPy backend)"
try:
    import torch
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / (1024 * 1024)
        reserved = torch.cuda.memory_reserved() / (1024 * 1024)
        gpu_desc = f"Allocated: {alloc:.1f} MB, Reserved: {reserved:.1f} MB"
except Exception:
    pass

print(f"\n5. GPU Memory Status: {gpu_desc}")

print("\n================================================================================")
print(f"MEMORY & RESOURCE BASELINE AUDIT: {'PASS (STABLE NO LEAKS)' if not leak_detected else 'WARNING (GROWTH DETECTED)'}")
print("================================================================================")
