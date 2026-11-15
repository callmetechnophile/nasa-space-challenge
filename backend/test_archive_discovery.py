import urllib.parse
import urllib.request
import io
import json
from astropy.io.votable import parse_single_table

def query_irsa_sia(collection: str, ra: float, dec: float, radius_deg: float = 0.05, timeout: int = 30):
    pos_param = f"circle {ra} {dec} {radius_deg}"
    params = {
        "COLLECTION": collection,
        "POS": pos_param
    }
    url = f"https://irsa.ipac.caltech.edu/SIA?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "SPHEREx-3D-Explorer/1.0"})
    
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from IRSA SIA")
        data = resp.read()
        table = parse_single_table(io.BytesIO(data))
        rows = table.array
        
        results = []
        for row in rows:
            record = {}
            for field in table.fields:
                val = row[field.name]
                # Convert bytes / numpy types
                if isinstance(val, (bytes, bytearray)):
                    val = val.decode("utf-8", errors="replace")
                elif hasattr(val, "item"):
                    val = val.item()
                record[field.name] = val
            results.append(record)
        return {
            "collection": collection,
            "ra": ra,
            "dec": dec,
            "radius_deg": radius_deg,
            "url": url,
            "match_count": len(results),
            "records": results
        }

if __name__ == "__main__":
    print("=================================================================")
    print("  PHASE 1: IRSA SIA2 SPHEREx ARCHIVE DISCOVERY ACCEPTANCE TESTS  ")
    print("=================================================================\n")
    
    # 1. WISE 0855 in QR3
    print("TEST 1: Query WISE 0855 (133.795129, -7.245147) in spherex_qr3...")
    res_wise_qr3 = query_irsa_sia("spherex_qr3", 133.795129, -7.245147, 0.05)
    print(f"  -> QR3 Matches: {res_wise_qr3['match_count']}")
    
    # 2. WISE 0855 with QR2 fallback
    print("\nTEST 2: Query WISE 0855 with QR2 fallback...")
    res_wise_qr2 = query_irsa_sia("spherex_qr2", 133.795129, -7.245147, 0.05)
    print(f"  -> QR2 Matches: {res_wise_qr2['match_count']}")
    if res_wise_qr2['match_count'] > 0:
        sample = res_wise_qr2['records'][0]
        print(f"  -> Sample Obs ID:       {sample['obs_id']}")
        print(f"  -> Sample Detector:     {sample['energy_bandpassname']}")
        print(f"  -> Sample Center:       ({sample['s_ra']:.5f}, {sample['s_dec']:.5f})")
        print(f"  -> Sample Dimensions:   {sample['s_xel1']} x {sample['s_xel2']}")
        print(f"  -> Sample Access URL:   {sample['access_url']}")
        print(f"  -> Sample Est Size:     {sample['access_estsize']} KB (~{sample['access_estsize']/1024:.1f} MB)")
    
    # 3. Second independent position: Barnard's Star (269.452083, +4.693361)
    print("\nTEST 3: Query second position: Barnard's Star (269.452083, +4.693361)...")
    res_barnard_qr2 = query_irsa_sia("spherex_qr2", 269.452083, 4.693361, 0.05)
    print(f"  -> QR2 Matches: {res_barnard_qr2['match_count']}")
    if res_barnard_qr2['match_count'] > 0:
        sample2 = res_barnard_qr2['records'][0]
        print(f"  -> Sample Obs ID:       {sample2['obs_id']}")
        print(f"  -> Sample Detector:     {sample2['energy_bandpassname']}")
        print(f"  -> Sample Access URL:   {sample2['access_url']}")

    # 4. Third independent position: Epsilon Indi B (330.84, -56.79)
    print("\nTEST 4: Query third position: Epsilon Indi B (330.84, -56.79)...")
    res_eps_qr2 = query_irsa_sia("spherex_qr2", 330.84, -56.79, 0.05)
    print(f"  -> QR2 Matches: {res_eps_qr2['match_count']}")
    
    # 5. Position with no available data: Empty sky region with tiny radius
    print("\nTEST 5: Query unobserved coordinate with no data...")
    res_empty = query_irsa_sia("spherex_qr3", 0.0, -89.9, 0.001)
    print(f"  -> Matches: {res_empty['match_count']} (Expected: 0)")
    
    # Save discovery results to disk
    out_path = "data/fits/phase1_archive_discovery_results.json"
    summary = {
        "wise_0855_qr3": {"count": res_wise_qr3["match_count"]},
        "wise_0855_qr2": {"count": res_wise_qr2["match_count"], "sample": res_wise_qr2["records"][0] if res_wise_qr2["records"] else None},
        "barnards_star_qr2": {"count": res_barnard_qr2["match_count"], "sample": res_barnard_qr2["records"][0] if res_barnard_qr2["records"] else None},
        "epsilon_indi_qr2": {"count": res_eps_qr2["match_count"]},
        "empty_region": {"count": res_empty["match_count"]},
    }
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved discovery results to: {out_path}")
