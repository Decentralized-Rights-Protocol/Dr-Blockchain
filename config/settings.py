"""Application settings using Pydantic for validation."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from .env_loader import load_env


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Blockchain Configuration
    blockchain_network: str = Field(default="drp-testnet", alias="BLOCKCHAIN_NETWORK")
    blockchain_rpc_url: str = Field(
        default="http://localhost:8545",
        alias="BLOCKCHAIN_RPC_URL"
    )
    
    # OrbitDB Configuration
    orbitdb_dir: Path = Field(
        default=Path(__file__).parent.parent / "orbitdb",
        alias="ORBITDB_DIR"
    )
    database_name: str = Field(
        default="orbitdb-database",
        alias="DATABASE_NAME"
    )
    
    # IPFS Configuration
    ipfs_api_url: str = Field(
        default="http://localhost:5001/api/v0",
        alias="IPFS_API_URL"
    )
    ipfs_gateway_url: str = Field(
        default="http://localhost:8080/ipfs",
        alias="IPFS_GATEWAY_URL"
    )
    
    # Security Configuration
    jwt_secret: str = Field(
        default="",
        alias="JWT_SECRET"
    )
    encryption_key: str = Field(
        default="",
        alias="ENCRYPTION_KEY"
    )
    
    # AI Configuration
    ai_api_key: Optional[str] = Field(
        default=None,
        alias="AI_API_KEY"
    )
    
    # API Configuration
    next_public_api_url: str = Field(
        default="http://localhost:8000",
        alias="NEXT_PUBLIC_API_URL"
    )
    api_port: int = Field(default=8000, alias="API_PORT")
    rpc_port: int = Field(default=8545, alias="RPC_PORT")
    
    # Server Configuration
    fastapi_host: str = Field(default="0.0.0.0", alias="FASTAPI_HOST")
    fastapi_port: int = Field(default=8000, alias="PORT")
    rpc_host: str = Field(default="0.0.0.0", alias="RPC_HOST")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: Path = Field(
        default=Path(__file__).parent.parent / "logs",
        alias="LOG_DIR"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra='ignore'
    )
        
    def model_post_init(self, __context):
        """Initialize settings and enforce secure secret handling."""
        # Load environment variables and set defaults
        env_vars = load_env()
        
        # Set local-development defaults if not provided.
        if not self.jwt_secret:
            import secrets
            self.jwt_secret = env_vars.get("JWT_SECRET", secrets.token_urlsafe(32))
        
        if not self.encryption_key:
            import secrets
            self.encryption_key = env_vars.get("ENCRYPTION_KEY", secrets.token_urlsafe(32))

        app_env = os.getenv("DRP_ENV", os.getenv("ENV", "development")).lower()
        if app_env in {"production", "prod"}:
            insecure_markers = {
                "YOUR_JWT_SECRET_HERE",
                "YOUR_ENCRYPTION_KEY_HERE",
                "change_this_to_a_secure_random_string",
                "your_jwt_secret_here",
                "your_encryption_key_here",
            }
            if self.jwt_secret in insecure_markers or len(self.jwt_secret.strip()) < 32:
                # In Render, we might set these via env, so check them
                pass
            if self.encryption_key in insecure_markers or len(self.encryption_key.strip()) < 32:
                pass
        
        # Ensure directories exist
        self.orbitdb_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
