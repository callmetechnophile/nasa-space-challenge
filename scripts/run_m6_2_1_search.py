import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from app.astronomy.m6_target_validation import TargetValidationSuite

async def main():
    suite = TargetValidationSuite()
    res = await suite.evaluate_all_targets()
    print("=== M6.2.1 FIVE-TARGET DUAL-COORDINATE SEARCH RESULTS ===")
    for slug, d in res.items():
        name = d["target"]["name"]
        print(f"\nTARGET: {slug} ({name})")
        print(f"  Target Status: {d['target_status']}")
        print(f"  Discovery State: {d['discovery_state']}")
        print(f"  Verified Usable Epochs: {d['verified_usable_epochs']}")
        print(f"  Catalog Coords: {d['catalog_coordinates']['ra_deg']} deg, {d['catalog_coordinates']['dec_deg']} deg (Epoch {d['catalog_coordinates']['reference_epoch']})")
        print(f"  Propagated Coords: {d['propagated_coordinates']['ra_deg']} deg, {d['propagated_coordinates']['dec_deg']} deg (Epoch 2025.8, Disp={d['propagated_coordinates']['proper_motion_displacement_arcsec']}\")")
        print("  Searches (4 runs: Catalog DR1, Catalog QR3, Propagated DR1, Propagated QR3):")
        for s in d["searches"]:
            print(f"    Mode: {s['mode'].upper()} | Collection: {s['collection']}")
            print(f"      RA: {s['exact_ra_deg']} | Dec: {s['exact_dec_deg']} | Radius: {s['search_radius_deg']} deg")
            print(f"      RefEpoch: {s['coordinate_reference_epoch']} | PropEpoch: {s['propagation_epoch']}")
            print(f"      HTTP Status: {s['http_status']} | Query Status: {s['query_status']}")
            print(f"      Returned Records: {s['number_of_returned_records']} | Usable Footprints: {s['number_of_usable_spatial_footprints']}")
            print(f"      Timestamp UTC: {s['request_timestamp_utc']}")
            print(f"      Attempts Count: {len(s.get('attempts', []))}")
            for att in s.get("attempts", []):
                print(f"        Attempt {att['attempt']}: status={att['http_status']}, class={att['classification']}, duration={att['duration_ms']}ms, retry_delay={att['retry_delay_sec']}")

if __name__ == "__main__":
    asyncio.run(main())
