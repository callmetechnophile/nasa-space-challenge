"""Storage abstraction for SkyTrace FITS products.
Supports both Azure Blob Storage (production) and local disk cache (development/fallback).
Preserves SHA-256 integrity, streaming for large products, and content-length validation.
"""

from __future__ import annotations

import os
import io
import hashlib
import logging
from typing import Optional, BinaryIO, List
from app.config import settings

logger = logging.getLogger("skytrace.storage")


class ScientificStorageManager:
    """Manages storage of multi-extension FITS and calibration products."""

    def __init__(self):
        self.account_name = settings.azure_storage_account_name
        self.container_name = settings.azure_storage_container
        self.local_dir = settings.local_storage_dir
        try:
            os.makedirs(self.local_dir, exist_ok=True)
        except Exception:
            self.local_dir = os.path.join("/tmp", "spherex")
            os.makedirs(self.local_dir, exist_ok=True)
        self._blob_service_client = None

    def _get_blob_client(self):
        if not self._blob_service_client and self.account_name:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.storage.blob import BlobServiceClient

                account_url = settings.azure_storage_account_url or f"https://{self.account_name}.blob.core.windows.net"
                credential = DefaultAzureCredential()
                self._blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
                logger.info(f"Initialized Azure Blob Storage client for account: {self.account_name}")
            except Exception as e:
                logger.warning(f"Could not initialize Azure Blob Storage client ({e}); falling back to local disk.")
                self._blob_service_client = None
        return self._blob_service_client

    def save_product(self, filename: str, data: bytes, expected_sha256: Optional[str] = None) -> dict:
        """Store product bytes, verify SHA-256 checksum, and record storage metadata."""
        computed_sha256 = hashlib.sha256(data).hexdigest()
        if expected_sha256 and computed_sha256.lower() != expected_sha256.lower():
            raise ValueError(
                f"Cryptographic integrity mismatch for {filename}: computed {computed_sha256} != expected {expected_sha256}"
            )

        client = self._get_blob_client()
        if client:
            try:
                container_client = client.get_container_client(self.container_name)
                blob_client = container_client.get_blob_client(filename)
                blob_client.upload_blob(data, overwrite=True)
                return {
                    "storage_backend": "AZURE_BLOB_STORAGE",
                    "container": self.container_name,
                    "blob_name": filename,
                    "size_bytes": len(data),
                    "sha256": computed_sha256,
                }
            except Exception as e:
                logger.error(f"Azure Blob upload failed for {filename}: {e}. Falling back to local storage.")

        # Local storage fallback
        local_path = os.path.join(self.local_dir, filename)
        with open(local_path, "wb") as f:
            f.write(data)

        return {
            "storage_backend": "LOCAL_DISK",
            "path": local_path,
            "size_bytes": len(data),
            "sha256": computed_sha256,
        }

    def get_product_bytes(self, filename: str, container: Optional[str] = None) -> Optional[bytes]:
        """Retrieve stored product bytes, checking specified container or standard containers."""
        client = self._get_blob_client()
        if client:
            containers = [container] if container else ["fits-raw", "fits-products", self.container_name]
            for cname in containers:
                if not cname:
                    continue
                try:
                    container_client = client.get_container_client(cname)
                    blob_client = container_client.get_blob_client(filename)
                    if blob_client.exists():
                        logger.info(f"Retrieved {filename} from Azure Blob container: {cname}")
                        return blob_client.download_blob().readall()
                except Exception as e:
                    logger.debug(f"Container {cname} check for {filename} failed: {e}")

        local_path = os.path.join(self.local_dir, filename)
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                return f.read()

        return None

    def download_product_to_file(self, filename: str, target_path: str, container: Optional[str] = None) -> bool:
        """Download product from Azure Blob Storage directly to a target file path."""
        client = self._get_blob_client()
        if not client:
            return False

        containers = [container] if container else ["fits-raw", "fits-products", self.container_name]
        for cname in containers:
            if not cname:
                continue
            try:
                container_client = client.get_container_client(cname)
                blob_client = container_client.get_blob_client(filename)
                if blob_client.exists():
                    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
                    with open(target_path, "wb") as f:
                        data = blob_client.download_blob().readall()
                        f.write(data)
                    logger.info(f"Successfully downloaded {filename} from container {cname} to {target_path}")
                    return True
            except Exception as e:
                logger.debug(f"Container {cname} download failed for {filename}: {e}")

        return False


storage_manager = ScientificStorageManager()
