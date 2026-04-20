"""Main entry point for DRP backend."""

import os
import sys
import uvicorn
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_settings
from api.router import app  # noqa: F401 — exported for uvicorn

if __name__ == "__main__":
    settings = get_settings()

    # Render (and most PaaS) injects $PORT — always respect it
    port = int(os.environ.get("PORT", getattr(settings, "fastapi_port", 8000)))
    host = os.environ.get("API_HOST", getattr(settings, "fastapi_host", "0.0.0.0"))

    print("🚀 Starting DRP Backend...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📍 Network: {getattr(settings, 'blockchain_network', 'drp-testnet')}")
    print(f"📍 Docs: http://{host}:{port}/docs")
    print()

    uvicorn.run(
        "api.router:app",
        host=host,
        port=port,
        log_level=getattr(settings, "log_level", "info").lower(),
        reload=False,
    )
