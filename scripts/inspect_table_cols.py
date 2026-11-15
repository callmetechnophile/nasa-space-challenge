import io
import httpx
from astropy.io.votable import parse_single_table

url = "https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex_qr3&POS=circle+45.0+0.0+0.01&RESPONSEFORMAT=votable"
r = httpx.get(url, timeout=30.0)
table = parse_single_table(io.BytesIO(r.content))

print(f"Total fields: {len(table.fields)}")
field_names = [f.name for f in table.fields]
print("Field names:", field_names)

row0 = table.array[0]
print("\n--- RECORD 0 ---")
for f in table.fields:
    val = row0[f.name]
    if isinstance(val, (bytes, bytearray)):
        val = val.decode()
    print(f"  {f.name} ({f.ID}): {val}")
