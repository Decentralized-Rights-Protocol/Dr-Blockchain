"""Application settings using Pydantic for validation."""

import os
import secrets
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from .env_loader import load_env


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Blockchain Configuration
    blockchain_network: str = Field(default="drp-testnet", alias="BLOCKCHAIN_NETWORK")
    blockchain_rpc_url: str = Field(default="http://localhost:8545", alias="BLOCKCHAIN_RPC_URL")

    # OrbitDB Configuration
    orbitdb_dir: str = Field(default="/tmp/drp-data/orbitdb", alias="ORBITDB_DIR")
    database_name: str = Field(default="orbitdb-database", alias="DATABASE_NAME")

    # IPFS Configuration
    ipfs_api_url: str = Field(default="http://localhost:5001/api/v0", alias="IPFS_API_URL")
    ipfs_gateway_url: str = Field(default="http://localhost:8080/ipfs", alias="IPFS_GATEWAY_URL")

    # Security Configuration
    secret_key: str = Field(default="", alias="SECRET_KEY")
    jwt_secret_key: str = Field(default="", alias="JWT_SECRET_KEY")
    master_encryption_key: str = Field(default="", alias="MASTER_ENCRYPTION_KEY")
    # Legacy aliases
    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    encryption_key: str = Field(default="", alias="ENCRYPTION_KEY")

    # AI Configuration
    ai_api_key: Optional[str] = Field(default=None, alias="AI_API_KEY")

    # API Configuration
    next_public_api_url: str = Field(default="http://localhost:8000", alias="NEXT_PUBLIC_API_URL")
    api_port: int = Field(default=8000, alias="API_PORT")
    rpc_port: int = Field(default=8545, alias="RPC_PORT")

    # Server Configuration
    fastapi_host: str = Field(default="0.0.0.0", alias="FASTAPI_HOST")
    fastapi_port: int = Field(default=8000, alias="PORT")
    rpc_host: str = Field(default="0.0.0.0", alias="RPC_HOST")

    # Feature flags
    enable_swagger_ui: bool = Field(default=True, alias="ENABLE_SWAGGER_UI")
    debug: bool = Field(default=False, alias="DEBUG")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: str = Field(default="/tmp/drp-data/logs", alias="LOG_DIR")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "populate_by_name": True,
        "extra": "ignore"
    }

    def model_post_init(self, __context):
        """Set secure defaults and ensure directories exist after init."""
        # Fall back to SECRET_KEY for JWT/encryption if not set
        if not self.jwt_secret_key and self.secret_key:
            object.__setattr__(self, "jwt_secret_key", self.secret_key)
        if not self.jwt_secret_key:
            object.__setattr__(self, "jwt_secret_key", secrets.token_urlsafe(32))
        if not self.master_encryption_key:
            object.__setattr__(self, "master_encryption_key", secrets.token_urlsafe(32))

        # Ensure data directories exist
        try:
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
            Path(self.orbitdb_dir).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass  # Non-fatal on read-only filesystems


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
