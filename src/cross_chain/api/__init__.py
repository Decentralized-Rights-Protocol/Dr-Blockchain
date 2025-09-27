"""
DRP Cross-Chain API Endpoints

This module provides FastAPI endpoints for cross-chain interoperability,
enabling developers to integrate new blockchain networks and manage
cross-chain operations.

Endpoints:
- /v1/cross-chain/ - Cross-chain transaction management
- /v1/bridges/ - Bridge management and status
- /v1/relays/ - Relay and oracle services
- /v1/crypto/ - Cryptographic operations
- /v1/quantum/ - Quantum-resistant features
- /v1/chains/ - Chain integration management
"""

from .cross_chain_api import CrossChainAPI
from .bridge_endpoints import BridgeEndpoints
from .relay_endpoints import RelayEndpoints
from .crypto_endpoints import CryptoEndpoints
from .quantum_endpoints import QuantumEndpoints

__version__ = "1.0.0"
__all__ = [
    "CrossChainAPI",
    "BridgeEndpoints",
    "RelayEndpoints", 
    "CryptoEndpoints",
    "QuantumEndpoints"
]


