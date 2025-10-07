#!/usr/bin/env python3
"""
DRP Health Check Script
=======================
Simple health check endpoint for Docker containers.
This script provides basic health monitoring for DRP services.
"""

import os
import sys
import time
import json
import requests
from typing import Dict, Any


def check_database_connection() -> bool:
    """Check if database/ledger is accessible."""
    try:
        # Import blockchain module to check if it's working
        from src.blockchain import Blockchain
        blockchain = Blockchain()
        return True
    except Exception as e:
        print(f"Database check failed: {e}")
        return False


def check_crypto_functions() -> bool:
    """Check if cryptographic functions are working."""
    try:
        from src.crypto.hashing import generate_key_pair
        sk, vk = generate_key_pair()
        return sk is not None and vk is not None
    except Exception as e:
        print(f"Crypto check failed: {e}")
        return False


def check_consensus_system() -> bool:
    """Check if consensus system is operational."""
    try:
        from src.consensus.mining import halting_puzzle_miner
        # Just check if the function is importable
        return callable(halting_puzzle_miner)
    except Exception as e:
        print(f"Consensus check failed: {e}")
        return False


def check_network_connectivity() -> bool:
    """Check basic network connectivity."""
    try:
        # Try to reach a well-known endpoint
        response = requests.get("https://httpbin.org/status/200", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Network check failed: {e}")
        return False


def get_system_info() -> Dict[str, Any]:
    """Get system information for health report."""
    return {
        "timestamp": time.time(),
        "environment": os.getenv("DRP_ENV", "development"),
        "node_type": os.getenv("DRP_NODE_TYPE", "unknown"),
        "log_level": os.getenv("DRP_LOG_LEVEL", "INFO"),
        "python_version": sys.version,
        "working_directory": os.getcwd(),
    }


def run_health_check() -> Dict[str, Any]:
    """Run comprehensive health check."""
    checks = {
        "database": check_database_connection(),
        "crypto": check_crypto_functions(),
        "consensus": check_consensus_system(),
        "network": check_network_connectivity(),
    }
    
    overall_health = all(checks.values())
    
    health_report = {
        "status": "healthy" if overall_health else "unhealthy",
        "checks": checks,
        "system": get_system_info(),
        "timestamp": time.time(),
    }
    
    return health_report


def main():
    """Main health check function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # Return JSON output for programmatic use
        report = run_health_check()
        print(json.dumps(report, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if report["status"] == "healthy" else 1)
    else:
        # Human-readable output
        report = run_health_check()
        
        print("=== DRP Health Check ===")
        print(f"Status: {report['status'].upper()}")
        print(f"Environment: {report['system']['environment']}")
        print(f"Node Type: {report['system']['node_type']}")
        print()
        
        print("Component Checks:")
        for component, status in report["checks"].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component.capitalize()}")
        
        print()
        print(f"Timestamp: {time.ctime(report['timestamp'])}")
        
        # Exit with appropriate code
        sys.exit(0 if report["status"] == "healthy" else 1)


if __name__ == "__main__":
    main()

