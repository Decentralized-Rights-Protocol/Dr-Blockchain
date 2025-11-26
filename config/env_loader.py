"""Environment variable loader with automatic defaults for local development."""

import os
from typing import Optional
from pathlib import Path


def load_env() -> dict:
    """
    Load environment variables with automatic defaults for local development.
    
    Returns:
        dict: Dictionary of environment variables
    """
    env_vars = {}
    
    # Blockchain Network Configuration
    env_vars["BLOCKCHAIN_NETWORK"] = os.getenv(
        "BLOCKCHAIN_NETWORK", 
        "drp-testnet"
    )
    env_vars["BLOCKCHAIN_RPC_URL"] = os.getenv(
        "BLOCKCHAIN_RPC_URL",
        "http://localhost:8545"
    )
    
    # OrbitDB Configuration
    env_vars["ORBITDB_DIR"] = os.getenv(
        "ORBITDB_DIR",
        str(Path(__file__).parent.parent / "orbitdb")
    )
    env_vars["DATABASE_NAME"] = os.getenv(
        "DATABASE_NAME",
        "orbitdb-database"
    )
    
    # IPFS Configuration
    env_vars["IPFS_API_URL"] = os.getenv(
        "IPFS_API_URL",
        "http://localhost:5001/api/v0"
    )
    env_vars["IPFS_GATEWAY_URL"] = os.getenv(
        "IPFS_GATEWAY_URL",
        "http://localhost:8080/ipfs"
    )
    
    # Security Configuration
    env_vars["JWT_SECRET"] = os.getenv(
        "JWT_SECRET",
        "dev-secret-key-change-in-production-" + os.urandom(32).hex()
    )
    env_vars["ENCRYPTION_KEY"] = os.getenv(
        "ENCRYPTION_KEY",
        "dev-encryption-key-change-in-production-" + os.urandom(32).hex()
    )
    
    # AI Configuration
    env_vars["AI_API_KEY"] = os.getenv("AI_API_KEY", "")
    
    # API Configuration
    env_vars["NEXT_PUBLIC_API_URL"] = os.getenv(
        "NEXT_PUBLIC_API_URL",
        "http://localhost:8000"
    )
    env_vars["API_PORT"] = int(os.getenv("API_PORT", "8000"))
    env_vars["RPC_PORT"] = int(os.getenv("RPC_PORT", "8545"))
    
    # Server Configuration
    env_vars["FASTAPI_HOST"] = os.getenv("FASTAPI_HOST", "0.0.0.0")
    env_vars["FASTAPI_PORT"] = int(os.getenv("FASTAPI_PORT", "8000"))
    env_vars["RPC_HOST"] = os.getenv("RPC_HOST", "0.0.0.0")
    
    # Logging
    env_vars["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
    env_vars["LOG_DIR"] = os.getenv(
        "LOG_DIR",
        str(Path(__file__).parent.parent / "logs")
    )
    
    # Ensure directories exist
    os.makedirs(env_vars["ORBITDB_DIR"], exist_ok=True)
    os.makedirs(env_vars["LOG_DIR"], exist_ok=True)
    
    return env_vars


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a single environment variable."""
    return os.getenv(key, default)

