import json
from collections import defaultdict

with open('synthetic_scan_raw.json') as f:
    data = json.load(f)

files_b = defaultdict(list)
files_f = defaultdict(list)

for pattern, res in data.items():
    for line in res['backend']:
        parts = line.split(':', 2)
        if len(parts) >= 2:
            files_b[parts[0]].append((pattern, parts[1], parts[2] if len(parts) > 2 else ""))
    for line in res['frontend']:
        parts = line.split(':', 2)
        if len(parts) >= 2:
            files_f[parts[0]].append((pattern, parts[1], parts[2] if len(parts) > 2 else ""))

print("=== BACKEND FILES WITH MATCHES ===")
for fn, matches in sorted(files_b.items()):
    patterns_found = sorted(set(m[0] for m in matches))
    print(f"{fn:45s} | count={len(matches):3d} | patterns={patterns_found}")

print("\n=== FRONTEND FILES WITH MATCHES ===")
for fn, matches in sorted(files_f.items()):
    patterns_found = sorted(set(m[0] for m in matches))
    print(f"{fn:45s} | count={len(matches):3d} | patterns={patterns_found}")
