"""Application Configuration for SkyTrace Backend."""

from __future__ import annotations

import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "production"))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    # CORS
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            ).split(",")
            if origin.strip()
        ]
    )
    
    # Azure Blob Storage Configuration
    azure_storage_account_name: str = Field(default_factory=lambda: os.getenv("AZURE_STORAGE_ACCOUNT_NAME", ""))
    azure_storage_account_url: str = Field(default_factory=lambda: os.getenv("AZURE_STORAGE_ACCOUNT_URL", ""))
    azure_storage_container: str = Field(default_factory=lambda: os.getenv("AZURE_STORAGE_CONTAINER", "fits-products"))
    
    # Local fallback storage
    local_storage_dir: str = Field(
        default_factory=lambda: os.getenv(
            "SPHEREX_STORAGE_DIR",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/spherex")),
        )
    )
    max_storage_bytes: int = Field(
        default_factory=lambda: int(os.getenv("MAX_STORAGE_BYTES", str(1024 * 1024 * 1024)))  # 1 GB
    )
    
    # Database Configuration (PostgreSQL Flexible Server / SQLite local fallback)
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    
    # Archive Base URL
    irsa_base_url: str = Field(
        default_factory=lambda: os.getenv("IRSA_BASE_URL", "https://irsa.ipac.caltech.edu")
    )
    request_timeout: int = Field(
        default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "60"))
    )


settings = Settings()
