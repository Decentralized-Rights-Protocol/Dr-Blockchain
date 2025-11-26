"""Application settings using Pydantic for validation."""

from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field
from pathlib import Path
from .env_loader import load_env


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Blockchain Configuration
    blockchain_network: str = Field(default="drp-testnet", env="BLOCKCHAIN_NETWORK")
    blockchain_rpc_url: str = Field(
        default="http://localhost:8545",
        env="BLOCKCHAIN_RPC_URL"
    )
    
    # OrbitDB Configuration
    orbitdb_dir: Path = Field(
        default=Path(__file__).parent.parent / "orbitdb",
        env="ORBITDB_DIR"
    )
    database_name: str = Field(
        default="orbitdb-database",
        env="DATABASE_NAME"
    )
    
    # IPFS Configuration
    ipfs_api_url: str = Field(
        default="http://localhost:5001/api/v0",
        env="IPFS_API_URL"
    )
    ipfs_gateway_url: str = Field(
        default="http://localhost:8080/ipfs",
        env="IPFS_GATEWAY_URL"
    )
    
    # Security Configuration
    jwt_secret: str = Field(
        default="",
        env="JWT_SECRET"
    )
    encryption_key: str = Field(
        default="",
        env="ENCRYPTION_KEY"
    )
    
    # AI Configuration
    ai_api_key: Optional[str] = Field(
        default=None,
        env="AI_API_KEY"
    )
    
    # API Configuration
    next_public_api_url: str = Field(
        default="http://localhost:8000",
        env="NEXT_PUBLIC_API_URL"
    )
    api_port: int = Field(default=8000, env="API_PORT")
    rpc_port: int = Field(default=8545, env="RPC_PORT")
    
    # Server Configuration
    fastapi_host: str = Field(default="0.0.0.0", env="FASTAPI_HOST")
    fastapi_port: int = Field(default=8000, env="FASTAPI_PORT")
    rpc_host: str = Field(default="0.0.0.0", env="RPC_HOST")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_dir: Path = Field(
        default=Path(__file__).parent.parent / "logs",
        env="LOG_DIR"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        """Initialize settings with automatic defaults."""
        super().__init__(**kwargs)
        
        # Load environment variables and set defaults
        env_vars = load_env()
        
        # Set defaults if not provided
        if not self.jwt_secret:
            import secrets
            self.jwt_secret = env_vars.get("JWT_SECRET", secrets.token_urlsafe(32))
        
        if not self.encryption_key:
            import secrets
            self.encryption_key = env_vars.get("ENCRYPTION_KEY", secrets.token_urlsafe(32))
        
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

