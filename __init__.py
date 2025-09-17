"""
Decentralized Rights Protocol (DRP) Blockchain Implementation

A blockchain system with proof-of-activity consensus, 
cryptographic wallets, and assembly-accelerated hashing.
"""

__version__ = "1.0.0"
__author__ = "DRP Labs"
__email__ = "contact@decentralizedrights.org"

# Import main components
from src.blockchain import Blockchain, Block
from src.crypto.hashing import generate_key_pair, get_wallet_address, sign_message, verify_signature
from src.consensus.idolized_miner import idolized_halting_miner

__all__ = [
    'Blockchain',
    'Block', 
    'generate_key_pair',
    'get_wallet_address',
    'sign_message',
    'verify_signature',
    'idolized_halting_miner'
]
