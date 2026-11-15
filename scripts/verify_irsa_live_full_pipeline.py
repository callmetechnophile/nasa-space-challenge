import os
import io
import time
import socket
import ssl
import hashlib
import asyncio
import urllib.parse
import httpx
from astropy.io import fits
from astropy.io.votable import parse_single_table

from app.models.spherex_observation import SpherexSearchRequest
from app.services.spherex_query import execute_spherex_search

TEST_DOWNLOAD_PATH = "d:/nasa/data/spherex/live_irsa_pipeline_test.fits"

async def download_with_resumption(url: str, dest_path: str, chunk_size: int = 8 * 1024 * 1024, max_retries: int = 5):
    """Download large file from IRSA with HTTP Range support and bounded resumption."""
    t0 = time.time()
    headers = {"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0 (NASA Space Apps)"}

    # 1. Get total content length
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        head_resp = await client.head(url, headers=headers)
        if head_resp.status_code != 200:
            raise RuntimeError(f"HEAD request failed: HTTP {head_resp.status_code}")
        total_size = int(head_resp.headers.get("Content-Length", 0))

    print(f"  Target File Size:  {total_size:,} bytes ({total_size / (1024*1024):.2f} MB)", flush=True)

    # 2. Check if part of the file already downloaded
    downloaded = 0
    if os.path.exists(dest_path):
        downloaded = os.path.getsize(dest_path)
        if downloaded == total_size:
            print(f"  File already fully downloaded ({downloaded:,} bytes).", flush=True)
        else:
            print(f"  Resuming from byte offset {downloaded:,}...", flush=True)

    mode = "ab" if downloaded > 0 and downloaded < total_size else "wb"
    if downloaded > total_size:
        downloaded = 0
        mode = "wb"

    with open(dest_path, mode) as f_out:
        while downloaded < total_size:
            end_byte = min(downloaded + chunk_size - 1, total_size - 1)
            chunk_headers = dict(headers)
            chunk_headers["Range"] = f"bytes={downloaded}-{end_byte}"
            
            chunk_success = False
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
                        resp = await client.get(url, headers=chunk_headers)
                        if resp.status_code in (200, 206):
                            data = resp.content
                            f_out.write(data)
                            f_out.flush()
                            downloaded += len(data)
                            pct = (downloaded / total_size) * 100.0
                            print(f"    Downloaded {downloaded:,} / {total_size:,} bytes ({pct:.1f}%)...", flush=True)
                            chunk_success = True
                            break
                        else:
                            print(f"    HTTP {resp.status_code} on attempt {attempt+1}", flush=True)
                except Exception as e:
                    print(f"    Chunk error on attempt {attempt+1}: {e}", flush=True)
                    await asyncio.sleep(2.0 * (attempt + 1))
            
            if not chunk_success:
                raise RuntimeError(f"Failed to download chunk starting at byte {downloaded} after {max_retries} attempts.")

    total_dur = time.time() - t0
    # Calculate SHA-256
    hasher = hashlib.sha256()
    with open(dest_path, "rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            hasher.update(block)
    final_sha = hasher.hexdigest()

    return {
        "file_size": total_size,
        "duration": total_dur,
        "sha256": final_sha
    }


async def run_irsa_live_audit():
    print("="*80, flush=True)
    print("TASK F: IRSA LIVE SIA2 CONNECTIVITY & FULL DATA RETRIEVAL AUDIT", flush=True)
    print("="*80, flush=True)

    # 1. DNS Resolution
    print("\n--- Diagnostic A: DNS Resolution ---", flush=True)
    t0 = time.time()
    try:
        ip = socket.gethostbyname("irsa.ipac.caltech.edu")
        dns_dur = time.time() - t0
        print(f"  Target Host:       irsa.ipac.caltech.edu", flush=True)
        print(f"  Resolved IP:       {ip}", flush=True)
        print(f"  DNS Duration:      {dns_dur:.3f} s", flush=True)
        print(f"  Status:            SUCCESS (PASS)", flush=True)
    except Exception as e:
        print(f"  Status:            FAILED ({e})", flush=True)
        return

    # 2. TCP Connection
    print("\n--- Diagnostic B: TCP Connection ---", flush=True)
    t0 = time.time()
    try:
        s = socket.create_connection((ip, 443), timeout=10.0)
        tcp_dur = (time.time() - t0) * 1000.0
        s.close()
        print(f"  Target:            {ip}:443", flush=True)
        print(f"  TCP Latency:       {tcp_dur:.1f} ms", flush=True)
        print(f"  Status:            SUCCESS (PASS)", flush=True)
    except Exception as e:
        print(f"  Status:            FAILED ({e})", flush=True)
        return

    # 3. TLS Handshake
    print("\n--- Diagnostic C: TLS Handshake ---", flush=True)
    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((ip, 443), timeout=15.0) as sock:
            with ctx.wrap_socket(sock, server_hostname="irsa.ipac.caltech.edu") as ssock:
                tls_ver = ssock.version()
                cipher = ssock.cipher()
                tls_dur = (time.time() - t0) * 1000.0
                print(f"  TLS Protocol:      {tls_ver}", flush=True)
                print(f"  Cipher Suite:      {cipher[0]}", flush=True)
                print(f"  Handshake Latency: {tls_dur:.1f} ms", flush=True)
                print(f"  Status:            SUCCESS (PASS)", flush=True)
    except Exception as e:
        print(f"  Status:            FAILED ({e})", flush=True)
        return

    # 4. HTTP SIA2 Query & VOTable Parsing
    print("\n--- Diagnostic D & E: HTTP SIA2 Query & VOTable Parsing ---", flush=True)
    base_url = "https://irsa.ipac.caltech.edu/SIA"
    query_params = {
        "COLLECTION": "spherex_qr3",
        "POS": "circle 45.0 0.0 0.01",
        "RESPONSEFORMAT": "votable"
    }
    encoded_url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
    print(f"  Request URL:       {encoded_url}", flush=True)
    print(f"  Parameters:        COLLECTION=spherex_qr3, POS=circle 45.0 0.0 0.01, RESPONSEFORMAT=votable", flush=True)

    t0 = time.time()
    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
        resp = await client.get(
            encoded_url,
            headers={"User-Agent": "SPHEREx-3D-Sky-Explorer/1.0 (NASA Space Apps)"}
        )
    query_dur = time.time() - t0

    print(f"  HTTP Status Code:  {resp.status_code}", flush=True)
    print(f"  Response Duration: {query_dur:.3f} s", flush=True)
    print(f"  Content-Type:      {resp.headers.get('content-type')}", flush=True)
    print(f"  Response Size:     {len(resp.content):,} bytes", flush=True)
    assert resp.status_code == 200, f"Expected HTTP 200, got {resp.status_code}"

    # Parse VOTable
    t0 = time.time()
    table = parse_single_table(io.BytesIO(resp.content))
    parse_dur = time.time() - t0
    records = table.array
    record_count = len(records)
    print(f"  VOTable Parse:     SUCCESS ({parse_dur:.3f} s)", flush=True)
    print(f"  Records Returned:  {record_count}", flush=True)
    assert record_count > 0, "No records returned in VOTable!"

    # 5. Extract Product Access URL
    print("\n--- Diagnostic F: Product Access URL Extraction ---", flush=True)
    first_row = records[0]
    access_url = None
    obs_id = None
    for field in table.fields:
        if field.name == "access_url":
            val = first_row[field.name]
            access_url = val.decode() if isinstance(val, (bytes, bytearray)) else str(val)
        elif field.name == "obs_id":
            val = first_row[field.name]
            obs_id = val.decode() if isinstance(val, (bytes, bytearray)) else str(val)

    print(f"  First Record ID:   {obs_id}", flush=True)
    print(f"  Target Access URL: {access_url}", flush=True)
    assert access_url and access_url.startswith("https://"), f"Invalid access_url: {access_url}"
    print(f"  Status:            SUCCESS (PASS)", flush=True)

    # 6. Live FITS Download via Resilient Range Streaming
    print("\n--- Diagnostic G: Live FITS Stream Download ---", flush=True)
    dl_info = await download_with_resumption(access_url, TEST_DOWNLOAD_PATH, chunk_size=8*1024*1024)
    print(f"  Download Duration: {dl_info['duration']:.2f} s", flush=True)
    print(f"  Downloaded Bytes:  {dl_info['file_size']:,} bytes ({dl_info['file_size'] / (1024*1024):.2f} MB)", flush=True)
    print(f"  Mean Throughput:   {(dl_info['file_size'] / (1024*1024)) / dl_info['duration']:.2f} MB/s", flush=True)
    print(f"  SHA-256 Digest:    {dl_info['sha256']}", flush=True)
    print(f"  Status:            SUCCESS (PASS)", flush=True)

    # 7. FITS Validation & Structure Verification
    print("\n--- Diagnostic H: FITS Validation & Extension Inspection ---", flush=True)
    t0 = time.time()
    with fits.open(TEST_DOWNLOAD_PATH) as hdul:
        val_dur = time.time() - t0
        hdu_count = len(hdul)
        print(f"  FITS Parse Time:   {val_dur:.3f} s", flush=True)
        print(f"  Total HDUs Found:  {hdu_count}", flush=True)
        for idx, hdu in enumerate(hdul):
            shape = getattr(hdu, "shape", None)
            dtype = getattr(hdu, "data", None).dtype if getattr(hdu, "data", None) is not None else None
            print(f"    HDU {idx}: {hdu.name:<12} Type={type(hdu).__name__:<16} Shape={str(shape):<16} Dtype={str(dtype)}", flush=True)
        assert "IMAGE" in hdul, "Missing IMAGE HDU in downloaded FITS!"
        assert hdul[1].shape == (2040, 2040), f"Unexpected IMAGE dimensions: {hdul[1].shape}"
        print("  FITS Structural Integrity: FULLY VALIDATED (PASS)", flush=True)

    # 8. Application Workflow Integration Test
    print("\n--- Diagnostic I: Application Retrieval Service Workflow Integration ---", flush=True)
    app_request = SpherexSearchRequest(
        ra=45.0,
        dec=0.0,
        radius_deg=0.01,
        collection="spherex_qr3"
    )
    search_resp = await execute_spherex_search(app_request)
    print(f"  Service Search Status: {search_resp.archive_status}", flush=True)
    print(f"  Service Match Count:   {search_resp.match_count}", flush=True)
    print(f"  Fallback Triggered:    {search_resp.fallback_triggered}", flush=True)
    assert search_resp.archive_status == "OK", "Service search failed!"
    assert search_resp.match_count > 0, "No records returned via service!"
    first_obs = search_resp.observations[0]
    print(f"  Normalized Observation 0:", flush=True)
    print(f"    Obs ID:          {first_obs.obs_id}", flush=True)
    print(f"    Detector Band:   {first_obs.detector_band}", flush=True)
    print(f"    Dimensions:      {first_obs.dimensions}", flush=True)
    print(f"    Access URL:      {first_obs.access_url}", flush=True)
    print(f"    Access Format:   {first_obs.access_format}", flush=True)
    print(f"    Estimated Size:  {first_obs.file_size_mb:.2f} MB", flush=True)
    print(f"  Application Workflow Integration: FULLY VERIFIED (PASS)", flush=True)

    # Clean up test file
    if os.path.exists(TEST_DOWNLOAD_PATH):
        os.remove(TEST_DOWNLOAD_PATH)
        print("\nCleaned up temporary live test download file.", flush=True)

    print("\n" + "="*80, flush=True)
    print("TASK F AUDIT VERDICT: FULL PASS (LIVE IRSA RETRIEVAL VERIFIED)", flush=True)
    print("="*80, flush=True)

if __name__ == "__main__":
    asyncio.run(run_irsa_live_audit())
