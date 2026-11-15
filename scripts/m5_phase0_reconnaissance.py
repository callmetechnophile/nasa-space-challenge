"""Comprehensive IRSA SIA2 Reconnaissance for SPHEREx M5 Phase 0 Feasibility Audit.
Queries the official NASA/IPAC IRSA SIA service for QR2 and QR3 collections across:
- WISE 0855-0714
- Barnard's Star
- Epsilon Indi B
- South Ecliptic Pole (0.0, -89.9)
- Equatorial Corridor (45.0, 0.0)

Extracts all 51 VOTable metadata fields, differentiates observation time from release time,
evaluates unique epochs, detectors, processing versions, spatial overlaps, and downloads.
"""

import os
import sys
import json
import time
import urllib.parse
import urllib.request
import numpy as np
from astropy.io.votable import parse_single_table

EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../evidence/m5/raw_queries"))
os.makedirs(EVIDENCE_DIR, exist_ok=True)

TARGETS = [
    ("WISE 0855-0714", 133.795129, -7.245147, 1.0),
    ("Barnard's Star", 269.452083, 4.693361, 1.0),
    ("Epsilon Indi B", 330.84, -56.79, 1.0),
    ("South Ecliptic Pole", 0.0, -89.9, 1.0),
    ("Equatorial Corridor", 45.0, 0.0, 1.0),
]

COLLECTIONS = ["spherex_qr2", "spherex_qr3"]


def query_irsa_sia(collection: str, ra: float, dec: float, radius_deg: float, xml_filename: str):
    base_url = "https://irsa.ipac.caltech.edu/SIA"
    params = {
        "COLLECTION": collection,
        "POS": f"circle {ra} {dec} {radius_deg}",
        "RESPONSEFORMAT": "votable",
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    xml_path = os.path.join(EVIDENCE_DIR, xml_filename)
    
    print(f"\n>>> Querying {collection} for {xml_filename} ...")
    print(f"    URL: {url}")
    
    start_time = time.time()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SPHEREx-M5-Reconnaissance/1.0 (NASA Space Apps)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            content = resp.read()
            elapsed = time.time() - start_time
            print(f"    Received {len(content)} bytes in {elapsed:.2f}s")
            with open(xml_path, "wb") as f:
                f.write(content)
        return xml_path, elapsed, None
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"    ERROR after {elapsed:.2f}s: {e}")
        return None, elapsed, str(e)


def analyze_votable(xml_path: str):
    if not xml_path or not os.path.exists(xml_path):
        return None
    try:
        t = parse_single_table(xml_path)
    except Exception as e:
        print(f"    Error parsing VOTable {xml_path}: {e}")
        return None

    arr = t.array
    fields = [f.name for f in t.fields]
    records = []
    for r in arr:
        row_dict = {}
        for f in fields:
            val = r[f]
            if isinstance(val, (bytes, bytearray)):
                val = val.decode("utf-8", errors="replace")
            elif hasattr(val, "item"):
                val = val.item()
            row_dict[f] = val
        records.append(row_dict)
    return records, fields


def run_audit():
    summary_results = []
    
    for name, ra, dec, rad in TARGETS:
        for col in COLLECTIONS:
            target_slug = name.lower().replace(" ", "_").replace("'", "")
            filename = f"{target_slug}_{col}.xml"
            xml_path = os.path.join(EVIDENCE_DIR, filename)
            
            # If already fetched recently and valid, use it; otherwise query
            if not os.path.exists(xml_path) or os.path.getsize(xml_path) == 0:
                xml_path, elapsed, err = query_irsa_sia(col, ra, dec, rad, filename)
            else:
                elapsed = 0.0
                err = None
                print(f"Using cached query file: {filename} ({os.path.getsize(xml_path)} bytes)")

            parsed = analyze_votable(xml_path)
            if parsed is None:
                summary_results.append({
                    "target": name,
                    "collection": col,
                    "records_count": 0,
                    "unique_epochs": 0,
                    "unique_detectors": [],
                    "unique_versions": [],
                    "overlapping_pairs": 0,
                    "downloadable_fits": 0,
                    "error": err or "Failed to parse",
                    "file_path": xml_path if xml_path else None,
                })
                continue
                
            records, fields = parsed
            
            # Metadata analysis
            obs_ids = set()
            obs_epochs = set()  # based on t_min observation timestamp
            detectors = set()
            versions = set()
            urls = []
            
            for r in records:
                obs_id = r.get("obs_id")
                if obs_id:
                    obs_ids.add(str(obs_id))
                t_min = r.get("t_min")
                if t_min is not None and not np.isnan(float(t_min)):
                    # Group within 10 minutes into common epoch
                    obs_epochs.add(round(float(t_min) * 24.0 * 6.0) / (24.0 * 6.0))
                det = r.get("energy_bandpassname") or r.get("energy_emband")
                if det:
                    detectors.add(str(det))
                url = r.get("access_url")
                if url and "fits" in str(url):
                    urls.append(url)
                    # Extract version token from URL or obs_id
                    # e.g., l2b-v27 or l2b-v20
                    parts = str(url).split("/")
                    for p in parts:
                        if "v2" in p or "v1" in p:
                            versions.add(p)

            # Spatial overlap calculation
            overlap_pairs = 0
            n_rec = len(records)
            for i in range(n_rec):
                for j in range(i + 1, n_rec):
                    r1 = records[i]
                    r2 = records[j]
                    ra1, dec1 = float(r1["s_ra"]), float(r1["s_dec"])
                    ra2, dec2 = float(r2["s_ra"]), float(r2["s_dec"])
                    dra = np.radians(ra2 - ra1) * np.cos(np.radians(0.5 * (dec1 + dec2)))
                    ddec = np.radians(dec2 - dec1)
                    sep_deg = np.degrees(np.hypot(dra, ddec))
                    if sep_deg < 0.8:  # Significant overlap within 3.5 deg detector FOV
                        overlap_pairs += 1

            summary_results.append({
                "target": name,
                "ra": ra,
                "dec": dec,
                "collection": col,
                "records_count": len(records),
                "unique_obs_ids": len(obs_ids),
                "unique_epochs": len(obs_epochs),
                "unique_detectors": sorted(list(detectors)),
                "unique_versions": sorted(list(versions)),
                "overlapping_pairs": overlap_pairs,
                "downloadable_fits": len(urls),
                "error": None,
                "file_path": os.path.relpath(xml_path, os.path.abspath(os.path.join(EVIDENCE_DIR, "../.."))),
                "sample_records": records[:3] if records else [],
            })

    output_json = os.path.join(EVIDENCE_DIR, "m5_phase0_query_summary.json")
    with open(output_json, "w") as f:
        json.dump(summary_results, f, indent=2)
    print(f"\nSaved summary to: {output_json}")
    
    # Print formatted table
    print("\n" + "=" * 110)
    print(f"{'Target':<22} {'Collection':<14} {'Records':<8} {'Epochs':<8} {'Detectors':<15} {'Versions':<15} {'Overlaps':<10} {'FITS URLs':<10}")
    print("=" * 110)
    for res in summary_results:
        dets = ",".join(res["unique_detectors"]) if res["unique_detectors"] else "None"
        vers = ",".join(res["unique_versions"][:2]) if res["unique_versions"] else "None"
        print(f"{res['target']:<22} {res['collection']:<14} {res['records_count']:<8} {res['unique_epochs']:<8} {dets:<15} {vers:<15} {res['overlapping_pairs']:<10} {res['downloadable_fits']:<10}")
    print("=" * 110)


if __name__ == "__main__":
    run_audit()
