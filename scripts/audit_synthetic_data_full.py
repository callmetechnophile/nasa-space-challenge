import os
import re
import subprocess
import json

PATTERNS = [
    r'synthetic',
    r'procedural',
    r'mock',
    r'placeholder',
    r'fake',
    r'random',
    r'fallback',
    r'generate_stars',
    r'demo',
    r'fixture',
    r'hardcode',
    r'dummy',
    r'simulate',
]

def search_repo():
    results = {}
    for p in PATTERNS:
        try:
            out_b = subprocess.check_output(['git', 'grep', '-i', '-n', p, '--', 'backend/app/'], text=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            out_b = ""
        try:
            out_f = subprocess.check_output(['git', 'grep', '-i', '-n', p, '--', 'frontend/app/', 'frontend/components/', 'frontend/lib/', 'frontend/hooks/'], text=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            out_f = ""
            
        results[p] = {
            "backend": out_b.strip().splitlines() if out_b else [],
            "frontend": out_f.strip().splitlines() if out_f else []
        }
    return results

if __name__ == '__main__':
    data = search_repo()
    summary = {}
    for p, res in data.items():
        summary[p] = {
            "backend_count": len(res["backend"]),
            "frontend_count": len(res["frontend"]),
            "backend_samples": res["backend"][:5],
            "frontend_samples": res["frontend"][:5]
        }
    with open('synthetic_scan_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    with open('synthetic_scan_raw.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("Completed scan. Found occurrences across patterns.")
    for p, s in summary.items():
        print(f"{p:15s} | Backend: {s['backend_count']:4d} | Frontend: {s['frontend_count']:4d}")
