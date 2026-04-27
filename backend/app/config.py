"""Application configuration using Pydantic BaseSettings.

Loads settings from environment variables with sensible defaults.
Addresses: S-1 (wildcard CORS), S-9 (rate limiting config), B-9 (environment-aware config), B-20 (configurable ports).
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = Field(default="development", description="Runtime environment: development, staging, production")
    debug: bool = Field(default=True, description="Enable debug mode (verbose errors, etc.)")

    # FRED API
    fred_api_key: str = Field(default="", description="FRED API key for live data access")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # Rate limiting
    rate_limit_requests: int = Field(default=100, description="Max requests per rate limit window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")

    # Upload limits
    max_upload_size_bytes: int = Field(default=10_000_000, description="Max upload file size in bytes (10 MB)")
    max_dataset_rows: int = Field(default=100_000, description="Max rows per uploaded dataset")
    max_dataset_columns: int = Field(default=50, description="Max columns per uploaded dataset")

    # Cache
    fred_cache_ttl: int = Field(default=900, description="FRED data cache TTL in seconds (15 min)")
    fred_cache_maxsize: int = Field(default=200, description="Max entries in FRED data cache")
    demo_cache_maxsize: int = Field(default=50, description="Max entries in demo data cache")

    # Server
    backend_port: int = Field(default=8000, description="Backend server port")

    # Auth
    api_key: str = Field(default="", description="API key for endpoint authentication (empty = no auth)")

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_demo_mode(self) -> bool:
        return not bool(self.fred_api_key)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
