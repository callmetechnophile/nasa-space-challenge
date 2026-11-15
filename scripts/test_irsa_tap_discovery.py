from astroquery.ipac.irsa import Irsa
import sys

print('=== 1. Checking SIA Collections ===')
try:
    cols = Irsa.list_collections(servicetype="SIA", filter="spherex")
    print('SPHEREx SIA Collections:', cols)
except Exception as e:
    print('list_collections error:', type(e), e)

print('\n=== 2. Checking TAP Tables ===')
try:
    query = "SELECT table_name, description FROM tap_schema.tables WHERE table_name LIKE 'spherex%'"
    res = Irsa.query_tap(query)
    tbl = res.to_table()
    for row in tbl:
        print(f"Table: {row['table_name']} | {row['description']}")
except Exception as e:
    print('TAP query error:', type(e), e)
