import httpx
from astropy.io.votable import parse_single_table

url = "https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex&POS=CIRCLE+0.0+0.0+0.5&FORMAT=image/fits"
print(f"Querying IRSA: {url}")
r = httpx.get(url, timeout=30.0)
print(f"HTTP Status: {r.status_code}")
dump_path = "data/spherex/irsa_query_dump.xml"
with open(dump_path, "wb") as f:
    f.write(r.content)

vt = parse_single_table(dump_path)
df = vt.to_table()
print(f"Total records in table: {len(df)}")
print("Available columns:", df.colnames)

print("\n--- Inspecting first 10 records ---")
for i in range(min(10, len(df))):
    row = df[i]
    s_ra = row["s_ra"] if "s_ra" in df.colnames else None
    s_dec = row["s_dec"] if "s_dec" in df.colnames else None
    s_region = str(row["s_region"])[:80] if "s_region" in df.colnames else None
    acc_url = row["access_url"] if "access_url" in df.colnames else None
    print(f"Row {i:2d}: s_ra={s_ra}, s_dec={s_dec}, s_region={s_region}")
    print(f"        access_url={acc_url}")

# Find where the URL used earlier came from:
target_fn = "level2_2026W30_2A_0607_1D1_spx_l2b-v27-2026-224.fits"
match_idx = None
for i, row in enumerate(df):
    if target_fn in str(row["access_url"]):
        match_idx = i
        print(f"\nFound match for earlier test product at Row {i}:")
        for col in df.colnames:
            print(f"  {col}: {row[col]}")
        break

if match_idx is None:
    print(f"\nTarget {target_fn} NOT found in this query! Let's check why.")
