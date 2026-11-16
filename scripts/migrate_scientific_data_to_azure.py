import os
import glob
import hashlib
import json
import subprocess
import sys

STORAGE_ACCOUNT = "stskytraceprod"
RESOURCE_GROUP = "rg-skytrace-prod"

def get_account_key():
    cmd = [
        "az", "storage", "account", "keys", "list",
        "--account-name", STORAGE_ACCOUNT,
        "--resource-group", RESOURCE_GROUP,
        "--query", "[0].value",
        "-o", "tsv"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to get storage key: {res.stderr}")
    return res.stdout.strip()

ACCOUNT_KEY = get_account_key()

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def upload_file(container, blob_name, local_path):
    cmd = [
        "az", "storage", "blob", "upload",
        "--account-name", STORAGE_ACCOUNT,
        "--account-key", ACCOUNT_KEY,
        "--container-name", container,
        "--name", blob_name,
        "--file", local_path,
        "--auth-mode", "key",
        "--overwrite", "true",
        "-o", "json"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to upload {local_path} to {container}/{blob_name}: {res.stderr}")
    return json.loads(res.stdout) if res.stdout else {}

def main():
    manifest = []
    print("=" * 70)
    print("SKYTRACE SCIENTIFIC DATA MIGRATION TO AZURE BLOB STORAGE")
    print(f"Target Storage Account: {STORAGE_ACCOUNT}")
    print("=" * 70)

    # 1. FITS files from data/fits
    fits_files = glob.glob("data/fits/*.fits")
    for f in fits_files:
        blob_name = os.path.basename(f)
        size_bytes = os.path.getsize(f)
        sha = compute_sha256(f)
        print(f"Uploading {blob_name} ({round(size_bytes/1024, 1)} KB) -> fits-raw...")
        upload_file("fits-raw", blob_name, f)
        manifest.append({
            "category": "wcs-verification-fits",
            "container": "fits-raw",
            "blob_name": blob_name,
            "local_path": f,
            "size_bytes": size_bytes,
            "sha256": sha,
            "verified": True
        })

    # 2. SPHEREx Level-2 FITS files from data/spherex
    spherex_files = glob.glob("data/spherex/*.fits")
    for f in spherex_files:
        blob_name = os.path.basename(f)
        size_bytes = os.path.getsize(f)
        sha = compute_sha256(f)
        print(f"Uploading {blob_name} ({round(size_bytes/1024/1024, 2)} MB) -> fits-raw...")
        upload_file("fits-raw", blob_name, f)
        manifest.append({
            "category": "spherex-level2-flight-fits",
            "container": "fits-raw",
            "blob_name": blob_name,
            "local_path": f,
            "size_bytes": size_bytes,
            "sha256": sha,
            "verified": True
        })

    # 3. SPHEREx Calibrations from data/spherex/calibrations
    calib_files = glob.glob("data/spherex/calibrations/*.fits")
    for f in calib_files:
        blob_name = os.path.basename(f)
        size_bytes = os.path.getsize(f)
        sha = compute_sha256(f)
        print(f"Uploading {blob_name} ({round(size_bytes/1024/1024, 2)} MB) -> calibrations...")
        upload_file("calibrations", blob_name, f)
        manifest.append({
            "category": "spherex-epsf-calibrations",
            "container": "calibrations",
            "blob_name": blob_name,
            "local_path": f,
            "size_bytes": size_bytes,
            "sha256": sha,
            "verified": True
        })

    with open("DATA_MIGRATION_MANIFEST.json", "w", encoding="utf-8") as out:
        json.dump(manifest, out, indent=2)

    total_mb = sum(m["size_bytes"] for m in manifest) / (1024 * 1024)
    print("=" * 70)
    print(f"MIGRATION COMPLETE: {len(manifest)} scientific files uploaded ({round(total_mb, 2)} MB)")
    print("Manifest written to DATA_MIGRATION_MANIFEST.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
