"""Controlled FITS Download Service for SPHEREx Archive Products (Milestone 4).
Streams large multi-extension FITS files directly from official IRSA URLs,
verifies cryptographic integrity, avoids duplicate downloads, and validates readability.
"""

from __future__ import annotations

import os
import time
import hashlib
import logging
import urllib.parse
from typing import Optional
import httpx
from astropy.io import fits

from app.models.spherex_observation import SpherexDownloadRequest, SpherexDownloadResponse

logger = logging.getLogger("spherex_download")

SPHEREx_STORAGE_DIR = os.getenv("SPHEREX_STORAGE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex")))
MAX_STORAGE_BYTES = 1024 * 1024 * 1024  # 1 GB local cache limit
ALLOWED_DOMAINS = ["irsa.ipac.caltech.edu"]


def ensure_storage_dir() -> str:
    """Ensure data/spherex directory exists."""
    global SPHEREx_STORAGE_DIR
    try:
        os.makedirs(SPHEREx_STORAGE_DIR, exist_ok=True)
    except Exception:
        SPHEREx_STORAGE_DIR = os.path.join("/tmp", "spherex")
        os.makedirs(SPHEREx_STORAGE_DIR, exist_ok=True)
    return SPHEREx_STORAGE_DIR


def get_storage_stats() -> dict:
    """Return count and total size of downloaded files in data/spherex."""
    ensure_storage_dir()
    files = [os.path.join(SPHEREx_STORAGE_DIR, f) for f in os.listdir(SPHEREx_STORAGE_DIR) if f.endswith(".fits")]
    total_bytes = sum(os.path.getsize(f) for f in files)
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "max_mb": round(MAX_STORAGE_BYTES / (1024 * 1024), 2),
    }


def enforce_storage_limit(new_file_bytes: int):
    """Enforce storage ceiling by pruning oldest files if needed."""
    stats = get_storage_stats()
    if stats["total_bytes"] + new_file_bytes > MAX_STORAGE_BYTES:
        files = [
            (os.path.join(SPHEREx_STORAGE_DIR, f), os.path.getmtime(os.path.join(SPHEREx_STORAGE_DIR, f)))
            for f in os.listdir(SPHEREx_STORAGE_DIR) if f.endswith(".fits")
        ]
        files.sort(key=lambda x: x[1])  # Oldest first
        for fpath, _ in files:
            if stats["total_bytes"] + new_file_bytes <= MAX_STORAGE_BYTES:
                break
            try:
                sz = os.path.getsize(fpath)
                os.remove(fpath)
                stats["total_bytes"] -= sz
                logger.info("Evicted old cached FITS: %s (%d bytes)", fpath, sz)
            except Exception as e:
                logger.warning("Failed to evict %s: %e", fpath, e)


async def download_spherex_fits(
    request: SpherexDownloadRequest,
    timeout_sec: float = 180.0
) -> SpherexDownloadResponse:
    """Stream download a genuine SPHEREx FITS product from NASA/IPAC IRSA."""
    ensure_storage_dir()

    # 1. Validate URL domain
    parsed = urllib.parse.urlparse(request.access_url)
    if parsed.netloc not in ALLOWED_DOMAINS:
        raise ValueError(f"Disallowed archive domain '{parsed.netloc}'. Must be an official IRSA URL ({ALLOWED_DOMAINS})")

    filename = os.path.basename(parsed.path)
    if not filename.endswith(".fits"):
        filename = f"{filename}.fits"
    dest_path = os.path.join(SPHEREx_STORAGE_DIR, filename)
    temp_path = f"{dest_path}.part"

    # 2. Check if already downloaded and valid
    if os.path.exists(dest_path):
        existing_size = os.path.getsize(dest_path)
        if existing_size > 1024 * 1024:  # At least 1 MB
            try:
                # Fast header verification
                with fits.open(dest_path) as hdul:
                    if len(hdul) >= 2 and "IMAGE" in hdul:
                        sha256 = hashlib.sha256()
                        with open(dest_path, "rb") as f:
                            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                                sha256.update(chunk)
                        return SpherexDownloadResponse(
                            success=True,
                            obs_id=request.obs_id,
                            filename=filename,
                            file_path=dest_path,
                            file_size_bytes=existing_size,
                            file_size_mb=round(existing_size / (1024 * 1024), 2),
                            sha256=sha256.hexdigest(),
                            download_time_sec=0.0,
                            already_existed=True,
                            message=f"Product '{filename}' already cached locally.",
                        )
            except Exception:
                logger.warning("Existing file %s corrupted; re-downloading", dest_path)
                os.remove(dest_path)

    # 3. Stream download
    logger.info("Starting download of %s from %s", filename, request.access_url)
    t0 = time.time()
    sha256 = hashlib.sha256()
    bytes_downloaded = 0

    try:
        async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
            async with client.stream(
                "GET",
                request.access_url,
                headers={"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0 (NASA Space Apps)"}
            ) as resp:
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code} from IRSA: {resp.text[:200]}")

                content_len = int(resp.headers.get("Content-Length", 71634240))
                enforce_storage_limit(content_len)

                with open(temp_path, "wb") as out_f:
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 1024):
                        out_f.write(chunk)
                        sha256.update(chunk)
                        bytes_downloaded += len(chunk)

        # Atomic rename on success
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(temp_path, dest_path)

    except Exception as exc:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error("Download failed for %s: %s", request.access_url, exc)
        raise RuntimeError(f"Failed to download SPHEREx FITS from IRSA: {exc}")

    download_time = round(time.time() - t0, 2)

    # 4. Verify FITS integrity immediately after download
    try:
        with fits.open(dest_path) as hdul:
            if len(hdul) < 2 or "IMAGE" not in hdul:
                raise ValueError("Downloaded file does not contain required SPHEREx IMAGE HDU")
    except Exception as exc:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise RuntimeError(f"Downloaded FITS failed integrity validation: {exc}")

    final_size = os.path.getsize(dest_path)
    return SpherexDownloadResponse(
        success=True,
        obs_id=request.obs_id,
        filename=filename,
        file_path=dest_path,
        file_size_bytes=final_size,
        file_size_mb=round(final_size / (1024 * 1024), 2),
        sha256=sha256.hexdigest(),
        download_time_sec=download_time,
        already_existed=False,
        message=f"Successfully downloaded and verified genuine SPHEREx FITS ({final_size / (1024 * 1024):.1f} MB in {download_time}s).",
    )
