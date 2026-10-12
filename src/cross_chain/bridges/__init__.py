"""
DRP Cross-Chain Bridge Implementations

This module provides bridge implementations for different blockchain networks
enabling cross-chain interoperability.

Supported Bridges:
- Ethereum Bridge (ERC-20, ERC-721, smart contracts)
- Bitcoin Bridge (UTXO-based transactions)
- Polkadot Bridge (Substrate-based chains)
- BSC Bridge (Binance Smart Chain)
- Polygon Bridge (Layer 2 scaling)

Features:
- Smart contract deployment and interaction
- Cross-chain asset transfers
- Multi-signature security
- Quantum-resistant upgrade support
- Gas optimization
- Event monitoring and handling
"""

from .bitcoin_bridge import BitcoinBridge
from .bridge_manager import BridgeManager
from .bsc_bridge import BSCBridge
from .ethereum_bridge import EthereumBridge
from .polkadot_bridge import PolkadotBridge
from .polygon_bridge import PolygonBridge

__version__ = "1.0.0"
__all__ = [
    "BridgeManager",
    "EthereumBridge",
    "BitcoinBridge",
    "PolkadotBridge",
    "BSCBridge",
    "PolygonBridge",
]
