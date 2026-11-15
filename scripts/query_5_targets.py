import asyncio
import httpx
import os
import json
import io
from astropy.io.votable import parse_single_table

targets = [
    ("Barnard's Star", 269.45208, 4.69333),
    ("Epsilon Indi B", 331.04379, -56.78272),
    ("WISE 0855", 133.79513, -7.24514),
    ("RW Aurigae", 76.95642, 30.40142),
    ("R Draconis", 248.16762, 66.75506),
]

async def query_target(client, name, ra, dec, coll):
    url = f"https://irsa.ipac.caltech.edu/SIA?COLLECTION={coll}&POS=circle+{ra}+{dec}+0.1"
    try:
        r = await client.get(url, timeout=30.0)
        if r.status_code != 200:
            return {"status": "ERROR", "code": r.status_code, "msg": r.text[:200]}
        
        # Check if response is HTML error
        if b"<!DOCTYPE" in r.content or b"<html" in r.content.lower():
            return {"status": "HTML_ERROR", "msg": r.text[:200]}
            
        table = parse_single_table(io.BytesIO(r.content))
        rows = []
        for row in table.array:
            d = {}
            for f in table.fields:
                val = row[f.name]
                if isinstance(val, (bytes, bytearray)):
                    val = val.decode("utf-8", "replace")
                elif hasattr(val, "item"):
                    val = val.item()
                d[f.name] = val
            rows.append(d)
        return {"status": "OK", "count": len(rows), "rows": rows}
    except Exception as exc:
        return {"status": "EXCEPTION", "error": str(exc)}

async def main():
    async with httpx.AsyncClient(headers={"User-Agent": "SPHEREx-3D-Explorer/1.0"}) as client:
        summary = {}
        for name, ra, dec in targets:
            print(f"\nTarget: {name} (RA={ra}, Dec={dec})")
            summary[name] = {}
            for coll in ["spherex_dr1", "spherex_qr3"]:
                res = await query_target(client, name, ra, dec, coll)
                st = res.get("status")
                cnt = res.get("count", 0)
                summary[name][coll] = {"status": st, "count": cnt}
                if st == "OK":
                    print(f"  {coll}: {cnt} observations found")
                    if cnt > 0:
                        obs0 = res["rows"][0]
                        print(f"    Obs 0: ID={obs0.get('obs_id')}, band={obs0.get('energy_bandpassname')}, t_min={obs0.get('t_min')}")
                else:
                    print(f"  {coll}: {st} -> {res.get('msg') or res.get('error')}")
                    
        os.makedirs("data/spherex/cache/queries", exist_ok=True)
        with open("data/spherex/cache/queries/five_targets_live_query.json", "w") as f:
            json.dump(summary, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
