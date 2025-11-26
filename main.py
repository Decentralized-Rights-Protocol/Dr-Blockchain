"""Main entry point for DRP backend."""

import uvicorn
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_settings
from api.router import app

if __name__ == "__main__":
    settings = get_settings()
    
    print("🚀 Starting DRP Backend...")
    print(f"📍 API URL: http://{settings.fastapi_host}:{settings.fastapi_port}")
    print(f"📍 RPC URL: http://{settings.rpc_host}:{settings.rpc_port}")
    print(f"📍 Network: {settings.blockchain_network}")
    print("")
    
    uvicorn.run(
        app,
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        log_level=settings.log_level.lower()
    )

