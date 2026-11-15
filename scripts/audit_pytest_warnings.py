import subprocess
import collections
import re

res = subprocess.run(["pytest", "tests/test_spherex_m5_validation.py", "-W", "error:::0"], capture_output=True, text=True)

# Run standard pytest and parse warnings
proc = subprocess.run(["pytest", "tests/test_spherex_m5_validation.py"], capture_output=True, text=True)

print("=== AUDIT 5: PYTEST WARNINGS BREAKDOWN ===")
lines = proc.stdout.splitlines()

warning_blocks = []
current_block = []
in_warnings = False

for line in lines:
    if "=== warnings summary ===" in line:
        in_warnings = True
        continue
    if in_warnings and ("=== 12 passed" in line or "-- Docs:" in line):
        if current_block:
            warning_blocks.append("\n".join(current_block))
            current_block = []
        break
    if in_warnings:
        if line.strip().startswith("C:\\") or line.strip().startswith("tests/"):
            if current_block:
                warning_blocks.append("\n".join(current_block))
                current_block = []
        current_block.append(line)

print(f"Total warning messages captured: {len(warning_blocks)}")

# Categorize warnings
categories = collections.defaultdict(list)
for b in warning_blocks:
    # Match warning type
    m = re.search(r"(\w+Warning):\s*(.*)", b)
    if m:
        w_type = m.group(1)
        w_msg = m.group(2)
        categories[w_type].append(w_msg)
    else:
        categories["Other"].append(b)

for w_type, msgs in categories.items():
    print(f"\nWarning Type: {w_type} (Count: {len(msgs)})")
    # Count unique messages
    c_msg = collections.Counter(msgs)
    for msg, count in c_msg.most_common(10):
        print(f"  [{count}x] {msg[:100]}...")
