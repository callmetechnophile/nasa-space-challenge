import os
import json
import numpy as np
from astropy.io.votable import parse_single_table

EVIDENCE_DIR = os.path.abspath("evidence/m5/raw_queries")

def analyze_target_pairs(xml_name, target_name):
    path = os.path.join(EVIDENCE_DIR, xml_name)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return []
    
    t = parse_single_table(path)
    fields = [f.name for f in t.fields]
    records = []
    for r in t.array:
        row = {}
        for f in fields:
            v = r[f]
            if isinstance(v, (bytes, bytearray)):
                v = v.decode("utf-8", errors="replace")
            elif hasattr(v, "item"):
                v = v.item()
            row[f] = v
        records.append(row)
        
    print(f"\n=======================================================")
    print(f"Target: {target_name} ({len(records)} records)")
    print(f"=======================================================")
    
    # Group by detector
    by_det = {}
    for r in records:
        det = str(r.get('energy_bandpassname') or r.get('energy_emband'))
        by_det.setdefault(det, []).append(r)
        
    pairs = []
    for det, recs in sorted(by_det.items()):
        recs.sort(key=lambda x: float(x['t_min']))
        for i in range(len(recs)):
            for j in range(i + 1, len(recs)):
                r1 = recs[i]
                r2 = recs[j]
                t1 = float(r1['t_min'])
                t2 = float(r2['t_min'])
                dt_days = t2 - t1
                if dt_days < 0.2:  # Skip same-visit dithers
                    continue
                ra1, dec1 = float(r1['s_ra']), float(r1['s_dec'])
                ra2, dec2 = float(r2['s_ra']), float(r2['s_dec'])
                dra = np.radians(ra2 - ra1) * np.cos(np.radians(0.5 * (dec1 + dec2)))
                ddec = np.radians(dec2 - dec1)
                sep_deg = np.degrees(np.hypot(dra, ddec))
                if sep_deg < 0.05:  # Within 3 arcmin (tight pointing alignment)
                    pairs.append({
                        'target': target_name,
                        'detector': det,
                        'sep_arcsec': sep_deg * 3600.0,
                        'dt_days': dt_days,
                        't1_mjd': t1,
                        't2_mjd': t2,
                        'obs1': str(r1['obs_id']),
                        'obs2': str(r2['obs_id']),
                        'url1': str(r1['access_url']),
                        'url2': str(r2['access_url']),
                        'ra1': ra1, 'dec1': dec1,
                        'ra2': ra2, 'dec2': dec2,
                    })

    # Sort pairs by separation then dt_days
    pairs.sort(key=lambda p: (p['sep_arcsec'], -p['dt_days']))
    print(f"Found {len(pairs)} candidate multi-epoch pairs with separation < 3 arcmin")
    for p in pairs[:10]:
        print(f"Det: {p['detector']:<12} | Sep: {p['sep_arcsec']:.2f}\" | Delta_t: {p['dt_days']:.3f} d ({p['dt_days']*24:.1f} h) | Obs1: {p['obs1']} | Obs2: {p['obs2']}")
    return pairs

if __name__ == "__main__":
    targets = [
        ("barnards_star_spherex_qr3.xml", "Barnard's Star"),
        ("epsilon_indi_b_spherex_qr3.xml", "Epsilon Indi B"),
        ("south_ecliptic_pole_spherex_qr3.xml", "South Ecliptic Pole"),
        ("equatorial_corridor_spherex_qr3.xml", "Equatorial Corridor"),
    ]
    all_best = {}
    for xml_file, name in targets:
        p = analyze_target_pairs(xml_file, name)
        if p:
            all_best[name] = p[0]
            
    print("\n\n### Top Candidate Pair Per Target Area ###")
    for name, p in all_best.items():
        print(f"\nTarget: {name}")
        print(f"  Detector: {p['detector']}")
        print(f"  Pointing Sep: {p['sep_arcsec']:.2f} arcsec ({p['sep_arcsec']/6.2:.2f} pixels)")
        print(f"  Time Delta: {p['dt_days']:.3f} days ({p['dt_days']*24:.1f} hours)")
        print(f"  Obs 1: {p['obs1']} (MJD {p['t1_mjd']:.4f})")
        print(f"  Obs 2: {p['obs2']} (MJD {p['t2_mjd']:.4f})")
        print(f"  URL 1: {p['url1']}")
        print(f"  URL 2: {p['url2']}")
